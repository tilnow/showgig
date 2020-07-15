
# reusing the bones of knewit to build a system that generates gig pages
#





from flask import Flask, redirect, render_template, render_template_string,request, url_for
from flask_sqlalchemy import SQLAlchemy

import datetime
from datetime import timedelta
import random

import os
from PIL import Image
import re

app = Flask(__name__)
app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="showgig",
    password="leaveagig",
    hostname="showgig.mysql.pythonanywhere-services.com",
    databasename="showgig$default",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
preamble='/home/showgig/mysite' # should probbaly be in app.config[]

class Gigs(db.Model):

    __tablename__ = "gigs"

    id = db.Column(db.Integer, primary_key=True) # at this time, map and spider are created on java, so we only store the images, not underlying parameters
    body = db.Column(db.String(4096)) #for now, keywords are inline, so no need to save seperatly
    title = db.Column(db.String(100)) #for now, images have a fixed name based on gignumber + map; +spider. so no need to save either
    created_at=db.Column(db.TIMESTAMP)
    other = db.Column(db.String(4096)) #random other data


@app.route('/', methods=["GET"])
def index():
    return render_template("main.html")

@app.route('/makeagig', methods=["POST"])
def makeagig():
    c = Gigs(body=request.form["body"],title=request.form["title"],other="")
    print("made c:",c)
    files = request.files.getlist("file")
    db.session.add(c)
    db.session.commit()
    gignum=c.id
    print(gignum, files)
    for file in files:
        file.save(preamble, str(gignum)+file.filename)
        print("filename being saved:",file.filename)
    print("will now redirect")
    return redirect('/gig/'+str(gignum))

@app.route('/gig/<gignumber>', methods=["GET"])
def gig(gignumber):
    if request.method == "GET":
        gig=Gigs.query.filter_by(id = int(gignumber)).first()
        if(gig):
            spiderloc=url_for('static',filename=str(gig.id)+"spider"+".png")
            maploc=url_for('static',filename=str(gig.id)+"map"+".png")
            comboloc=url_for('static',filename=str(gig.id)+"combo"+".png")
            print(spiderloc,maploc,comboloc);
            if not os.path.exists(preamble+comboloc):
                files=[preamble+spiderloc,preamble+maploc]
                images = list(map(Image.open, files))
                combo_1 = append_images(images, direction='horizontal')
                combo_1.save(preamble+comboloc)
            return render_template("gig.html", gig=gig.id, comboloc=comboloc,spiderloc=spiderloc,maploc=maploc,title=gig.title, text=gig.body, words=" ".join(getkeywords(gig.body))) 
        return render_template_string("no_such_gig #"+str(gig))




def append_images(images, direction='horizontal',
                  bg_color=(255,255,255), aligment='center'):
    """
    Appends images in horizontal/vertical direction.

    Args:
        images: List of PIL images
        direction: direction of concatenation, 'horizontal' or 'vertical'
        bg_color: Background color (default: white)
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center'

    Returns:
        Concatenated image as a new PIL image object.
    """
    widths, heights = zip(*(i.size for i in images))

    if direction=='horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)
    print(widths, heights,new_width,new_height)
    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)


    offset = 0
    for im in images:
        if direction=='horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1])/2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            print(offset,y)
            new_im.paste(im, (offset, y))
            offset += im.size[0]
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0])/2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]
    new_im=new_im.resize((200,100),Image.LANCZOS)

    return new_im
def getkeywords(txt): #return keywords, without hashsign
    return [word[1:] for word in filter(None, re.split("[, !?:;]+", txt)) if word.startswith("#")]

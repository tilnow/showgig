
# reusing the bones of knewit to build a system that generates gig pages and roam unfurls
#





from flask import Flask, redirect, render_template, render_template_string,request, url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin

import datetime
from datetime import timedelta
import random
from dotenv import load_dotenv

import os
from PIL import Image
import re
load_dotenv()
app = Flask(__name__)
CORS(app)#, resources={r"/*": {"origins": "*"}})

app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="showgig",
    password=os.environ.get("DBPASS"),
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
    c = Gigs(body=request.form["body"],title=request.form["title"],other=request.form["other"])
    print("made c:",c)
    files = request.files.getlist("file")
    print(request.files)
    try:
        print(request.files['spider_file'])
    except:
        print("not file[0]")
    try:
        print(request.files['map_file'])
    except:
        print("not file['file1']")
    files=[request.files['map_file'],request.files['spider_file']]
    db.session.add(c)
    db.session.commit()
    gignum=c.id
    print(gignum, files)
    for file in files:
        fname=preamble+url_for('static',filename=str(gignum)+file.filename)
        file.save(fname)
        f=Image.open(fname)
        if file.filename=='spider.png':
            w,h=f.size
            f=f.crop(box=(w/7,0,(w*6)/7,h))
            f=remove_transparency(f)
        f=f.resize((300,300),Image.LANCZOS)
        f.save(fname)
        print("filename being saved:",file.filename)
    print("will now redirect")
    return redirect('/gig/'+str(gignum))

def remove_transparency(im, bg_colour=(255, 255, 255)):

    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):

        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]

        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = Image.new("RGBA", im.size, bg_colour + (255,))
        bg.paste(im, mask=alpha)
        return bg

    else:
        return im

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
            return render_template("gig.html", gig=gig.id, comboloc=comboloc,spiderloc=spiderloc,maploc=maploc,title=gig.title, text=gig.body.replace("#","").replace("\n","</p><p>"), words=" ".join(getkeywords(gig.body)),other=gig.other.replace("\n","</p><p>") )
        return render_template_string("no_such_gig #"+str(gig))

@app.route('/gigtest/<gignumber>', methods=["GET"])
def gigtest(gignumber):
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
            return render_template("gigtest.html", gig=gig.id, comboloc=comboloc,spiderloc=spiderloc,maploc=maploc,title=gig.title, text=gig.body.replace("#","").replace("\n","</p><p>"), words=" ".join(getkeywords(gig.body)),other=gig.other.replace("\n","</p><p>") )
        return render_template_string("no_such_gig #"+str(gig))

@app.route('/roamme', methods=["post"])
@cross_origin()
def makeroampreview():
    b=request.form["topleft"].replace("ArtOfGig","Yak Collective | Roam")
    c = Gigs(body=b,title=request.form["h1"],other=request.form["roam_url"])
    db.session.add(c)
    db.session.commit()
    return jsonify(c.id)

@app.route('/roampreview/<id>', methods=["get"])
def showroampreview(id):
    roam=Gigs.query.filter_by(id = int(id)).first()

    return render_template("roampreview.html", title=roam.title, description=roam.body,roam_url=roam.other)

@app.route('/roampreview1/<id>', methods=["get"])
def showroampreview1(id):
    roam=Gigs.query.filter_by(id = int(id)).first()

    return render_template("roampreview1.html", title=roam.title, description=roam.body,roam_url=roam.other)


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
    new_im=new_im.resize((400,200),Image.LANCZOS)

    return new_im
def getkeywords(txt): #return keywords, without hashsign
    return [word[1:] for word in filter(None, re.split("[, !?:;\.]+", txt)) if word.startswith("#")]

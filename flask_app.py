
# reusing teh bones of prediction box
#
#e




from flask import Flask, redirect, render_template, render_template_string,request, url_for
from flask_sqlalchemy import SQLAlchemy
import time
from time import strftime, strptime, mktime
import datetime
from datetime import timedelta
import random
import smtplib
from PIL import Image

from email.message import EmailMessage



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


class Prediction(db.Model):

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    pred = db.Column(db.String(4096))
    cert = db.Column(db.String(100))
    expose_date=db.Column(db.DateTime)
    entry_time=db.Column(db.TIMESTAMP, onupdate=datetime.datetime.now())
    pred_code=db.Column(db.Integer)

prediction=[]
@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("main.html")

    if request.method == "GET":
        return render_template("main_page.html")
    if request.form["prediction"]=="":
        return render_template("main_page.html", wasmissing=1)
    pred_code=int(time.time())+random.randint(0,100000)
    datetouse=request.form["expose_date"] or datetime.datetime.now() #need to correct back for timezone change
    td=timedelta(minutes=int(request.form["timediff"]))
    lt=datetime.datetime.strptime(request.form["expose_date"],"%Y-%m-%dT%H:%M")
    print("lt",lt)
    print("td",td)
    print(lt+td)
    nt=lt+td
    print(request.form["expose_date"],request.form["timediff"], nt.strftime("%Y-%m-%dT%H:%M"))


    c = Prediction(pred=request.form["prediction"], expose_date=nt,pred_code=pred_code, entry_time=datetime.datetime.utcnow())
    db.session.add(c)
    db.session.commit()



    return redirect(url_for('pred',prednumber=pred_code))

@app.route('/test', methods=["GET", "POST"])
def test():
    unfurldata='''
<!-— facebook open graph tags -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://https://showgig.pythonanywhere.com/test" />
<meta property="og:title" content="test gig display with unfurl" />
<meta property="og:description" content="the some text words.<BR>and here a line break?<b>bold</b>" />
<meta property="og:image" content="https://showgig.pythonanywhere.com/static/combo_1.png" />

    
    '''
    img1='<img src="'+url_for('static',filename="examplechart.png")+'" alt="no img1">'
    img2='<img src="'+url_for('static',filename="examplemap.png")+'" alt="no img2">'
    files=['/home/showgig/mysite'+url_for('static',filename='examplemap.png'),'/home/showgig/mysite'+url_for('static',filename='examplechart.png')]
    images = list(map(Image.open, files))

    combo_1 = append_images(images, direction='horizontal')
    combo_1.save('/home/showgig/mysite'+url_for('static',filename='combo_1.png'))
    return render_template_string('<html>'+unfurldata+'<div>some text</div>'+img1+img2+'</html>')

@app.route('/gig/<gignumber>', methods=["GET", "POST"])
def gig(gignumber):
    if request.method == "GET":
#        print("before query",prednumber)
        prediction=Prediction.query.filter(Prediction.pred_code == prednumber).first()
#        print("after query",prediction)
        if(prediction):
            return render_template("pred_page.html", prediction=prediction, instant=datetime.datetime.utcnow()) #prednumber=prediction.pred_code, #seems to fail here!
        print("no such pred",prednumber)
        return render_template("no_such_pred.html",missing_pred=prednumber)




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

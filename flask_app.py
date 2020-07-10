
# reusing teh bones of prediction box
#
#e




from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
import time
from time import strftime, strptime, mktime
import datetime
from datetime import timedelta
import random
import smtplib

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
    returnrender_template("main.html")

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


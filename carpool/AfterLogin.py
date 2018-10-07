import functools
import random
import string
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import json
from werkzeug.security import check_password_hash, generate_password_hash
from carpool.db1 import connector
from carpool.auth import login_required,session_name
from carpool.transaction import *

bp = Blueprint('insidelogin', __name__, url_prefix='/auth')

@bp.route('/offerRide',methods=('GET','POST'))
@login_required
def update():
    if request.method=='POST':
            mailid1= session_name()
            distance=int(request.form['slider1'])

            time=100-distance
            persons=int(request.form['seats'])

            db,conn1 = connector()
            ride= db.offerride
            ride.update_many(
            {"mailid": mailid1,"Time":session.get('time',None)},
            {'$set': { "Distance_flex":distance,
                    "Time_flex":time,
                    "No_of_persons":persons}
            }
            )
            return redirect(url_for('insidelogin.drivercode'))
    return render_template('AfterLogin/offerRide.html')

@bp.route('/cardeets',methods=['GET','POST'])
@login_required
def cardeets():
        if request.method=='POST':
                mailid1= session_name()
                plate=request.form['plate']
                model=request.form['model']
                license=request.form['license']

                db,conn1 = connector()
                user= db.users
                user.update_many(
                {"mailid": mailid1},
                {'$set': { "car_details.0.plate":plate,
                        "car_details.0.model":model,
                        "car_details.0.license":license}
                }
                )
                return redirect(url_for('insidelogin.profile'))
        return render_template('auth/cardeets.html')
@bp.route('/begin', methods=['GET', 'POST'])
@login_required
def takeRoute():
    if request.method == 'POST':
        mailid1 = session_name()
        place1 = request.form['Start']
        place2 = request.form['End']
        date = request.form['Date']
        routeinfo = {
            "mailid":mailid1,
            "Start":place1,
            "End":place2,
            "Time":date,
            "Distance_flex":None,
            "Time_flex":None,
            "No_of_persons":None,
            "waypoints":""
        }
        db,conn1 = connector()
        session['routeinfo']=str(routeinfo)
        if request.form['Ride'] == 'Book Ride':
            return redirect(url_for('afterbookride.showRides'))
            print("ComeBack")
        elif request.form['Ride'] == 'Offer Ride':
            user=db.users
            print("In offer Ride")
            car=user.find({'mailid':mailid1},{'_id':0,'car_details':1})
            plate=car[0]['car_details'][0]['plate']
            print (plate)
            if plate == None:
                return render_template('AfterLogin/Begin.html',check=0)
            ride= db.offerride
            ride.insert_one(routeinfo)
            #print(session['username'])
            session['time'] = routeinfo['Time']
            print("Going to slider")
            return redirect(url_for('insidelogin.update'))

    return render_template('AfterLogin/Begin.html')

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

@bp.route('/drivercode', methods=['GET', 'POST'])
@login_required
def drivercode():

    db,conn1=connector()
    mailid=session_name()
    codes=db.codes
    code=id_generator()
    codes.insert_one({'mailid':mailid,'code':code,'Time':session.get('time',None))})
    return render_template('AfterLogin/congrat.html',code=code)

@bp.route('/passengercode',methods=['GET','POST'])
@login_required
def passengercode():
    mailid=session_name()
    db,conn1=connector()
    codes=db.codes
    activeRides=db.activeRides
    if request.method=='POST':
        code=request.form['code1']
        match=codes.find_one({'code':code})
        if match is None:
            return render_template('AfterLogin/yay.html',match=0)
        else:
            bookedRides=db.bookedRides
            passengerActiveRide=bookedRides.find_one({'mailid':match['mailid'],'mailid':mailid})
            activeRides.insert_one({'mailid':mailid,'trip':passengerActiveRide})
            bookedRides.find_one_and_delete({'mailid':match['mailid'],'mailid':mailid})

            return redirect(url_for('insidelogin.profile'))
    return render_template('AfterLogin/yay.html')
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    mailid=session_name()
    db,conn1=connector()
    users = db.users
    user_prof = users.find_one({'mailid' : mailid })
    car=users.find({'mailid':mailid},{'_id':0,'car_details':1})
    plate=car[0]['car_details'][0]['plate']
    model=car[0]['car_details'][0]['model']
    license=car[0]['car_details'][0]['license']
    user_details = {
        'Name':user_prof['name'],
        'email':mailid,
        'Mobile_No':user_prof['phno'],
        'Car_Number':plate,
        'Car_Model':model,
        'licence_Number':license
        }
    return render_template('AfterLogin/index.html',user=user_details)

@bp.route('/mytrips',methods=['GET','POST'])
@login_required
def mytrips():
    db,conn1=connector()
    bookedRides=db.bookedRides
    passengerRides=bookedRides.find({'mailid':session_name()})
    return render_template('AfterLogin/mytrips.html',passengerRides=passengerRides)

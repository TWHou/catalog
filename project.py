from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from datetime import datetime

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Shelter, Puppy

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

# Load Google client secret
# CLIENT_ID = json.loads(open('clent_secrets.json', 'r').read())['web']['client_id']

# Connect to database and create database session
engine = create_engine('sqlite:///puppyshelter.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# oauth login routes
@app.route('/login')
def showLogin():
    return "This will be the Login page"


@app.route('/gconnect')
def gconnect():
    return "This will be the google connect methods"


@app.route('/gdisconnect')
def gdisconnect():
    return "This disconnects from google"


# JSON API routes
@app.route('/shelter/JSON/')
def shelterJSON():
    shelters = session.query(Shelter).all()
    return jsonify(shelters = [s.serialize for s in shelters])


@app.route('/shelter/<int:shelter_id>/puppy/JSON/')
def listPuppyJSON(shelter_id):
    puppies = session.query(Puppy).filter_by(shelter_id = shelter_id).all()
    return jsonify(puppies = [p.serialize for p in puppies])


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/JSON/')
def puppyJSON(shelter_id, puppy_id):
    puppy = session.query(Puppy).filter_by(id = puppy_id).one()
    return jsonify(puppy = puppy.serialize)


# shelter routes
@app.route('/')
@app.route('/shelter/')
def listShelter():
    shelters = session.query(Shelter).all()
    return render_template("shelter-list.html", shelters=shelters)


@app.route('/shelter/new/', methods=['GET', 'POST'])
def newShelter():
    if request.method == 'POST':
        if request.form['name']:
            name = request.form['name']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            zipCode = request.form['zip']
            # temporarily hardcode user_id before implementing user login
            user_id = 1
            newShelter = Shelter(name=name, address=address, city=city, state=state, zipCode=zipCode, user_id=user_id)
            session.add(newShelter)
            session.commit()
            flash("New Shelter Created")
            return redirect(url_for("listShelter"))
        else:
            flash("A name for your shelter would be deeply appreciated.")
            return render_template('shelter-new.html')
    else:
        return render_template("shelter-new.html")


@app.route('/shelter/<int:shelter_id>/edit/', methods=['GET', 'POST'])
def editShelter(shelter_id):
    shelter = session.query(Shelter).filter_by(id=shelter_id).one()
    if request.method == 'POST':
        if request.form['name']:
            shelter.name = request.form['name']
            shelter.address = request.form['address']
            shelter.city = request.form['city']
            shelter.state = request.form['state']
            shelter.zipCode = request.form['zip']
            session.add(shelter)
            session.commit()
            flash("Shelter Edited")
            return redirect(url_for("listShelter"))
        else:
            flash("You left the shelter name blank. Let me know what it is now called.")
            return render_template("shelter-edit.html", shelter=shelter)
    else:
        return render_template("shelter-edit.html", shelter=shelter)


@app.route('/shelter/<int:shelter_id>/delete/', methods=['GET', 'POST'])
def deleteShelter(shelter_id):
    shelter = session.query(Shelter).filter_by(id=shelter_id).one()
    if request.method == 'POST':
        session.delete(shelter)
        session.commit()
        flash("Shelter Deleted.")
        return redirect(url_for("listShelter"))
    else:
        return render_template("shelter-delete.html", shelter=shelter)


# puppy routes
@app.route('/shelter/<int:shelter_id>/')
@app.route('/shelter/<int:shelter_id>/puppy/')
def listPuppy(shelter_id):
    shelter = session.query(Shelter).filter_by(id=shelter_id).one()
    puppies = session.query(Puppy).filter_by(shelter_id=shelter.id).all()
    return render_template("puppy-list.html", shelter=shelter, puppies=puppies)


@app.route('/shelter/<int:shelter_id>/puppy/new/', methods = ['GET', 'POST'])
def newPuppy(shelter_id):
    shelter = session.query(Shelter).filter_by(id=shelter_id).one()
    if request.method == 'POST':
        if request.form['name'] and request.form['sex']:
            name = request.form['name']
            sex = request.form['sex']
            dateOfBirth = datetime.strptime(request.form['dob'], "%Y-%m-%d")
            picture = request.form['picture']
            newPuppy = Puppy(name=name, sex=sex, dateOfBirth=dateOfBirth, picture=picture, shelter_id=shelter_id)
            session.add(newPuppy)
            session.commit()
            flash("%s is now looking for a forever home." % name)
            return redirect(url_for('listPuppy', shelter_id=shelter_id))
        else:
            if not request.form['name']:
                flash("Please name the puppy so we'll know who's been a good dog.");
            if not request.form['sex']:
                flash("Not trying to assume their gender, but the sex of the puppy would really help.")
                return render_template("puppy-new.html", shelter = shelter)
    else:
        return render_template("puppy-new.html", shelter=shelter)


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/')
def detailPuppy(shelter_id, puppy_id):
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    return render_template("puppy-detail.html", shelter_id=shelter_id, puppy=puppy)


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/edit/', methods = ['GET', 'POST'])
def editPuppy(shelter_id, puppy_id):
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    if request.method == 'POST':
        if request.form['name'] and request.form['sex']:
            puppy.name = request.form['name']
            puppy.sex = request.form['sex']
            puppy.dateOfBirth = datetime.strptime(request.form['dob'], "%Y-%m-%d")
            puppy.picture = request.form['picture']
            puppy.shelter_id = shelter_id
            session.add(puppy)
            session.commit()
            flash("%s's info has been updated." % puppy.name)
            return redirect(url_for('detailPuppy', shelter_id=shelter_id, puppy_id=puppy_id))
        else:
            if not request.form['name']:
                flash("Please name the puppy so we'll know who's been a good dog.");
            if not request.form['sex']:
                flash("Not trying to assume their gender, but the sex of the puppy would really help.")
                return render_template("puppy-edit.html", puppy = puppy)
    else:
        return render_template("puppy-edit.html", shelter_id=shelter_id, puppy=puppy)


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/delete/', methods = ['GET', 'POST'])
def deletePuppy(shelter_id, puppy_id):
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    if request.method == 'POST':
        session.delete(puppy)
        session.commit()
        flash("Congradulations, %s!" % puppy.name)
        return redirect(url_for('listPuppy', shelter_id = shelter_id))
    else:
        return render_template("puppy-delete.html", shelter_id=shelter_id, puppy=puppy)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

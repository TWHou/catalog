from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Shelter, Puppy

from flask import session as login_session
import random, string

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
@app.route('/shelter/JSON')
def shelterJSON():
    return "JSON of all shelters"

@app.route('/shelter/<int:shelter_id>/puppy/JSON')
def listPuppyJSON(shelter_id):
    return "JSON of puppies at one shelter"

@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/JSON')
def puppyJSON(shelter_id, puppy_id):
    return "JSON of puppy detail"

# shelter routes
@app.route('/')
@app.route('/shelter/')
def listShelter():
    return render_template("shelter-list.html")

@app.route('/shelter/new/')
def newShelter():
    return render_template("shelter-new.html")

@app.route('/shelter/<int:shelter_id>/edit/')
def editShelter(shelter_id):
    return render_template("shelter-edit.html", shelter = shelter_id)

@app.route('/shelter/<int:shelter_id>/delete/')
def deleteShelter(shelter_id):
    return render_template("shelter-delete.html", shelter = shelter_id)

# puppy routes
@app.route('/shelter/<int:shelter_id>/')
@app.route('/shelter/<int:shelter_id>/puppy/')
def listPuppy(shelter_id):
    return render_template("puppy-list.html", shelter = shelter_id)

@app.route('/shelter/<int:shelter_id>/puppy/new/')
def newPuppy(shelter_id):
    return render_template("puppy-new.html", shelter = shelter_id)

@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/')
def detailPuppy(shelter_id, puppy_id):
    return render_template("puppy-detail.html", puppy = puppy_id)

@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/edit/')
def editPuppy(shelter_id, puppy_id):
    return render_template("puppy-edit.html", puppy = puppy_id)

@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/delete/')
def deletePuppy(shelter_id, puppy_id):
    return render_template("puppy-delete.html", puppy = puppy_id)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)

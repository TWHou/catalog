from flask import (Flask, render_template, request, redirect, jsonify,
                   url_for, flash, make_response)
from datetime import datetime

from functools import wraps

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Shelter, Puppy

from flask import session as login_session
import random
import string

from oauth2client import client, crypt
import httplib2
import json
import requests

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

# Connect to database and create database session
engine = create_engine('sqlite:///puppyshelter.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = app.config['CLIENT_ID']


def createUser(login_session):
    """Creates user using data in session variable"""
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserId(email):
    """Returns user id using email"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if login_session['username']:
                return f(*args, **kwargs)
        except KeyError:
            flash("You must sign in first.")
            return redirect(url_for('listShelter'))
    return decorated_function


def owns_shelter(f):
    @wraps(f)
    def decorated_function(shelter_id, *args, **kwargs):
        shelter = session.query(Shelter).filter_by(id=shelter_id).one()
        if shelter.user_id != login_session['user_id']:
            flash("You do not own this shelter.")
            return redirect(url_for('listPuppy', shelter_id=shelter.id))
        return f(shelter, *args, **kwargs)
    return decorated_function


# oauth login routes

@app.route('/login')
def showLogin():
    """Set state variable and show login screen for google oauth"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('googleauth.html', STATE=state, CLIENT_ID=CLIENT_ID)


@app.route('/logout')
def showLogout():
    """Confirm logout for google oauth"""
    return render_template('googleauth.html', CLIENT_ID=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Handle authentication of google token"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps("Invalid state parameter"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    try:
        idinfo = client.verify_id_token(request.form['idtoken'], CLIENT_ID)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
    except crypt.AppIdentityError:
        response = make_response(json.dumps('Invalid Token.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    gid = idinfo['sub']

    # Check if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gid = login_session.get('gid')
    if stored_credentials is not None and gid == stored_gid:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'applcation/json'
        return response

    # Store access token in session
    login_session['credentials'] = idinfo
    login_session['gid'] = gid
    login_session['username'] = idinfo['name']
    login_session['picture'] = idinfo['picture']
    login_session['email'] = idinfo['email']

    # Check if user registered, if not, register user
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width: 300px; height: 300px; border-radius: 150px;">'
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Clear session variables after google sign out"""
    del login_session['credentials']
    del login_session['gid']
    del login_session['username']
    del login_session['picture']
    del login_session['email']
    del login_session['user_id']
    response = make_response(json.dumps('Successfully Signed Out.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


# JSON API routes
@app.route('/shelter/JSON/')
def shelterJSON():
    """Return shelters in JSON format"""
    shelters = session.query(Shelter).all()
    return jsonify(shelters=[s.serialize for s in shelters])


@app.route('/shelter/<int:shelter_id>/puppy/JSON/')
def listPuppyJSON(shelter_id):
    """Return puppies in the shelter in JSON format"""
    puppies = session.query(Puppy).filter_by(shelter_id=shelter_id).all()
    return jsonify(puppies=[p.serialize for p in puppies])


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/JSON/')
def puppyJSON(shelter_id, puppy_id):
    """Return puppy info in JSON format"""
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    return jsonify(puppy=puppy.serialize)


# shelter routes
@app.route('/')
@app.route('/shelter/')
def listShelter():
    """Show list of shelters"""
    shelters = session.query(Shelter).all()
    return render_template("shelter-list.html", shelters=shelters)


@app.route('/shelter/new/', methods=['GET', 'POST'])
@logged_in
def newShelter():
    """Create new shelter"""
    if request.method == 'POST':
        if request.form['name']:
            name = request.form['name']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            zipCode = request.form['zip']
            user_id = login_session['user_id']
            newShelter = Shelter(name=name, address=address, city=city,
                                 state=state, zipCode=zipCode, user_id=user_id)
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
@logged_in
@owns_shelter
def editShelter(shelter):
    """Edit shelter details"""
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
            flash("You left the shelter name blank. \
                  Let me know what it is now called.")
            return render_template("shelter-edit.html", shelter=shelter)
    else:
        return render_template("shelter-edit.html", shelter=shelter)


@app.route('/shelter/<int:shelter_id>/delete/', methods=['GET', 'POST'])
@logged_in
@owns_shelter
def deleteShelter(shelter):
    """Delete shelter from database"""
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
    """List all puppies in the shelter"""
    shelter = session.query(Shelter).filter_by(id=shelter_id).one()
    puppies = session.query(Puppy).filter_by(shelter_id=shelter.id).all()
    return render_template("puppy-list.html", shelter=shelter, puppies=puppies)


@app.route('/shelter/<int:shelter_id>/puppy/new/', methods=['GET', 'POST'])
@logged_in
@owns_shelter
def newPuppy(shelter):
    """Add new puppy to the shelter"""
    if request.method == 'POST':
        if request.form['name'] and request.form['sex']:
            name = request.form['name']
            sex = request.form['sex']
            dateOfBirth = datetime.strptime(request.form['dob'], "%Y-%m-%d")
            picture = request.form['picture']
            newPuppy = Puppy(name=name, sex=sex, dateOfBirth=dateOfBirth,
                             picture=picture, shelter_id=shelter.id)
            session.add(newPuppy)
            session.commit()
            flash("%s is now looking for a forever home." % name)
            return redirect(url_for('listPuppy', shelter_id=shelter.id))
        else:
            if not request.form['name']:
                flash("Please name the puppy \
                      so we'll know who's been a good dog.")
            if not request.form['sex']:
                flash("Not trying to assume their gender, \
                      but the sex of the puppy would really help.")
                return render_template("puppy-new.html", shelter=shelter)
    else:
        return render_template("puppy-new.html", shelter=shelter)


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/')
def detailPuppy(shelter_id, puppy_id):
    """Show details about puppy"""
    shelter = session.query(Shelter).filter_by(id=shelter_id).one()
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    return render_template("puppy-detail.html", shelter=shelter, puppy=puppy)


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/edit/',
           methods=['GET', 'POST'])
@logged_in
@owns_shelter
def editPuppy(shelter, puppy_id):
    """Change puppy details"""
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    if request.method == 'POST':
        if request.form['name'] and request.form['sex']:
            puppy.name = request.form['name']
            puppy.sex = request.form['sex']
            puppy.dateOfBirth = datetime.strptime(
                request.form['dob'], "%Y-%m-%d")
            puppy.picture = request.form['picture']
            puppy.shelter_id = shelter.id
            session.add(puppy)
            session.commit()
            flash("%s's info has been updated." % puppy.name)
            return redirect(url_for('detailPuppy', shelter_id=shelter.id,
                                    puppy_id=puppy_id))
        else:
            if not request.form['name']:
                flash("Please name the puppy \
                      so we'll know who's been a good dog.")
            if not request.form['sex']:
                flash("Not trying to assume their gender, \
                      but the sex of the puppy would really help.")
                return render_template("puppy-edit.html", puppy=puppy)
    else:
        return render_template("puppy-edit.html", shelter_id=shelter.id,
                               puppy=puppy)


@app.route('/shelter/<int:shelter_id>/puppy/<int:puppy_id>/delete/',
           methods=['GET', 'POST'])
@logged_in
@owns_shelter
def deletePuppy(shelter, puppy_id):
    """Remove puppy from database"""
    puppy = session.query(Puppy).filter_by(id=puppy_id).one()
    if request.method == 'POST':
        session.delete(puppy)
        session.commit()
        flash("Congradulations, %s!" % puppy.name)
        return redirect(url_for('listPuppy', shelter_id=shelter.id))
    else:
        return render_template("puppy-delete.html", shelter_id=shelter.id,
                               puppy=puppy)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

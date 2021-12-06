#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm


from forms import *
import sys
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  ''' data=[{
      "city": "San Francisco",
      "state": "CA",
      "venues": [{
        "id": 1,
        "name": "The Musical Hop",
        "num_upcoming_shows": 0,
      }, {
        "id": 3,
        "name": "Park Square Live Music & Coffee",
        "num_upcoming_shows": 1,
      }]
    }, {
      "city": "New York",
      "state": "NY",
      "venues": [{
        "id": 2,
        "name": "The Dueling Pianos Bar",
        "num_upcoming_shows": 0,
      }]
    }]
    '''
  # send query via sqlalchemy to database for state,city distinct pairs to use later  
  state_cities = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  print(state_cities);
  data = []
  for item in state_cities:

        # Querying venues and filter them based on area (city, venue) pair value
        venues_list = Venue.query.filter(Venue.state == item.state).filter(Venue.city == item.city).all()

        venue_infos = []

        # Creating venues' response as required by commented above requirement
        for venue in venues_list:
            venue_infos.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
            })

        data.append({
                'city': item.city,
                'state': item.state,
                'venues': venue_infos
        })


  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    venues_list = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
    list_result = []
    for venue in venues_list:
            list_result.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).filter(Show.venue_id == venue.id).all())
            })
    response = {
          "count": len(venues_list),
          "data": list_result
      }
    '''  response={
            "count": len(venues_list),
            "data": [{
              "id": 2,
              "name": "The Dueling Pianos Bar",
              "num_upcoming_shows": 0,
            }]
        }
    '''
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter(Venue.id == venue_id).first()

  past = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
        Show.start_time < datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                                Artist.image_link,
                                                                                                Show.start_time).all()

  # flter Shows by venue_id and joins with Artist to pickup other fields like name,image_link of artist
  upcoming = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
        Show.start_time > datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                                Artist.image_link,
                                                                                                Show.start_time).all()
  # forming the requeted json format as specified in below commented reauirement
  upcoming_shows = []

  past_shows = []

  for upshow in upcoming:
        upcoming_shows.append({
            'artist_id': upshow[1],
            'artist_name': upshow[2],
            'image_link': upshow[3],
            'start_time': str(upshow[4])
        })

  for pastshow in past:
        past_shows.append({
            'artist_id': pastshow[1],
            'artist_name': pastshow[2],
            'image_link': pastshow[3],
            'start_time': str(pastshow[4])
        })

  if venue is None:
        abort(404)

  data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [venue.genres],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past),
        "upcoming_shows_count": len(upcoming),
    }

  '''  data1={
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
        "past_shows": [{
          "artist_id": 4,
          "artist_name": "Guns N Petals",
          "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
          "start_time": "2019-05-21T21:30:00.000Z"
        }],
        "upcoming_shows": [],
        "past_shows_count": 1,
        "upcoming_shows_count": 0,
      }
      data2={
        "id": 2,
        "name": "The Dueling Pianos Bar",
        "genres": ["Classical", "R&B", "Hip-Hop"],
        "address": "335 Delancey Street",
        "city": "New York",
        "state": "NY",
        "phone": "914-003-1132",
        "website": "https://www.theduelingpianos.com",
        "facebook_link": "https://www.facebook.com/theduelingpianos",
        "seeking_talent": False,
        "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
      }
      data3={
        "id": 3,
        "name": "Park Square Live Music & Coffee",
        "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
        "address": "34 Whiskey Moore Ave",
        "city": "San Francisco",
        "state": "CA",
        "phone": "415-000-1234",
        "website": "https://www.parksquarelivemusicandcoffee.com",
        "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
        "seeking_talent": False,
        "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
        "past_shows": [{
          "artist_id": 5,
          "artist_name": "Matt Quevedo",
          "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
          "start_time": "2019-06-15T23:00:00.000Z"
        }],
        "upcoming_shows": [{
          "artist_id": 6,
          "artist_name": "The Wild Sax Band",
          "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
          "start_time": "2035-04-01T20:00:00.000Z"
        }, {
          "artist_id": 6,
          "artist_name": "The Wild Sax Band",
          "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
          "start_time": "2035-04-08T20:00:00.000Z"
        }, {
          "artist_id": 6,
          "artist_name": "The Wild Sax Band",
          "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
          "start_time": "2035-04-15T20:00:00.000Z"
        }],
        "past_shows_count": 1,
        "upcoming_shows_count": 1,
      }
      data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    '''
 
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  body={}
  dup_count = 0;
  form = VenueForm()
  print(form.name.data);
  try:
        # TODO: insert form data as a new Venue record in the db, instead
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        dup_count = Venue.query.filter_by(name = form.name.data).count()
        if dup_count == 0 :
          db.session.add(venue)
          db.session.commit()
        
          # TODO: modify data to be the data object returned from db insertion
          body['name'] = venue.name
          body['city'] = venue.city
          body['state'] = venue.state
          body['address'] = venue.address
          body['phone'] = venue.phone
          body['genres'] = venue.genres
          body['image_link'] = venue.image_link
          body['facebook_link'] = venue.facebook_link
          body['website_link'] = venue.website_link
          body['seeking_talent'] = venue.seeking_talent
          body['seeking_description'] = venue.seeking_description
          # on successful db insert, flash success
          print(jsonify(body))

          flash('Venue ' + request.form['name'] + ' was successfully listed!')
        else :
          flash('An error occurred. Venue ' + request.form['name'] + ' is duplicated.')
  except Exception as e:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        print(jsonify(body))
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        db.session.rollback()
        print(e)
        
  finally:
        db.session.close()


  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  #print('hello deleting')
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(e)
  finally:
    db.session.close()
  if error: 
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')
  if not error: 
    flash(f'Venue {venue_id} was successfully deleted.')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  #return render_template('pages/home.html')
  #return jsonify({ 'success': True })
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data =  db.session.query(Artist.id,Artist.name).all()
  ''' data=[{
      "id": 4,
      "name": "Guns N Petals",
    }, {
      "id": 5,
      "name": "Matt Quevedo",
    }, {
      "id": 6,
      "name": "The Wild Sax Band",
    }]
    '''
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    artist_list = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
    count = len(artist_list)
    list_result = []
    for artist in artist_list:
            list_result.append({
                'id': artist.id,
                'name': artist.name,
                'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).filter(Show.artist_id == artist.id).all())
            })
    response = {
        "count": count,
        "data": artist_list
    }
    ''' response={
        "count": count,
        "data": [{
          "id": 4,
          "name": "Guns N Petals",
          "num_upcoming_shows": len(db.session.query(Show).filter(Show.start_time > datetime.now()).filter(Show.venue_id == venue_id).all()),
        }]
      }
      '''
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.filter(Artist.id == artist_id).first()

  list_past = db.session.query(Show).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name,
                                                                                                Venue.image_link,
                                                                                                Show.start_time).all()

  list_upcoming = db.session.query(Show).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name,
                                                                                                Venue.image_link,
                                                                                                Show.start_time).all()

  upcoming_shows = []

  past_shows = []

  for upshow in list_upcoming:
        upcoming_shows.append({
            'venue_id': upshow[1],
            'venue_name': upshow[2],
            'image_link': upshow[3],
            'start_time': str(upshow[4])
        })

  for pastshow in list_past:
        past_shows.append({
            'venue_id': pastshow[1],
            'venue_name': pastshow[2],
            'image_link': pastshow[3],
            'start_time': str(pastshow[4])
        })

  if artist is None:
        abort(404)

  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [artist.genres],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(list_past),
        "upcoming_shows_count": len(list_upcoming),
    }
  '''  data1={
      "id": 4,
      "name": "Guns N Petals",
      "genres": ["Rock n Roll"],
      "city": "San Francisco",
      "state": "CA",
      "phone": "326-123-5000",
      "website": "https://www.gunsnpetalsband.com",
      "facebook_link": "https://www.facebook.com/GunsNPetals",
      "seeking_venue": True,
      "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
      "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
      "past_shows": [{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
        "start_time": "2019-05-21T21:30:00.000Z"
      }],
      "upcoming_shows": [],
      "past_shows_count": 1,
      "upcoming_shows_count": 0,
    }
    data2={
      "id": 5,
      "name": "Matt Quevedo",
      "genres": ["Jazz"],
      "city": "New York",
      "state": "NY",
      "phone": "300-400-5000",
      "facebook_link": "https://www.facebook.com/mattquevedo923251523",
      "seeking_venue": False,
      "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
      "past_shows": [{
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
      }],
      "upcoming_shows": [],
      "past_shows_count": 1,
      "upcoming_shows_count": 0,
    }
    data3={
      "id": 6,
      "name": "The Wild Sax Band",
      "genres": ["Jazz", "Classical"],
      "city": "San Francisco",
      "state": "CA",
      "phone": "432-325-5432",
      "seeking_venue": False,
      "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "past_shows": [],
      "upcoming_shows": [{
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
      }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
      }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
      }],
      "past_shows_count": 0,
      "upcoming_shows_count": 3,
    }
    data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
    '''
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  
  ''' artist={
      "id": 4,
      "name": "Guns N Petals",
      "genres": ["Rock n Roll"],
      "city": "San Francisco",
      "state": "CA",
      "phone": "326-123-5000",
      "website": "https://www.gunsnpetalsband.com",
      "facebook_link": "https://www.facebook.com/GunsNPetals",
      "seeking_venue": True,
      "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
      "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    '''
  # TODO: populate form with fields from artist with ID <artist_id>
  current_artist = Artist.query.get(artist_id)
  #form_availability.artist_id.data = artist_id;
  if current_artist: 
    # get availabilities times by sqlalchemy for current artist to return back to user
    availabilities = db.session.query(Availability).filter(Availability.artist_id == artist_id).all()
    # fill the form by current values to send over reauest so the user can change if desired
    form.name.data = current_artist.name
    form.city.data = current_artist.city
    form.state.data = current_artist.state
    form.phone.data = current_artist.phone
    form.genres.data = current_artist.genres
    form.facebook_link.data = current_artist.facebook_link
    form.image_link.data = current_artist.image_link
    form.website_link.data = current_artist.website_link
    form.seeking_venue.data =current_artist.seeking_venue
    form.seeking_description.data = current_artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=current_artist, availabilities= availabilities)

@app.route('/availability/<int:availability_id>/<int:artist_id>', methods=['GET'])
def delete_availability(availability_id, artist_id):
  form = ArtistForm()
  # read  current deleted avialability to be deleted
  current_availability = db.session.query(Availability).filter(Availability.id == availability_id).first()
  db.session.delete(current_availability)
  db.session.commit()
  # get updated list after deleting to send back
  availabilities = db.session.query(Availability).filter(Availability.artist_id == artist_id).all()
  edited_artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=edited_artist, availabilities= availabilities)
   



@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False 
    redirect_info = True
    form = ArtistForm()
    # get list of availabilities for this artist  and current edited artist
    availabilities = db.session.query(Availability).filter(Availability.artist_id == artist_id).all()
    edited_artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
      
    try:
      #  check if forms was submitted by add_time click button: so we have to add a new availability and link it with current artist
      if form.add_time.data == True:
        print('herrre')
        # mark current time as non bocked yet, so it will available to use by venu later when adding a show if desired
        # if availability already booked , it will not shows in list of availabilities on artist editing page.
        form.booked.data = False;
        availability_to_add = Availability(available_time=form.available_time.data,
                                     booked = False,
                                     artist_id = artist_id)
        availability_to_add.artist = edited_artist
        db.session.add(edited_artist)
        db.session.commit()
        availabilities = db.session.query(Availability).filter(Availability.artist_id == artist_id).all()
        return render_template('forms/edit_artist.html', form=form, artist=edited_artist, availabilities= availabilities)
      
      # check if the form was submitted by bootm submit button so we will save all artist fields into database
      if form.add_time.data == False:
      
        edited_artist.name = form.name.data
        edited_artist.city = form.city.data,
        edited_artist.state = form.state.data,
        
        edited_artist.phone = form.phone.data,
        edited_artist.genres = form.genres.data,
        edited_artist.image_link = form.image_link.data,
        edited_artist.facebook_link = form.facebook_link.data,
        edited_artist.website_link = form.website_link.data,
        # check if seeking_venu is included 
        if 'seeking_venue' in request.form :
         edited_artist.seeking_venue = True
        else :
         edited_artist.seeking_venue = False
        edited_artist.seeking_description = form.seeking_description.data
        db.session.add(edited_artist)
        db.session.commit()
    except Exception as e: 
      error = True
      db.session.rollback()
      print(e)
    finally: 
      db.session.close()
    if error: 
      flash('An error occurred. Artist edit problem happened.')
    if not error: 
      flash('Artist was successfully changed')

   
    return redirect(url_for('show_artist', artist_id=artist_id, availabilities= availabilities)) 

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  #edited_venue = Venue.query.filter(Venue.id == venue_id).first()
  ''' venue={
      "id": 1,
      "name": "The Musical Hop",
      "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
      "address": "1015 Folsom Street",
      "city": "San Francisco",
      "state": "CA",
      "phone": "123-123-1234",
      "website": "https://www.themusicalhop.com",
      "facebook_link": "https://www.facebook.com/TheMusicalHop",
      "seeking_talent": True,
      "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
      "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
  '''
  # TODO: populate form with values from venue with ID <venue_id>
  current_venue = Venue.query.filter(Venue.id == venue_id).first()
  form.name.data = current_venue.name
  
  form.city.data = current_venue.city
  form.state.data = current_venue.state
  form.address.data = current_venue.address
  form.phone.data = current_venue.phone
  form.genres.data = current_venue.genres
  form.image_link.data = current_venue.image_link
  form.facebook_link.data = current_venue.facebook_link
  form.website_link.data = current_venue.website_link
  form.seeking_talent.data = current_venue.seeking_talent
  form.seeking_description.data = current_venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=current_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm()
  try:
    edited_venue = Venue.query.filter(Venue.id == venue_id).first()
    edited_venue.name = form.name.data
    edited_venue.city = form.city.data,
    edited_venue.state = form.state.data,
    edited_venue.address = form.address.data,
    edited_venue.phone = form.phone.data,
    edited_venue.genres = form.genres.data,
    edited_venue.image_link = form.image_link.data,
    edited_venue.facebook_link = form.facebook_link.data,
    edited_venue.website_link = form.website_link.data,
    if 'seeking_talent' in request.form :
     edited_venue.seeking_talent = True
    else:
     edited_venue.seeking_talent = False
    edited_venue.seeking_description = form.seeking_description.data
    db.session.add(edited_venue)
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(e)
  finally: 
    db.session.close()
  if error: 
    flash(f'An error occurred.edit problem happened.')
  if not error: 
    flash(f'Venue was successfully changed!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  body={}
  dup_count = 0;
  form = ArtistForm()
  print(form.name.data);
  try:
        # TODO: insert form data as a new Venue record in the db, instead
  
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
        )
        dup_count = Artist.query.filter_by(name = form.name.data).count()
        if dup_count == 0 :
          db.session.add(artist)
          db.session.commit()
        
          # TODO: modify data to be the data object returned from db insertion
          body['name'] = artist.name
          body['city'] = artist.city
          body['state'] = artist.state
          body['phone'] = artist.phone
          body['genres'] = artist.genres
          body['image_link'] = artist.image_link
          body['facebook_link'] = artist.facebook_link
          body['website_link'] = artist.website_link
          body['seeking_venue'] = artist.seeking_venue
          body['seeking_description'] = artist.seeking_description
          
          print(jsonify(body))
          # on successful db insert, flash success
          flash('Artist ' + form.name.data + ' was successfully listed!')
          
        else :
          flash('An error occurred. Venue ' + form.name.data + ' is duplicated.')
  except Exception as e:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        print(jsonify(body))
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
        db.session.rollback()
        print(e)
        
  finally:
        db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  ''' data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
   }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
   }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
   }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
   }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
   }]
  '''
  # joins Show with Artist and venue to render full infoemation about the show
  data = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).all()

  response = []
  for show in data:
        response.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })

  return render_template('pages/shows.html', shows=response)



@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  
  #form.sstart_time.choices.insert(1,'ddddd')
  #form.sstart_time.choices.insert(2,'ccccckll kkk')
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()
  try:
    # check if user requests to fill times list on the form  to choose right vailable time.

    if form.update_time_list.data == True:
      # read not yet booked availabilities for current artist
      availabilities = db.session.query(Availability).filter(Availability.artist_id == form.artist_id.data,Availability.booked == False).all()
      # forming list of tuples for combobox of availabilities
      # form a list of times to use on form dropdown list by applying on choices
      availabilities_list = [(av.id, av.available_time) for av in availabilities]
      form.sstart_time.choices = availabilities_list
      return render_template('forms/new_show.html', form=form)
    # check if form submitted to adding new show
    if form.update_time_list.data == False:
      print(form.sstart_time.id)
      # read choosed(selected) availability and link it to a show before commit
      availability = db.session.query(Availability).get(form.sstart_time.data)
      availability.booked =True
      db.session.add(availability)
      db.session.commit()



    show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=availability.available_time
        )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except Exception as e:
        print(e)
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Show could not be listed')
        db.session.rollback()
  finally:
        db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

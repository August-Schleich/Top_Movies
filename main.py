from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import json
import requests
from pprint import pprint
from os import environ
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.app_context().push()

# app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top-movie-list.db"
db = SQLAlchemy(app)
# MOVIE API CREDENTIALS

# API_KEY= environ.get('API_KEY')
API_KEY = 'd163201d6cd5122c27335c50341e5b0b'
REQUEST_URL = "https://api.themoviedb.org/3/search/movie"

# API_READ_ACCESS_TOKEN= environ.get('API_READ_ACCESS_TOKEN')
API_READ_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJkMTYzMjAxZDZjZDUxMjJjMjczMzVjNTAzNDFlNWIwYiIsInN1YiI6IjYzOGU1MmJjYzJiOWRmMDA4Y2MxMGQ3NSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.-vy1XQoIT468POzhbeSKNbTnm19CDmhbIR2oCdHFH1A'
api_key = '{{API_KEY}}'
language = 'en-US'

       

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250),unique=False, nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
    
    def __repr__(self):
        return f'<Movie {self.title}>'

# db.create_all()

# # NEW MOVIE TEMPLATE FOR DB
# new_movie = Movie(
#     id = 1,
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()

    
@app.route("/")
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating).all()
    
    for i in range(len(all_movies)):
        #This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
        
    db.session.commit()
    return render_template("index.html", movies = all_movies)


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add")
    
@app.route("/add", methods=["POST","GET"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(REQUEST_URL, params={"api_key":API_KEY, "query": movie_title})
        data = response.json()["results"]
        title = form.title.data
        return render_template("select.html", options=data, title=title)

    return render_template("add.html", form=form)

class RateMovieForm(FlaskForm):
    rating = FloatField( "Your Rating Out of 10 e.g. 7.5 (Enter as a whole or decimal number)", validators=[DataRequired(), NumberRange(min=1, max=10, message="Please enter a number between in the range of 1.0-10.0")])
    review = StringField("Your Review",validators=[DataRequired(),])
    submit = SubmitField("Done")
    
         
@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'
@app.route("/find")
def find_movie():
    rating_count = 0
    movie_api_id = request.args.get("id")
    print(movie_api_id)
    if movie_api_id:
        movie_api_url = f"{REQUEST_URL}/{movie_api_id}"
        print(movie_api_url)
        response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_api_id}?api_key={API_KEY}")
        data = response.json()
        review= data["title"]
        new_movie = Movie(
            id=movie_api_id,
            title=data["title"],
            rating=0.0,
            review=f"{review}  No Review",
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{TMDB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        rating_count +=1
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("home"))

@app.route("/delete")
def delete():
        movie_id = request.args.get('id')

    # DELETE A RECORD BY ID
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

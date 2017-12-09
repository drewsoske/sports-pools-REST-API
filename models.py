from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pools.db')
db = SQLAlchemy(app)

# Create your models here.
SPORT_IDS = (
        (1, 'NHL'),
        (2, 'NBA'),
        (3, 'MLB'),
    )


# Member Model
class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False)
    email = db.Column(db.String(200), unique=False)
    name = db.Column(db.String(200), unique=False)

    def __init__(self, sport_id, email, name):
        self.sport_id = sport_id
        self.email = email
        self.name - name


# Team Model
class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False, nullable=True)
    name = db.Column(db.String(200), unique=False, nullable=True)
    city = db.Column(db.String(200), unique=False, nullable=True)

    def __init__(self, sport_id, name, city):
        self.sport_id = sport_id
        self.name = name
        self.city = city


# Member Team Model
class MembersTeams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    def __init__(self, member_id, team_id):
        self.member_id = member_id
        self.team_id = team_id


# Pool Column Model
class SportsColumns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False, nullable=False)
    name = db.Column(db.String(15), unique=False, nullable=False)

    def __init__(self, sport_id, name):
        self.sport_id = sport_id
        self.name = name


# Pool Column Team Model
class SportsColumnsTeams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False, nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('sports_pools.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    def __init__(self, sport_id, column_id, team_id):
        self.sport_id = sport_id
        self.column_id = column_id


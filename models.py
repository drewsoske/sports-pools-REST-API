from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from flask_jsontools import JsonSerializableBase
from sqlalchemy.inspection import inspect

import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pools.db')
db = SQLAlchemy(app)

Base = declarative_base(cls=(JsonSerializableBase,))

# Create your models here.
SPORT_IDS = (
        (1, 'NHL'),
        (2, 'NBA'),
        (3, 'MLB'),
    )


class Serializer(object):
    def serialize(self):
        #return {'id': self.id, 'name': self.name}
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


# Member Model
class Members(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False)
    email = db.Column(db.String(200), unique=False)
    name = db.Column(db.String(200), unique=False)

    def __init__(self, sport_id, email, name):
        self.sport_id = sport_id
        self.email = email
        self.name = name

    def serialize(self):
        d = Serializer.serialize(self)
        return d


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

    def serialize(self):
        d = Serializer.serialize(self)
        return d


# Member Team Model
class MembersTeams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    column_id = db.Column(db.Integer, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    def __init__(self, member_id, column_id, team_id):
        self.member_id = member_id
        self.column_id = column_id
        self.team_id = team_id

    def serialize(self):
        d = Serializer.serialize(self)
        return d


# Pool Column Model
class SportsColumns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False, nullable=False)
    name = db.Column(db.String(15), unique=False, nullable=False)

    def __init__(self, sport_id, name):
        self.sport_id = sport_id
        self.name = name

    def serialize(self):
        d = Serializer.serialize(self)
        return d


# Pool Column Team Model
class SportsColumnsTeams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, unique=False, nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('sports_pools.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    def __init__(self, sport_id, column_id, team_id):
        self.sport_id = sport_id
        self.column_id = column_id

    def serialize(self):
        d = Serializer.serialize(self)
        return d

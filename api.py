from flask import Flask, request, abort, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine

from models import Members, Teams, MembersTeams, SportsColumns, SportsColumnsTeams

import logging
import os
import simplejson as json
import requests
import unicodedata


db_connect = create_engine('sqlite:///pools.db')
app = Flask(__name__)

@app.route("/log")
def logTest():
    return "Code Handbook !! Log testing."

api = Api(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pools.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Feeds:
    def get(self, sport_id):
        d = 'nun'
        if sport_id == 1:
            url = "http://statsapi.web.nhl.com/api/v1/standings?season=20172018"
            r = requests.get(url, stream=True)
            d = json.loads(r.text)
            return d
        elif sport_id == 2:
            url = "https://erikberg.com/nba/standings.json"
            user_agent = {'User-agent': 'DrewSoskePDX, apsapi.drewsoske.com, drew@drewsoske.com'}
            r = requests.get(url, headers=user_agent, stream=True)
            d = json.loads(r.text)
            return d

class Parser:
    def get(self, sport_id, feed, seed=False):
        t, output, seeder = Utility(), {}, []
        if sport_id == 1:
            for conference in feed['records']:
                for team in conference['teamRecords']:
                    name = t.strip_accents(team['team']['name'])
                    output[name] = team['points']
                    seeder.append(name)
        elif sport_id == 2:
            for team in feed['standing']:
                #n = str(team['first_name']) + ' ' + str(team['last_name'])
                n = unicode(team['first_name']) + ' ' + unicode(team['last_name'])
                name = t.strip_accents(n)
                output[name] = team['won']
                seeder.append(name)
        if seed:
            return seeder
        return output


class Utility:
    def strip_accents(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')


class NHL(Resource):
    sport_id = 1
    api_name = 'build'

    def feed(self, sport_id):
        feeds = Feeds()
        feed = feeds.get(sport_id)
        return feed

    def parse(self, sport_id, feed):
        parser = Parser()
        parsed = parser.get(sport_id, feed)
        return parsed
        t, output = Utility(), {}
        if sport_id == 1:
            for conference in feed['records']:
                for team in conference['teamRecords']:
                    name = t.strip_accents(team['team']['name'])
                    output[name] = team['points']
        elif sport_id == 2:
            for team in feed['standing']:
                n = str(team['first_name']) + ' ' + str(team['last_name'])
                name = t.strip_accents(n)
                output[name] = team['won']
        return output

    # returns just a list of pool members
    def members(self, sport_id):
        mbs = {}
        ms = Members.query.filter(Members.sport_id == sport_id).all()
        for m in ms:
            mbs[m.id] = m.name
        return mbs

    # returns just a list of pool members/or one with their current standings
    def member(self, feed, member_id, sport_id):
        conn = db_connect.connect()  # connect to database
        d, db_members = {}, None
        if member_id == 'all':
            db_members = Members.query.filter(Members.sport_id == sport_id).all()
        elif member_id:
            db_members = Members.query.get(member_id)

        if db_members:
            ordered, members = {}, {}
            for member in db_members:
                d = {'name': member.name, 'total': 0}
                member_teams = Teams.query.join(MembersTeams, Teams.id==MembersTeams.team_id).add_columns(Teams.id, Teams.name).filter(Teams.sport_id==sport_id).filter(MembersTeams.member_id==member.id).all()
                for member_team in member_teams:
                    cols = SportsColumns.query.join(SportsColumnsTeams, SportsColumns.id==SportsColumnsTeams.column_id).add_columns(SportsColumns.id, SportsColumns.name).filter(SportsColumnsTeams.team_id==member_team.id).all()
                    for col in cols:
                        c = col.name
                    if c in d:
                        c = 'E2'
                    d[c] = (member_team.name, feed[member_team.name])
                    d['total'] += feed[member_team.name]
                key = str(d['total']) + '_' + str(member.name)
                members[key] = d
        else:
            return {'message': 'No Members Available'}

        out = []
        for key in sorted(members, reverse=True):
            out.append(members[key])
        return out

    def build(self, feed, build_type, sport_id):
        if build_type == 'html':
            members = self.member(feed, 'all', sport_id)
        return {'members': members}

    def get(self, sport_name, api_name, feed=None, member_id=None):
        self.api_name = api_name
        if sport_name == 'nhl':
            self.sport_id = 1
        else:
            self.sport_id = 2

        if self.api_name == 'members':
            return self.members(self.sport_id)
        elif self.api_name == 'member':
            return self.member(feed, member_id, self.sport_id)
        elif self.api_name == 'feed':
            return {"Chicago Blackhawks": 25, "Philadelphia Flyers": 22, "Buffalo Sabres": 16, "Arizona Coyotes": 15, "Nashville Predators": 31, "Toronto Maple Leafs": 31, "Carolina Hurricanes": 24, "Boston Bruins": 24, "Pittsburgh Penguins": 27, "New York Rangers": 28, "San Jose Sharks": 26, "Edmonton Oilers": 20, "Minnesota Wild": 25, "Washington Capitals": 29, "Dallas Stars": 25, "Vancouver Canucks": 26, "Columbus Blue Jackets": 31, "New York Islanders": 30, "Tampa Bay Lightning": 34, "Calgary Flames": 27, "Los Angeles Kings": 29, "Montreal Canadiens": 21, "Detroit Red Wings": 25, "Ottawa Senators": 22, "New Jersey Devils": 32, "Florida Panthers": 18, "Anaheim Ducks": 24, "Vegas Golden Knights": 31, "Winnipeg Jets": 31, "St. Louis Blues": 35, "Colorado Avalanche": 24}
            #return self.feed(self.sport_id)


class NHL_Member(Resource):
    def get(self, member_id=None):
        nhl = NHL()
        feed = nhl.feed(1)
        member = nhl.member(feed, member_id, 1)
        return {'member_id': member_id, 'member': member}


class NHL_Build(Resource):
    def get(self, build_type):
        nhl = NHL()
        feed = nhl.feed(1)
        parse = nhl.parse(1, feed)
        build = nhl.build(parse, build_type, 1)
        return build


class NBA_Member(Resource):
    def get(self, member_id=None):
        nhl = NHL()
        feed = nhl.feed(2)
        member = nhl.member(feed, member_id, 2)
        return {'member_id': member_id, 'member': member}


class NBA_Build(Resource):
    def get(self, build_type):
        nba = NHL()
        feed = nba.feed(2)
        parse = nba.parse(2, feed)
        build = nba.build(parse, build_type, 2)
        return build


api.add_resource(NHL, '/nhl/<api_name>')

api.add_resource(NHL_Member, '/nhl/member/<member_id>')
api.add_resource(NHL_Build, '/nhl/build/<build_type>')

api.add_resource(NBA_Member, '/nba/member/<member_id>')
api.add_resource(NBA_Build, '/nba/build/<build_type>')

if __name__ == '__main__':
    # initialize the log handler
    logHandler = RotatingFileHandler('info.log', maxBytes=1000, backupCount=1)
    
    # set the log handler level
    logHandler.setLevel(logging.INFO)

    # set the app logger level
    app.logger.setLevel(logging.INFO)

    app.logger.addHandler(logHandler)
    app.run()


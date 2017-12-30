from _ckrits import Secrets
from flask import Flask, request, abort, jsonify, session
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from models import Members, Teams, MembersTeams, SportsColumns, SportsColumnsTeams, ApiUsers
from sqlalchemy import create_engine
from raven.contrib.flask import Sentry

import hashlib
import os
import requests
import simplejson as json
import sys
import unicodedata

# FLASK APP
app = Flask(__name__)
secret = Secrets()
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = secret.secret()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pools.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# START Flask_RESTFul API
api = Api(app)

# DB 
db_connect = create_engine('sqlite:///pools.db')
db = SQLAlchemy(app)

# START SESSION
session = requests.Session()
session.headers['Content-Type'] = 'application/json'

# SENTRY
sentry = Sentry(app, dsn='https://4491bf3c14aa4248be7166bdc0848383:1376151220554a1ea2eae341502ad1ba@sentry.io/260429')

# STREAK DICT
streak = {}


# AUTHORIZE AND MAKE, SEND & STORE TOKEN
class API_Auth(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type=str, required=True, help='API Key is required')
        super(API_Auth, self).__init__()

    def post(self):
        ''' 
           ONLY POST TO LOGIN FIRST TO GAIN TOKEN - SEND TO REQUESTOR
           TOKEN IS TO BE CHECKED WITH EACH REQUEST IN THE API ROUTES
        '''
        args = self.reqparse.parse_args()
        # CHECK THE USER
        u = self.check_user(args['key'])
        if u:
            # MAKE THE TOKEN
            t = self.make_token(800, args['key'])
            # ADD FURTHER HASHED TOKEN TO SESSION
            s = hashlib.sha224(str(t).encode('utf-8') + str(args['key']).encode('utf-8') + str(app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
            session.auth = s
            return t
        else:
            return {'message': 'You must have an API account.'}

    def check_user(self, k):
        ''' 
           CHECK IF API KEY IS REGISTERED IN DB - FOR NOW JUST CHECK FOR THE KEY 
        '''
        a = ApiUsers.query.filter(ApiUsers.key==k).first()
        print(a)
        if a:
            return True
        return False

    def make_token(self, expiration=800, key=1234):
        ''' 
           MAKE A TOKEN 
        '''
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        t = hashlib.sha224(str(s.dumps({'key':key})).encode('utf-8')).hexdigest()
        return t

    def check_token(self, key, token):
        ''' 
           CHECK THE TOKEN 
        '''
        args = self.reqparse.parse_args()
        c = hashlib.sha224(str(token).encode('utf-8') + str(key).encode('utf-8') + str(app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        if c == session.auth:
            return True
        return False


def authenticate(key, token):
    a = API_Auth()
    c = a.check_token(key, token)
    if c:
        return True
    else:
        return {'message': 'You must login. Please obtain an API Key from drewsoske.com if you need one.'}


class Feeds:
    def get(self, sport_id):
        d = {'message': 'No Results'}
        if sport_id == 1:
            url = "http://statsapi.web.nhl.com/api/v1/standings?season=20172018"
            r = requests.get(url)
            d = json.loads(r.text.encode('utf-8'))
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
                    streak[name] = team['streak']['streakCode']
                    seeder.append(name)
        elif sport_id == 2:
            for team in feed['standing']:
                if sys.version_info.major >= 3:
                    n = str(team['first_name']) + ' ' + str(team['last_name'])
                else:
                    n = unicode(team['first_name']) + ' ' + unicode(team['last_name'])
                name = t.strip_accents(n)
                output[name] = team['won']
                streak[name] = team['streak']
                seeder.append(name)
        if seed:
            return seeder
        return output


class Utility:
    def strip_accents(self, s):
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
   
    def html_builder(self, sport_id, data):
        rows, template = str(''), """<html><head><title>%s</title></head><body>%s</body></html>"""
        title = 'NHL Pools' if sport_id == 1 else 'NBA Pools'
        table = """<table class='poolresults'><tr>%s</tr>%s</table>"""
        labels = """<th></th><th>Total</th><th>A</th><th>B</th><th>C</th><th>D</th><th colspan='2'>E</th>"""
        for row in data:
            t = """<tr>
                       <th>%s</th>
                       <th>%s</th>
                       <td><h3>%s</h3><p>%s (%s)</p></td>
                       <td><h3>%s</h3><p>%s (%s)</p></td>
                       <td><h3>%s</h3><p>%s (%s)</p></td>
                       <td><h3>%s</h3><p>%s (%s)</p></td>
                       <td><h3>%s</h3><p>%s (%s)</p></td>
                       <td><h3>%s</h3><p>%s (%s)</p></td>
                   </tr>"""
            a, b, c, d, e, e2 = row.get('A'), row.get('B'), row.get('C'), row.get('D'), row.get('E'), row.get('E2')
            p = t % (row['name'], row['total'], a[1], a[0], streak[a[0]], b[1], b[0], streak[b[0]], c[1], c[0], streak[c[0]], d[1], d[0], streak[d[0]], e[1], e[0], streak[e[0]], e2[1], e2[0], streak[e2[0]],)
            rows = rows + p
        body = table % (labels, rows)
        html = template % (title, body)
        return html


class API(Resource):
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
            db_members_result = Members.query.get(member_id)
            db_members = []
            db_members.append(db_members_result)
            #db_members = db_members_result.serialize()

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
                    if sport_id == 1:
                        d[c] = (member_team.name, feed[member_team.name], streak[member_team.name])
                        d['total'] += feed[member_team.name]
                    elif sport_id == 2:
                        d[c] = (member_team.name, feed[member_team.name], streak[member_team.name])
                        d['total'] += feed[member_team.name]
                key = str(d['total']) + '_' + str(member.name)
                members[key] = d
        else:
            return {'message': 'No Members Available'}

        out = []
        for key in sorted(members, reverse=True):
            out.append(members[key])
        return out

    def build(self, member_id, feed, build_type, sport_id):
        if build_type == 'json':
            m = self.member(feed, member_id, sport_id)
            return {'members': m}
        elif build_type == 'html':
            o = self.member(feed, member_id, sport_id)
            u = Utility()
            h = u.html_builder(sport_id, o)
            print(h)
            return h

    def get(self, api_name, feed=None, member_id=None):
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
            return self.feed(self.sport_id)


class Pools_Member(Resource):
    ''' GET | POST A MEMBER PROFILE '''
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type = str)        
        self.reqparse.add_argument('token', type = str)
        self.reqparse.add_argument('name', type = str)
        self.reqparse.add_argument('email', type = str)
        self.reqparse.add_argument('sport_id', type = int)
        super(Pools_Member, self).__init__()

    def get(self, pool, member_id=None):
        args = self.reqparse.parse_args()
        a = authenticate(args['key'], args['token'])
        if a is True:
            member = Members.query.get(member_id)
            return member.serialize()
        else:
            return a

    def post(self, pool, member_id=None, **kwargs): 
        args = self.reqparse.parse_args()
        a = authenticate(args['key'], args['token'])
        if a is True:
            if member_id != 'new':
                mb = Members.query.filter_by(id=member_id).update(args)
                mb = Members.query.filter_by(id=member_id).first()
                member = mb.serialize()
            else:
                nw = Members(args['email'], args['name'], args['sport_id'])
                db.session.add(nw)
                db.session.commit()
                member = nw.serialize()
            return member
        else:
            return a


class Pools_MemberTeam(Resource):
    ''' GET | POST A MEMBERS TEAMS CHOICES '''
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type = str)        
        self.reqparse.add_argument('token', type = str)
        self.reqparse.add_argument('A', type = int)        
        self.reqparse.add_argument('B', type = int)
        self.reqparse.add_argument('C', type = int)
        self.reqparse.add_argument('D', type = int)
        self.reqparse.add_argument('E1', type = int)
        self.reqparse.add_argument('E2', type = int)
        super(Pools_MemberTeam, self).__init__()

    def get(self, pool, member_id=None):
        args = self.reqparse.parse_args()
        a = authenticate(args['key'], args['token'])
        if a is True:
            output = {}
            output[member_id], memberteams = {}, MembersTeams.query.filter_by(member_id=member_id).all()
            for memberteam in memberteams:
                mt = memberteam.serialize()
                print(mt)
                cm = SportsColumns.query.get(mt['column_id'])
                tm = Teams.query.get(mt['team_id'])
                ts, cs = tm.serialize(), cm.serialize()
                keyname = cs['name'] if cs['name'] not in output[member_id] else 'E2' 
                output[member_id][keyname] = ts['name']
            return output
        else:
            return a

    def post(self, pool, member_id):
        args = self.reqparse.parse_args()
        a = authenticate(args['key'], args['token'])
        if a is True:
            alist = ['E1','E2']
            for arg in args:
                argname = 'E' if arg in alist else arg
                sct = SportsColumns.query.filter_by(sport_id=1, name=argname).first()
                scr = sct.serialize()
                mt = MembersTeams(member_id, scr['id'], args[arg])
                db.session.add(mt)
                db.session.commit()
        else:
            return a


class Pools_Build(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('key', type = str)        
        self.reqparse.add_argument('token', type = str)
        super(Pools_Build, self).__init__()

    ''' GET BUILD '''
    def get(self, pool, build_type, member_id='all'):
        args = self.reqparse.parse_args()
        a = authenticate(args['key'], args['token'])
        if a is True:
            nhl = API()
            sport_id = 1 if pool == 'nhl' else 2
            feed = nhl.feed(sport_id)
            parse = nhl.parse(sport_id, feed)
            build = nhl.build(member_id, parse, build_type, sport_id)
            return build
        else:
            return a


# API AUTH ROUTE
api.add_resource(API_Auth, '/api/auth')

# API ROUTES
api.add_resource(API, '/apiname/<api_name>')
api.add_resource(Pools_Member, '/<pool>/member/<member_id>', endpoint='poolmember')
api.add_resource(Pools_MemberTeam, '/<pool>/memberteam/<member_id>', endpoint='poolmemberteams')
api.add_resource(Pools_Build, '/<pool>/build/<build_type>/<member_id>', endpoint='poolbuild')


if __name__ == '__main__':
    app.run(host='0.0.0.0')


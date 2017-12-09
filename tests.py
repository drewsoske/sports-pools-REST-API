#!vapi/bin/python
import os
import unittest

from app import app
from api import Feeds, Parser
from sqlalchemy import create_engine


class FeedsTests(unittest.TestCase):
    db_connect = create_engine('sqlite:///pools.db')

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
             
    def tearDown(self):
        pass
    
    # DATABASE TESTS
    def test_db_connection(self):
        self.assertTrue(self.db_connect)

    def test_db_nhl_teams(self):
        conn = self.db_connect.connect()
        test_teams = conn.execute("SELECT id, name FROM teams WHERE sport_id = ? ORDER BY name LIMIT 0,1", (1,))
        self.assertIsNotNone(test_teams)

    def test_db_nba_teams(self):
        conn = self.db_connect.connect()
        test_teams = conn.execute("SELECT id, name FROM teams WHERE sport_id = ? ORDER BY name LIMIT 0,1", (2,))
        self.assertIsNotNone(test_teams)

    def test_db_nhl_members(self):
        conn = self.db_connect.connect()
        test_members = conn.execute("SELECT id, name FROM members WHERE sport_id = ? ORDER BY name LIMIT 0,1", (1,))
        self.assertIsNotNone(test_members)

    def test_db_nba_members(self):
        conn = self.db_connect.connect()
        test_members = conn.execute("SELECT id, name FROM members WHERE sport_id = ? ORDER BY name LIMIT 0,1", (2,))
        self.assertIsNotNone(test_members)

    # API TESTS
    def test_nhl_url(self):
        response = self.app.get('/nhl/build/html', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_nba_url(self):
        response = self.app.get('/nba/build/html', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_nhl_feed_response(self):
        nhl = Feeds()
        test_response = nhl.get(1)
        self.assertTrue(bool(test_response['records']))

    def test_nba_feed_response(self):
        nba = Feeds()
        test_response = nba.get(2)
        self.assertTrue(bool(test_response['standing']))

    def test_nhl_parser_response(self):
        nhl_feed = Feeds()
        feed = nhl_feed.get(1)
        nhl_parsed = Parser()
        test_response = nhl_parsed.get(1, feed)
        self.assertTrue(bool(test_response['Pittsburgh Penguins']))

    def test_nba_parser_response(self):
        nba_feed = Feeds()
        feed = nba_feed.get(2)
        nba_parsed = Parser()
        test_response = nba_parsed.get(2, feed)
        self.assertTrue(bool(test_response['Boston Celtics']))


if __name__ == "__main__":
    unittest.main()


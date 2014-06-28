#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2
import json
import random
import cgi
import urllib2
from gaesessions import get_current_session
from pprint import pprint

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"))

class MainMenu(webapp2.RequestHandler):
    # Handler for the main menu.
    def get(self):
        session = get_current_session()
        session.clear()
        template = jinja_environment.get_template('mainmenu.html')
        self.response.out.write(template.render())

class Game(webapp2.RequestHandler):
    # Handler for game page

    def get(self):
        session = get_current_session()
        randomno = random.randint(0,4)
        words = ["love", "sad", "happy", "pity", "lazy"]
        chosen = words[randomno]
        session["chosen"] = chosen
        acceptedWords = session.get('acceptedWords', '')
        rejectedWords = session.get('rejectedWords', '')
        userTry = cgi.escape(session.get('userTry', ''), quote = True)
        tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords}
        template = jinja_environment.get_template('gamepage.html')
        self.response.out.write(template.render(tpl_vars)) 

    def post(self):
        userTry = self.request.get('userTry')
        session = get_current_session()
        acceptedWords = session.get('acceptedWords', '')
        rejectedWords = session.get('rejectedWords', '')
        chosen = session["chosen"]
        req = urllib2.Request('http://words.bighugelabs.com/api/2/c743707f91611556e614e4db7b1ba302/%s/json' % chosen)
        response = urllib2.urlopen(req)
        json_result = response.read()
        data = json.loads(json_result)
        listsyn = []
        if "noun" in data:
            listsyn.append(data["noun"]["syn"])
        if "verb" in data:
            listsyn.append(data["verb"]["syn"])
        if "adjective" in data:
            listsyn.append(data["adjective"]["syn"])
        if "adverb" in data:
            listsyn.append(data["adverb"]["syn"])
        if "pronoun" in data:
            listsyn.append(data["pronoun"]["syn"])
        if userTry in listsyn[0]:
            if acceptedWords == '':
                acceptedWords = userTry
            else:
                acceptedWords = acceptedWords + ', ' + userTry
        else:
            if rejectedWords == '':
                rejectedWords = userTry
            else:
                rejectedWords = rejectedWords + ', ' + userTry
        session["rejectedWords"] = rejectedWords
        session["acceptedWords"] = acceptedWords
        tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords}
        template = jinja_environment.get_template('gamepage.html')
        self.response.out.write(template.render(tpl_vars))

class Help(webapp2.RequestHandler):
    # Handler for help page
    def get(self):
        template = jinja_environment.get_template('helppage.html')
        self.response.out.write(template.render())

class LeaderBoard(webapp2.RequestHandler):
    # Handler for leaderboard page
    def get(self):
        self.response.write()

app = webapp2.WSGIApplication([
    ('/', MainMenu),
    ('/game', Game),
    ('/help', Help),
    ('/leaderboard', LeaderBoard)
], debug=True)

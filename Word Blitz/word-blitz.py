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
import itertools
import time
import Cookie
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
        session = get_current_session() #setting up session and getting current session
        wordCount = session.get('wordCount', 1) #gets current wordcounter and sets initial word counter set to 1
        level = session.get('level', 1) #gets current level and sets initial level set to 1
        reqSyn = session.get('reqSyn', 1) #required number of synonyms to pass the current level
        #------------------------importing wordlist and choosing random word from list-------------------------------
        json_wordlist = open("wordlist.json")
        unparsed_wordlist = json.load(json_wordlist)
        wordlist = unparsed_wordlist["wordlist"]
        session["wordlist"] = wordlist
        chosen = wordlist[random.randint(0, len(wordlist) - 1)]
        session["chosen"] = chosen
        #----------------------------------end of importing and word choice------------------------------
        acceptedWords = session.get('acceptedWords', '')
        rejectedWords = session.get('rejectedWords', '')

        rWL = []
        jsonrWL = json.dumps(rWL)
        session["jsonrWL"] = jsonrWL

        aWL = []
        jsonaWL = json.dumps(aWL)
        session["jsonaWL"] = jsonaWL

        userTry = cgi.escape(session.get('userTry', ''), quote = True)
        tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords, "wordCounter": wordCount, "level": level, "synLeft": reqSyn}
        template = jinja_environment.get_template('gamepage.html')
        self.response.out.write(template.render(tpl_vars)) 

    def post(self):
        session = get_current_session()

        userTry = (self.request.get('userTry')).lower() #obtains and stores user input in variable
        synLeft = session.get('synLeft', 1) #no. of synonyms remaining for level
        reqSyn = session.get('reqSyn', 1) #no. of synonyms req for levels in current level tier
        wordCount = session.get('wordCount', 1) #no. of words needed to be cleared to progress to next level
        wordCounter = session.get('wordCounter', 1) #how many more words to be cleared to progress
        level = session.get('level', 1)
        wordlist = session["wordlist"]

        acceptedWords = session.get('acceptedWords', '')
        rejectedWords = session.get('rejectedWords', '')

        jsonrWL = session["jsonrWL"]
        rWL = json.loads(jsonrWL)

        jsonaWL = session["jsonaWL"]
        aWL = json.loads(jsonaWL)

        chosen = session["chosen"]
        req = urllib2.Request('http://words.bighugelabs.com/api/2/c743707f91611556e614e4db7b1ba302/%s/json' % chosen)
        response = urllib2.urlopen(req)
        json_result = response.read()
        data = json.loads(json_result)
        listsyn = []

        #compiling all the synonyms into a list based on request to thesaurus
        if "noun" in data:
            if "syn" in data["noun"]:
                listsyn.append(data["noun"]["syn"])
            if "rel" in data["noun"]:
                listsyn.append(data["noun"]["rel"])
            if "sim" in data["noun"]:
                listsyn.append(data["noun"]["sim"])
        if "verb" in data:
            if "syn" in data["verb"]:
                listsyn.append(data["verb"]["syn"])
            if "rel" in data["verb"]:
                listsyn.append(data["verb"]["rel"])
            if "sim" in data["verb"]:
                listsyn.append(data["verb"]["sim"])
        if "adjective" in data:
            if "syn" in data["adjective"]:
                listsyn.append(data["adjective"]["syn"])
            if "rel" in data["adjective"]:
                listsyn.append(data["adjective"]["rel"])
            if "sim" in data["adjective"]:
                listsyn.append(data["adjective"]["sim"])    
        if "adverb" in data:
            if "syn" in data["adverb"]:
                listsyn.append(data["adverb"]["syn"])
            if "rel" in data["adverb"]:
                listsyn.append(data["adverb"]["rel"])
            if "sim" in data["adverb"]:
                listsyn.append(data["adverb"]["sim"])
        if "pronoun" in data:
            if "syn" in data["pronoun"]:
                listsyn.append(data["pronoun"]["syn"])
            if "rel" in data["pronoun"]:
                listsyn.append(data["pronoun"]["rel"])
            if "sim" in data["pronoun"]:
                listsyn.append(data["pronoun"]["sim"])
        syn_list = list(itertools.chain.from_iterable(listsyn))
        #end of compilation

        if userTry in rWL or userTry in aWL:
            warning = "You've entered this word before! Please enter a different one."
            tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords, "wordCounter": wordCounter, "level": level, "synLeft": synLeft, "warning": warning}
            template = jinja_environment.get_template('gamepage.html')
            self.response.out.write(template.render(tpl_vars))
        elif userTry == chosen:
            warning = "Isn't that the same word as the current one? Try something else!"
            tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords, "wordCounter": wordCounter, "level": level, "synLeft": synLeft, "warning": warning}
            template = jinja_environment.get_template('gamepage.html')
            self.response.out.write(template.render(tpl_vars))            
        else:
            if userTry in syn_list: #user entered correct synonym
                synLeft -= 1 
                if synLeft < 1: #user cleared req synonyms for the word
                    wordCounter -= 1
                    if wordCounter < 1: #user cleared req number of words for level
                        if level % 5 == 0: #increase in level tier
                            reqSyn += 1
                            wordCount = 1
                            wordCounter = wordCount
                            synLeft = reqSyn
                            session['reqSyn'] = reqSyn
                            session['synLeft'] = reqSyn
                            session['wordCount'] = wordCount
                            session['wordCounter'] = wordCount
                        else: #increase in level within tier
                            wordCount += 1
                            wordCounter = wordCount
                            synLeft = reqSyn
                            session['wordCount'] = wordCount
                            session['wordCounter'] = wordCounter
                            session['synLeft'] = reqSyn
                        level += 1 #increase level
                        warning = 'Level up! Keep going! :D'
                    else:
                        synLeft = reqSyn
                        session['synLeft'] = synLeft
                        session['wordCounter'] = wordCounter
                        if wordCounter == 1:
                            warning = 'Correct! ' + str(wordCounter) + " more word to next level!"
                        else:
                            warning = 'Correct! ' + str(wordCounter) + " more words to next level!"
                    chosen = wordlist[random.randint(0,len(wordlist)- 1)]
                    acceptedWords = ''
                    rejectedWords = ''
                    aWL = []
                    rWL = []
                    jsonaWL = json.dumps(aWL)
                    jsonrWL = json.dumps(rWL)
                    session["jsonaWL"] = jsonaWL
                    session["jsonrWL"] = jsonrWL
                    session["chosen"] = chosen
                    session["rejectedWords"] = rejectedWords
                    session["acceptedWords"] = acceptedWords
                    session["wordCounter"] = wordCounter
                    session["level"] = level
                    tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords, "wordCounter": wordCounter, "level": level, "synLeft": synLeft, "warning": warning}
                    template = jinja_environment.get_template('gamepage.html')
                    self.response.out.write(template.render(tpl_vars)) 
                else:
                    session['synLeft'] = synLeft
                    if acceptedWords == '':
                        acceptedWords = userTry
                        aWL = [userTry]
                    else:
                        acceptedWords = acceptedWords + ', ' + userTry
                        aWL.append(userTry)
                    if synLeft == 1:
                        warning = "1 more synonym to next word!"
                    else:
                        warning = str(synLeft) + " more synonyms to next word!"
                    jsonaWL = json.dumps(aWL)
                    session["jsonaWL"] = jsonaWL
                    session["acceptedWords"] = acceptedWords
                    tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords, "wordCounter": wordCounter, "level": level, "synLeft": synLeft, "warning": warning}
                    template = jinja_environment.get_template('gamepage.html')
                    self.response.out.write(template.render(tpl_vars)) 
            else: #user entered invalid synonym
                if rejectedWords == '':
                    rejectedWords = userTry
                    rWL = [userTry]
                else:
                    rejectedWords = rejectedWords + ', ' + userTry
                    rWL.append(userTry)
                session["rejectedWords"] = rejectedWords
                warning = "Invalid synonym, try again!"
                jsonrWL = json.dumps(rWL)
                session["jsonrWL"] = jsonrWL
                session["synLeft"] = synLeft
                session["acceptedWords"] = acceptedWords
                tpl_vars = {"chosen": chosen, "userTry": userTry, "acceptedWords": acceptedWords, "rejectedWords": rejectedWords, "wordCounter": wordCounter, "level": level, "synLeft": synLeft, "warning": warning}
                template = jinja_environment.get_template('gamepage.html')
                self.response.out.write(template.render(tpl_vars))

class Help(webapp2.RequestHandler):
    # Handler for help page
    def get(self):
        template = jinja_environment.get_template('helppage.html')
        self.response.out.write(template.render())

class LeaderBoard(webapp2.RequestHandler):
    # Handler for leaderboard page accessed through game
    def get(self):
        playerName = self.request.get("playerName")
        session = get_current_session()
        playerLevel = session.get('level', 1)
        tpl_vars = { "playerName" : playerName, "playerLevel" : playerLevel}
        template = jinja_environment.get_template('leaderboard.html')
        self.response.out.write(template.render(tpl_vars))

class LeaderBoards(webapp2.RequestHandler):
    # Handler for leaderboard page accessed through main menu
    def get(self):
        template = jinja_environment.get_template('leaderboards.html')
        self.response.out.write(template.render())

app = webapp2.WSGIApplication([
    ('/', MainMenu),
    ('/game', Game),
    ('/help', Help),
    ('/leaderboard', LeaderBoard),
    ('/leaderboards', LeaderBoards)
], debug=True)

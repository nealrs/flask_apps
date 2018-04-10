#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import random
import os
from flask import Flask, request, session, redirect, render_template, Response, make_response, jsonify, url_for, Markup
from flask_cors import CORS, cross_origin
from flask_basicauth import BasicAuth
from flask_ask import (
    Ask,
    request as ask_request,
    session as ask_session,
    context as ask_context,
    version as ask_version, 
    question, statement, audio, current_stream
)
from flask_sslify import SSLify
import redis
import json
import pytz
from datetime import datetime
import uuid
from bs4 import BeautifulSoup
import argparse

from urlparse import urlparse
import urllib

import re
import collections

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
from raven.contrib.flask import Sentry
from flask_compress import Compress

app = Flask(__name__)
sslify = SSLify(app)
Compress(app)

# set basic auth
app.config['BASIC_AUTH_USERNAME'] = os.environ['BAU']
app.config['BASIC_AUTH_PASSWORD'] = os.environ['BAP']
basic_auth = BasicAuth(app)

app.config.update(
    DEBUG=os.environ['DEBUG'],
    SECRET_KEY=os.environ['S3KR1T'],
    PREFERRED_URL_SCHEME = 'https'
)

if os.environ['DEBUG'] is False:
    app.config.update(
        SERVER_NAME = 'baelife.nealshyam.com'
    )
# setup sentry error reporting
sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])

# cache buster?
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


#### APP & ROUTES
@app.errorhandler(404)
def page_not_found_404(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found_500(e):
    return render_template('500.html'), 500

#### MAIN INDEX ROUTE ###
@app.route('/', )
@app.route("/", methods=["GET"])
def home():
    return redirect("https://nealshyam.com")

###### NEWS APP ######
@app.route('/news/', defaults={'source': None})
@app.route("/news/<path:source>", methods=["GET"])
def news(source):
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    feedmain = json.loads(redisdb.get("news"))

    if source is None or source == "":
        feed = feedmain
    else:
        feed = feedmain[source]
    
    if feed:
        r = jsonify(feed)
        r.mimetype = 'application/json'
        return r, 200
    else:
        return make_response("NEWS Feed Error", 400)


###### MTA APP ######
@app.route('/mta/', defaults={'source': None})
@app.route("/mta/<path:source>/", methods=["GET"])
def mta(source):
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    feedmain = json.loads(redisdb.get("mta"))

    if source is None or source == "":
        return render_template('mta.html')
    else:
        try: 
            feed = feedmain[source.decode('utf-8')]
            if feed:
                return make_response(feed, 200)
            else:
                return make_response("MTA Feed Error", 404)
        except KeyError as e:
            return make_response("MTA Feed Error", 404)


@app.route('/subway/', defaults={'line': None})
@app.route("/subway/<path:line>/", methods=["GET"])
def subway(line):
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    feedmain = json.loads(redisdb.get("subwayLines"))

    if line is None or line == "":
        return render_template('mta.html')
    else:
        try: 
            feed = feedmain[line.upper()]
            if feed:
                return make_response(feed, 200)
            else:
                return make_response("MTA Feed Error", 404)
        except KeyError as e:
            return make_response("MTA Feed Error", 404)

@app.route('/nyc/')
@app.route("/nyc/", methods=["GET"])
def nyc():
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    feedmain = json.loads(redisdb.get("subwayLines"))
    lines = [
        "ace",
        "bdfm",
        "g",
        "l",
        "nqrw",
        "jz",
        "123",
        "456",
        "7",
        "sir", 
        "s"
    ]
    resp = ""
    for l in lines:
        feed = feedmain[l.upper()]
        print feed
        print l
        resp = resp + (json.loads(feed))['titleText'].replace(" SUBWAY ", " ") + "\n"
    return make_response(resp, 200)


###### CURRENT TIME APP ######
def dates(tzp):
    if tzp == "ET":
        tz = pytz.timezone('America/New_York')
        tzn = "Eastern"
    elif tzp == "CT":
        tz = pytz.timezone('America/Chicago')
        tzn = "Central"
    elif tzp == "MT":
        tz = pytz.timezone('America/Denver')
        tzn = "Mountain"
    elif tzp == "PT":
        tz = pytz.timezone('America/Los_Angeles')
        tzn = "Pacific"
    else:
        tz = pytz.timezone('America/New_York')
        tzn = "Eastern"

    today = datetime.now(tz)
    today_utc = today.astimezone(pytz.UTC)

    if today.minute > 0:
        locale = today.strftime('%-I:%M %p')
    else:
        locale = locale = today.strftime('%-I %p')

    #logging.debug( today )
    #logging.debug( locale )
    #logging.debug( today_utc )
    return today, today_utc, locale, tzn


@app.route('/time/', defaults={'tz': 'ET'})
@app.route("/time/<path:tz>/", methods=["GET"])
def time(tz):
    if tz is None or tz == "":
        tz = "ET"
    else:
        date, utc, locale, tzn = dates(tz.upper())
    	feed = {}
    	feed['uid'] = str(uuid.uuid4())
    	feed['updateDate'] = utc.strftime('%Y-%m-%dT%H:%M:%S.0Z')
    	feed['mainText'] = "It's "+ locale
    	feed['titleText'] = feed['mainText'] + " "+ tzn + " Time"
    	feed_json = json.dumps(feed)
    	#logging.debug(feed_json)
    	return feed_json, 200


###### HACKATHON LIST APP ######
@app.route('/hackathons/', defaults={'mo': None})
@app.route("/hackathons/<path:mo>", methods=["GET"])
def hackathons(mo):
    months = [mo[i:i+3] for i in range(0, len(mo), 3)]
    # SCRAPE Hackathons from pages 1-10
    api = "https://devpost.com/hackathons?utf8=%E2%9C%93&search=&challenge_type=in-person&sort_by=Submission+Deadline&page="
    req_html = ""
    html = "<ul>\n"

    for i in range(1,11):
        req = requests.get( api+str(i) )
        req_html = req_html + req.text
        
    soup = BeautifulSoup(req_html, 'html.parser')
    rows = soup.find_all("article", class_="challenge-listing")

    # EXTRACT data from each row and add to hackathons list
    for i, r in enumerate(rows):
        name = r.find_all('h2')[0].text.strip()

        if any(month in r.find_all("span", class_="value date-range")[0].text.strip().lower() for month in months):
            dates = r.find_all("span", class_="value date-range")[0].text.strip()
        else:
            continue # just skip out of loop if no date

        url = (r.find_all('a', class_="clearfix", href=True)[0]['href']).strip().replace("/?ref_content=featured&ref_feature=challenge&ref_medium=discover", "").replace("/?ref_content=default&ref_feature=challenge&ref_medium=discover", "")

        if r.find_all("p", class_="challenge-location"):
            location = r.find_all("p", class_="challenge-location")[0].text.strip().replace(", US", "")
        else:
            location = ""

        hack = {
            "name" : name,
            "url" : url,
            "dates" : dates,
            "location" : location
            }

        html = html + "  <li><a href=\""+url+"\">"+name+"</a>, "+location+"</li>\n"

    html = html + "</ul>"
    return html, 200



###### DEBUG NEWS/TIME/SUBWAY APP ######
@app.route('/debug/')
@app.route("/debug/", methods=["GET"])
def debugme():
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    keys = redisdb.keys()
    data = {}
    try:
        for k in keys:
            if any(sub in k for sub in ["baelife_metrics", "_events", "_places", "feed", "newmovies", "topmovies", "neal", "recipies"]):
                pass 
            else:
                print k
                try:
                    feed = json.loads(redisdb.get(k))
                except ValueError as e:
                    feed = redisdb.get(k)
                print feed
                data[k] = feed

        #print data
        return jsonify(data), 200
    except KeyError as e:
        return make_response("REDIS Error", 404)


if __name__ == "__main__":
    if os.environ['DEBUG'] is True:
        from OpenSSL import SSL
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file('key.pem')
        context.use_certificate_file('cert.pem')
        app.run(ssl_context=context)
    else:
        app.run()
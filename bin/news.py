#!/usr/bin/env python
import requests
from datetime import datetime
import pytz
import os
import json
from ph_py import ProductHuntClient
import random
import feedparser
from lxml import html
import redis
from urlparse import urlparse
import re

# establish current date in PT timezone
def getTime():
    tz = pytz.timezone(os.environ['TZ'])
    today = datetime.now(tz)
    today_utc = today.astimezone(pytz.UTC)
    return today_utc


def comments(x):
    if x == 1:
        return str(x) + " comment: "
    else:
        return str(x) + " comments: "


def getHN(num=5):
    APIbase = "https://hacker-news.firebaseio.com/v0/"
    APItop = APIbase+"topstories.json"
    topReq = requests.get(APItop)
    topStories = topReq.json()
    #print topStories
    hn = []

    for s in topStories[:int(num)]:
        #print s
        APIstory = APIbase +"item/"+ str(s) +".json"
        r = requests.get(APIstory)
        d = r.json()
        story = {}
        #print d

        story["uid"] = s
        story["updateDate"] = getTime().strftime('%Y-%m-%dT%H:%M:%S.0Z')
        story["titleText"] = "From HN: "+ d['title'].encode('utf-8')
        story["commentURL"] = "https://news.ycombinator.com/item?id="+ str(s)
        story["title"] = d['title'].encode('utf-8')
        story["thumbnail"]="http://i.imgur.com/iNheuJ7.png"

        if 'descendants' in d:
            story["mainText"] = "With "+ str(d['score']) +" points and "+ comments(d['descendants']) + d['title'].encode('utf-8')
        else:
            story["mainText"] = "With "+ str(d['score']) +" points: "+ d['title'].encode('utf-8')

        #print story["uid"]
        if 'url' in d:
            story["redirectionUrl"] = d['url']
        else:
            story["redirectionUrl"] = story["commentURL"]

        hn.append(story)

    return hn


def getPH(num=5):
    phc = ProductHuntClient(os.environ['PHC'], os.environ['PHS'], "http://localhost:5000")
    # Example request
    ph = []
    for s in phc.get_todays_posts()[:int(num)]:
        story = {}
        story["uid"] = s.id
        story["updateDate"] = getTime().strftime('%Y-%m-%dT%H:%M:%S.0Z')
        story["titleText"] = "From PH: "+ (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')

        story["title"] = (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')
        story["commentURL"] =s.discussion_url.encode('utf-8')
        story["thumbnail"]="http://i.imgur.com/BOUdyc2.jpg"

        if s.comments_count:
            story["mainText"] = "With "+ str(s.votes_count) +" up votes and "+ comments(s.comments_count) + (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')
        else:
            story["mainText"] = "With "+ str(s.votes_count) +" up votes: " + (s.name).encode('utf-8') + ", " + (s.tagline).encode('utf-8')

        story["redirectionUrl"] = s.redirect_url
        ph.append(story)

    return ph


def getWIB():
    url = "https://warisboring.com/feed/"
    rss = feedparser.parse(url)
    wib = []

    for s in rss['entries']:
        story = {}
        story['title'] = s['title']
        story['commentURL'] = s['link']
        story['thumbnail'] = "http://i.imgur.com/rUk5Tar.png"
        wib.append(story)

    return wib


def getND():
    page = requests.get('http://nextdraft.com/current')
    tree = html.fromstring(page.content)
    nd = []

    links = tree.xpath('//div[@class="blurb-content"]/p/a/@href')
    sentences = tree.xpath('//div[@class="blurb-content"]/p/a/text()')

    for l, s in zip(links, sentences):
        story = {}
        story['title'] = s + ' ({uri.netloc})'.format(uri=urlparse(l)).replace('www.', '')
        story['commentURL'] = l
        story['thumbnail'] = "http://i.imgur.com/Pbcu4DI.png"
        nd.append(story)

    return nd


def getLR():
    url = "https://longreads.com/feed/"
    rss = feedparser.parse(url)
    lr = []

    for s in rss['entries']:
        story = {}
        story['title'] = s['title']
        story['commentURL'] = s['link']
        story['thumbnail'] = "http://i.imgur.com/B50b6Vq.png"
        lr.append(story)

    return lr


def getLF():
    url = "https://longform.org/feed.rss"
    rss = feedparser.parse(url)
    lf = []

    for s in rss['entries']:
        story = {}
        story['title'] = s['title']
        story['commentURL'] = s['link']
        story['thumbnail'] = "http://i.imgur.com/QTSwcg1.png"
        lf.append(story)

    return lf


def getNati():
    url = "http://nautil.us/rss/all"
    rss = feedparser.parse(url)
    nati = []

    for s in rss['entries']:
        story = {}
        story['title'] = re.sub(r"( - .*)", "", s['title'])
        #s['title']. #( - .*)
        story['commentURL'] = s['link']
        story['thumbnail'] = "https://i.imgur.com/XAlUMd1.jpg"
        nati.append(story)

    return nati


def getPubs():
    pubs = []

    pubs.append({
        "title" : "Hacker News",
        "url" : "https://news.ycombinator.com",
        "thumbnail": "http://i.imgur.com/iNheuJ7.png",
        "tagline": "Anything that gratifies one's intellectual curiosity"
    })

    pubs.append({
        "title" : "War is Boring",
        "url" : "https://warisboring.com",
        "thumbnail": "http://i.imgur.com/rUk5Tar.png",
        "tagline": "From drones to AKs, high technology to low politics"
    })

    pubs.append({
        "title" : "Longreads",
        "url" : "https://longreads.com/",
        "thumbnail": "http://i.imgur.com/B50b6Vq.png",
        "tagline": "The best longform stories on the web"
    })

    pubs.append({
        "title" : "NextDraft",
        "url" : "http://nextdraft.com/current",
        "thumbnail": "http://i.imgur.com/Pbcu4DI.png",
        "tagline": "The day's most fascinating news, curataed by Dave Pell"
    })

    pubs.append({
        "title" : "Longform",
        "url" : "http://longform.org",
        "thumbnail": "http://i.imgur.com/QTSwcg1.png",
        "tagline": "New and classic non-fiction from around the web"
    })

    pubs.append({
        "title" : "Product Hunt",
        "url" : "http://producthunt.com",
        "thumbnail": "http://i.imgur.com/BOUdyc2.jpg",
        "tagline": "Discover your next favorite thing"
    })
    

    pubs.append({
        "title" : "Nautilus",
        "url" : "http://nautil.us/",
        "thumbnail": "https://i.imgur.com/XAlUMd1.jpg",
        "tagline": "Science and its endless connections to our lives"
    })

    return pubs



def getNeal():
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    payload = json.loads(redisdb.get("neal"))
    
    #print payload
    if payload is None or payload =="":
        return None
    else:
        return payload


def getAll():
    feed = {}
    feed["stories"] = []
    feed["hn"] = []
    feed["ph"] = []
    feed["wib"] = []
    feed["lr"] = []
    feed["nd"] = []
    feed["lf"] = []
    feed["nati"] = []
    feed["pubs"] = []

    feed["tech"] = []
    feed["world"] = []
    feed["long"] = []
    feed["neal"] = []

    feed["stories"].extend(getHN(20))
    feed["stories"].extend(getWIB())
    feed["stories"].extend(getLR())
    feed["stories"].extend(getND())
    feed["stories"].extend(getLF())
    feed["stories"].extend(getPH(20))
    feed["stories"].extend(getNati())

    feed["hn"].extend(getHN(20))
    feed["ph"].extend(getPH(20))
    feed["wib"].extend(getWIB())
    feed["lr"].extend(getLR())
    feed["nd"].extend(getND())
    feed["lf"].extend(getLF())
    feed["nati"].extend(getNati())
    feed["pubs"].extend(getPubs())

    feed["tech"].extend(getHN(20))
    feed["tech"].extend(getNati())
    feed["tech"].extend(getPH(20))


    feed["world"].extend(getWIB())
    feed["world"].extend(getND())

    feed["long"].extend(getLF())
    feed["long"].extend(getLR())

    feed["neal"].extend(getNeal())

    # CONNECT TO REDIS
    redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
    return redisdb.set("news", str(json.dumps(feed)))
    #print redisdb.get("news")

    
######## Actually, let's rock!!
if __name__ == "__main__":
    print getAll()

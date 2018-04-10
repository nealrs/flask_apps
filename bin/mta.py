#!/usr/bin/env python
# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from bs4 import BeautifulSoup
import requests
from datetime import datetime
from time import gmtime, strftime
import os
import uuid
import pytz
import json
import redis
import lxml
import logging
import re
from HTMLParser import HTMLParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

presignoff = " "

def dates():
	# establish current date in PT timezone
	tz = pytz.timezone('America/New_York')
	today = datetime.now(tz)
	today_utc = today.astimezone(pytz.UTC)
	date = today.strftime("%Y-%m-%d")
	locale = today.strftime("%a, %B %d").lstrip("0").replace(" 0", " ")

	return today_utc, locale


def getFeed(mode):
	try:
		url = "http://tripplanner.mta.info/mobileApps/serviceStatus/serviceStatusPage.aspx?mode="+mode
		headers = {'Accept-Encoding': 'identity'}
		req = requests.get(url, headers=headers)
		return req.text
	except Exception as e:
		logging.debug( "Error retrieving feed" )
		raise
		return False


def getDetailUrl(mode):
	return "http://tripplanner.mta.info/mobileApps/serviceStatus/serviceStatusPage.aspx?mode="+mode


def oxfordComma(items):
    length = len(items)
    if length == 1:
        return items[0]
    if length == 2:
        return '{} and {}'.format(*items)
    else:
		return '{}, and {}'.format(', '.join(items[:-1]), items[-1])

#https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


# GET STATUS
def getSubwayStatus():
	good = []
	detour = []
	change = []
	delay =[]
	work=[]

	good_sentence = ""
	detour_sentence = ""
	change_sentence = ""
	delay_sentence = ""
	work_sentence = ""

	feed = getFeed("subway")
	if feed:
		soup = BeautifulSoup(feed, 'html.parser')
		rows = soup.find_all("tr")

		for r in rows:
			line=""

			imgs = r.find_all("img")
			for i in imgs:
				line = line + (i.get('src'))[-5:-4].upper()
			if imgs == []:
				line = "Staten Island"

			status =  r.select('td')[1].get_text(strip=True)

			if status == "GOOD SERVICE":
				if line == "Staten Island":
					good.append(line)
				else:
					good.extend(line)

			if status == "PLANNED WORK":
				if line == "Staten Island":
					work.append(line)
				else:
					work.extend(line)

			if status == "SERVICE CHANGE":
				if line == "Staten Island":
					change.append(line)
				else:
					change.extend(line)

			if status == "DELAYS":
				if line == "Staten Island":
					delay.append(line)
				else:
					delay.extend(line)

	if good:
		good_sentence = oxfordComma(good)+ " trains are running fine."

	if work:
		work_sentence = "Some "+oxfordComma(work)+ " trains have scheduled work."

	if change:
		change_sentence = "There's a service change on the "+ oxfordComma(change)+ "."

	if delay:
		delay_sentence = "And blurgh, the "+oxfordComma(delay)+ " trains are running with delays."

	alltrains =  good_sentence + " " +  work_sentence + " " + change_sentence + " " + delay_sentence + presignoff + "Stand clear of the closing doors please!"
	return alltrains


def getBusStatus():
	good = []
	detour = []
	change = []
	delay =[]

	good_sentence = ""
	detour_sentence = ""
	change_sentence = ""
	delay_sentence = ""
	work_sentence = ""

	feed = getFeed("bus")
	if feed:
		soup = BeautifulSoup(feed, 'html.parser')
		rows = soup.find_all("tr")

		for r in rows:
			line = (r.select('td')[0].get_text(strip=True)).replace(" - ", " to ")
			status =  r.select('td')[1].get_text(strip=True)

			if status == "GOOD SERVICE":
				good.append(line)

			if status == "PLANNED DETOUR":
				detour.append(line)

			if status == "SERVICE CHANGE":
				change.append(line)

			if status == "DELAYS":
				delay.append(line)

	if good:
		good_sentence = oxfordComma(good) + " busses are running fine."

	if detour:
		detour_sentence = "There are detours on routes: "+ oxfordComma(detour) + "."

	if change:
		change_sentence = "Be aware of service changes on "+ oxfordComma(change) + " busses."

	if delay:
		delay_sentence = "Routes "+ oxfordComma(delay) + " are running with delays."

	allbusses =  good_sentence + " " +  detour_sentence + " " +  change_sentence + " " + delay_sentence + presignoff +"Please exit through the rear door!"
	return allbusses


def getLIRRStatus():
	good = []
	detour = []
	change = []
	delay = []
	work = []
	good_sentence = ""
	detour_sentence = ""
	change_sentence = ""
	delay_sentence = ""
	work_sentence = ""

	feed = getFeed("LIRR")
	if feed:
		soup = BeautifulSoup(feed, 'html.parser')
		rows = soup.find_all("tr")

		for r in rows:
			line = (r.select('td')[0].get_text(strip=True)).replace(" - ", " to ")
			status =  r.select('td')[1].get_text(strip=True)

			if status == "GOOD SERVICE":
				good.append(line)

			if status == "PLANNED DETOUR":
				detour.append(line)

			if status == "SERVICE CHANGE":
				change.append(line)

			if status == "DELAYS":
				delay.append(line)

			if status == "PLANNED WORK":
				work.append(line)

	if good:
		good_sentence = oxfordComma(good)+ " trains are running fine."

	if detour :
		print detour
		detour_sentence = "There are detours on the "+ oxfordComma(detour) + " lines."

	if change:
		change_sentence = "Be aware of service changes on "+oxfordComma(change)+ " trains."

	if work:
		work_sentence = "There is work planned on the "+oxfordComma(work)+ " lines."

	if delay:
		delay_sentence = oxfordComma(delay)+ " trains are running with delays."


	alltrains =  good_sentence + " " +  detour_sentence + " " +  change_sentence + " " + work_sentence + " " +delay_sentence + presignoff +" Tickets please!"
	return alltrains


def getMNRStatus():
	good = []
	detour = []
	change = []
	delay = []
	work = []
	good_sentence = ""
	detour_sentence = ""
	change_sentence = ""
	delay_sentence = ""
	work_sentence = ""

	feed = getFeed("MetroNorth")
	if feed:
		soup = BeautifulSoup(feed, 'html.parser')
		rows = soup.find_all("tr")

		for r in rows:
			line = (r.select('td')[0].get_text(strip=True)).replace(" - ", " to ")
			status =  r.select('td')[1].get_text(strip=True)

			if status == "GOOD SERVICE":
				good.append(line)

			if status == "PLANNED DETOUR":
				detour.append(line)

			if status == "SERVICE CHANGE":
				change.append(line)

			if status == "DELAYS":
				delay.append(line)

			if status == "PLANNED WORK":
				work.append(line)

	if good:
		good_sentence = oxfordComma(good)+ " trains are running fine."

	if detour :
		detour_sentence = "There are detours on the "+ oxfordComma(detour) + " lines."

	if change:
		change_sentence = "Be aware of service changes on "+oxfordComma(change)+ " trains."

	if work:
		work_sentence = "There is work planned on the "+oxfordComma(work)+ " lines."

	if delay:
		delay_sentence = oxfordComma(delay)+ " trains are running with delays."


	alltrains =  good_sentence + " " +  detour_sentence + " " +  change_sentence + " " + work_sentence + " " +delay_sentence + presignoff +" Tickets please!"
	return alltrains


def getBTStatus():
	good = []
	detour = []
	change = []
	delay = []
	work = []
	good_sentence = ""
	detour_sentence = ""
	change_sentence = ""
	delay_sentence = ""
	work_sentence = ""

	feed = getFeed("BT")
	if feed:
		soup = BeautifulSoup(feed, 'html.parser')
		rows = soup.find_all("tr")

		for r in rows:
			line = (r.select('td')[0].get_text(strip=True)).replace(" - ", " to ")
			status =  r.select('td')[1].get_text(strip=True)

			if status == "GOOD SERVICE":
				good.append(line)

			if status == "PLANNED DETOUR":
				detour.append(line)

			if status == "SERVICE CHANGE":
				change.append(line)

			if status == "DELAYS":
				delay.append(line)

			if status == "PLANNED WORK":
				work.append(line)

	if good:
		good_sentence = "The "+oxfordComma(good)+ " are all running fine."

	if detour :
		print detour
		detour_sentence = "There are detours on the "+oxfordComma(detour)+ "."

	if change:
		change_sentence = "Be aware of service changes on the "+oxfordComma(change)+ "."

	if work:
		work_sentence = "There is work planned on the "+oxfordComma(work)+ "."

	if delay:
		delay_sentence = "The "+oxfordComma(delay)+ " are backed up."


	allroutes =  good_sentence + " " +  detour_sentence + " " +  change_sentence + " " + work_sentence + " " +delay_sentence + presignoff +" Sunglasses off, lights on!"
	return allroutes


# GENERATE FEEDS
def getSubway():
	date, locale = dates()
	feed = {}
	feed['uid'] = str(uuid.uuid4())
	feed['updateDate'] = date.strftime('%Y-%m-%dT%H:%M:%S.0Z')
	feed['mainText'] = getSubwayStatus() #+ " By the way, we added something new! You can now get the status of individual train lines like the A C E or the 7 train. Just open up the Alexa app, go to your Flash Briefing settings, and select which trains you're interested in from the NYC Subway and Transit Skill."
	feed['titleText'] = "NYC Subway Status "+ locale
	feed['redirectionUrl'] = getDetailUrl("subway")
	feed_json = json.dumps(feed)
	return feed_json


def getBus():
	date, locale = dates()
	feed = {}
	feed['uid'] = str(uuid.uuid4())
	feed['updateDate'] = date.strftime('%Y-%m-%dT%H:%M:%S.0Z')
	feed['mainText'] = getBusStatus()
	feed['titleText'] = "NYC Bus System Status "+ locale
	feed['redirectionUrl'] = getDetailUrl("bus")
	feed_json = json.dumps(feed)
	return feed_json


def getLIRR():
	date, locale = dates()
	feed = {}
	feed['uid'] = str(uuid.uuid4())
	feed['updateDate'] = date.strftime('%Y-%m-%dT%H:%M:%S.0Z')
	feed['mainText'] = getLIRRStatus()
	feed['titleText'] = "Long Island Railroad Status "+ locale
	feed['redirectionUrl'] = getDetailUrl("LIRR")
	feed_json = json.dumps(feed)
	return feed_json


def getMNR():
	date, locale = dates()
	feed = {}
	feed['uid'] = str(uuid.uuid4())
	feed['updateDate'] = date.strftime('%Y-%m-%dT%H:%M:%S.0Z')
	feed['mainText'] = getMNRStatus()
	feed['titleText'] = "Metro North Railroad Status "+ locale
	feed['redirectionUrl'] = getDetailUrl("MetroNorth")
	feed_json = json.dumps(feed)
	return feed_json


def getBT():
	date, locale = dates()
	feed = {}
	feed['uid'] = str(uuid.uuid4())
	feed['updateDate'] = date.strftime('%Y-%m-%dT%H:%M:%S.0Z')
	feed['mainText'] = getBTStatus()
	feed['titleText'] = "NYC Bridge & Tunnel Status "+ locale
	feed['redirectionUrl'] = getDetailUrl("BT")
	feed_json = json.dumps(feed)
	return feed_json

# FEED GEN METHODS
def getAll():
	logging.info("Start getAll")
	feed = {}
	feed["subway"] = []
	feed["bus"] = []
	feed["lirr"] = []
	feed["mnr"] = []
	feed["bt"] = []

	feed["subway"] = (getSubway())
	feed["bus"] = (getBus())
	feed["lirr"] = (getLIRR())
	feed["mnr"] = (getMNR())
	feed["bt"] = (getBT())

	# CONNECT TO REDIS
	redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
	redisdb.set("mta", str(json.dumps(feed)))
	logging.info("MTA json data set")


def getDetail(line):
	statusre = re.compile(r"(?<=<br\/><br\/>).*?(?=<br\/><br\/>)", re.IGNORECASE | re.DOTALL)
	streetre= re.compile(r"(St.*?)[\W|\d]")
	html = requests.get("http://tripplanner.mta.info/mobileApps/serviceStatus/statusMessage.aspx?mode=subway&lineName=%s" % line).text
	soup = BeautifulSoup(html, 'html.parser')
	detail = statusre.search(html).group(0)
	detail = detail.replace("<a href='http://tripplanner.mta.info/MyTrip/ui_phone/cp/idefault.aspx'><img src='widgetImages/nyct/TripPlannerPlus_logo_19px.png' ></a>","").replace("shuttleBusIcon.png' width='19' height='20' />","").replace("<img src='widgetImages/nyct/", "").replace(".gif' width='16' height='16' />", "").replace("<br>", " ").replace("<br/>", " ").replace(" 311 "," 3 1 1 ").replace(" 511 "," 5 1 1 ").replace(" 711 "," 7 1 1 ")
	ds1 = strip_tags(detail).strip()
	ds2 = streetre.sub(r"Street ", ds1)
	ds3 = re.sub(r"(\[|\])", "", ds2)
	return ds3.strip()


def AllSubwayLines():
	logging.info("Start AllSubwayLines")
	try:
		feed = getFeed("subway")

		if "<TITLE>Access Denied</TITLE>" not in feed:
			soup = BeautifulSoup(feed, 'html.parser')
			rows = soup.find_all("tr")

			allLines = {}
			for r in rows:
				line=""

				imgs = r.find_all("img")
				for i in imgs:
					line = line + (i.get('src'))[-5:-4].upper()
				if imgs == []:
					line = "SIR"
				#print line
				
				status =  r.select('td')[1].get_text(strip=True)

				if status == "GOOD SERVICE":
					status_nice = "Trains are running fine."
					update = None

				if status == "PLANNED WORK":
					status_nice = "Planned work: %s" % getDetail(line)
					logging.debug(status_nice)
					update = True

				if status == "SERVICE CHANGE":
					status_nice = "Service change: %s" % getDetail(line)
					logging.debug(status_nice)
					update = True

				if status == "DELAYS":
					status_nice = "Delay update: %s" % getDetail(line)
					logging.debug(status_nice)
					update = True
				
				name = line
				if name == "NQR":
					prettyname = oxfordComma("NQRW")
				elif name == "SIR":
					prettyname = "Stated Island"
				elif name == "S":
					prettyname = "Shuttle"
				else:
					prettyname = oxfordComma(str(line))
				
				date, locale = dates()
				feed = {}
				feed['uid'] = str(uuid.uuid4())
				feed['updateDate'] = date.strftime('%Y-%m-%dT%H:%M:%S.0Z')
				feed['mainText'] = status_nice
				feed['titleText'] = name + " SUBWAY - " + status.upper()
				if update is not None:
					feed['redirectionUrl'] = "http://tripplanner.mta.info/mobileApps/serviceStatus/serviceStatusPage.aspx?mode=subway"
				feed_json = json.dumps(feed)
				
				allLines[name] = feed_json

				#print feed_json

			# CONNECT TO REDIS
			redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
			redisdb.set("subwayLines", str(json.dumps(allLines)))
			logging.info("Ok, AllsubwayLines json data set")
			return "True"
		else:
			logging.error("rate limited / can't access MTA feeds ~ MTA.py")
	except Exception as e:
		logging.debug("Error retrieving / generating allLines feed %s" % e)
		raise
		return False


def listSubwayData():
	redisdb = redis.StrictRedis.from_url(os.environ['REDIS_URL'])
	logging.info( redisdb.get("mta") )
	logging.info( redisdb.get("subwayLines") )

######## Actually, let's rock!!
if __name__ == "__main__":
	# generate feeds for each line
	getAll()
	
	# generate all lines feed
	AllSubwayLines()

	#getDetail("123")
	#getDetail("456")
	#getDetail("ACE")
	#getDetail("SIR")
	#getDetail("S")

	# generate dem data
	#listSubwayData()

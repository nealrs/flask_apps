#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# This clock process should run jobs every 30 min or whatever & dump results in redis
#

import os
import logging
from raven import Client
sentry = Client(os.environ['SENTRY_DSN'])
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

import mta
import news

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
sched = BlockingScheduler()
#sched = BackgroundScheduler()


@sched.scheduled_job('cron', minute="*/30")
def News():
    news.getAll()
    logging.info("cache News data for flash briefing feeds / app | every 30 mins")
    #slackNotify("halfhourlyNews")


@sched.scheduled_job('cron', minute="*/30")
def MTA():
    mta.getAll()
    mta.AllSubwayLines()
    logging.info("cache MTA data for flash briefing feeds | every 30 mins")
    #slackNotify("halfhourlyMTA")

sched.start()
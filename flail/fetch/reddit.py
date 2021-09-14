#Reddit client functions
import praw
from psaw import PushshiftAPI
import json
import os
import time
import datetime as dt
import re
from asyncio import Queue
from threading import Timer

import smtplib, ssl
from email.message import EmailMessage

from django.db import models, transaction, connection, IntegrityError
from django.core.exceptions import ValidationError
from .models import Comment, Submission, SentimentRating, Ticker, Tweet
from flail.settings import BASE_DIR



#make reddit effectively a global variable. 
#if we're not calling through the main function, you need to 
#pass a client to any function in to any function that makes requests
client = None

#when true, we will use the ticker list file and only store relevant comments
#if false, ALL comments are stored
FILTER_TICKER = True

#fetches recent comments from the specified subreddit
#takes a subreddit name and optionally a client instance
#returns a 
def fetch_recent(subreddit, client=None, tickerlist=None):
	if client is None:
		client = praw.Reddit(
			client_id=os.environ["REDDIT_ID"],
			client_secret=os.environ["REDDIT_KEY"],
			user_agent=os.environ["REDDIT_AGENT"]
			)
	if tickerlist is None:
		tickerlist = TICKERS


	with open(os.path.join(BASE_DIR, "dailytickers.json")) as file:
		daily_tickers = json.load(file)

	#we should find out a good minimum comments/second rate of the subreddits so we dont
	#get too many repeated, but also should always be higher so we never miss a comment
	#either way, database insertion method should check if the comment exists in our records and do nothing if so
	num_new_comments = 0
	for comment in client.subreddit(subreddit).comments(limit=70):
		num_new_comments += add_new_comment(comment, tickerlist)
		daily_tickers = update_daily_tickers(comment, daily_tickers)

	if(daily_tickers):
		with open(os.path.join(BASE_DIR, "dailytickers.json"),'w') as file:
			json.dump(daily_tickers, file)

	num_new_submissions = 0
	# for submission in client.subreddit(subreddit).new(limit=20):
	# 	num_new_submissions += add_new_submission(submission)

	return num_new_comments, num_new_submissions

#fetches comments about the tickers in tickerlist from the specified time range/subreddit
#start and end_time are datetime objects specifying a time range
#end_time is input as +60 to make sure we get all comments in time range, may get a minute more
#uses the psaw api wrapper to search historical reddit data
def fetch_historical_comments(subreddit, start_time, end_time=None, tickerlist=None):
	global client
	if client is None:
		client = praw.Reddit(
			client_id=os.environ["REDDIT_ID"],
			client_secret=os.environ["REDDIT_KEY"],
			user_agent=os.environ["REDDIT_AGENT"]
			)
	if tickerlist is None:
		tickerlist = TICKERS
	
	pmawAPI = PushshiftAPI(client)


	
	start = int(start_time.timestamp())
	if end_time:
		end = int(end_time.timestamp())
	else:
		end = int(dt.utcnow().timestamp())

	last_comment_time = start + 1
	num_new_comments = 0
	
	max_comments_cache = 1000
	total_count = 0
	lastComment = None
	comment_queue = Queue()
	while True:
		comments = pmawAPI.search_comments(subreddit=subreddit,
						after=start, 
						before=end+60,
						size=100,
						limit=100,
						max_results_per_request=100,
						sort="asc")
		
		count = 0
		stime = time.time()
		for c in comments:
			num_new_comments += add_new_comment(c, tickerlist)
			count += 1
			#print(dt.datetime.fromtimestamp(int(c.created_utc)).isoformat() + " : " + c.body)

			lastComment = c
			if count >= max_comments_cache:
				print("numcomms: "+ str(total_count)+"  lastcommenttime:" + dt.datetime.fromtimestamp(int(c.created_utc)).isoformat())
				break
		etime = time.time()
		total_count += count
		start = int(lastComment.created_utc)
		print("new start time: "+ dt.datetime.fromtimestamp(start).isoformat())
		print(total_count)
		print("time to analyze: "+str(etime-stime))

		if lastComment and lastComment.created_utc >= end:
			break


#updates daily ticker list if we find a ticker looking thing in the given comment
def update_daily_tickers(comment, daily_tickers):
	potential_tickers = re.findall(r'[A-Z]{3,4}[ \.]', comment.body)

	#if too many in one comment, may be either spam or simply caps lock
	if len(potential_tickers) > 5 or len(potential_tickers) == 0:
		return daily_tickers

	for ticker in potential_tickers:
		ticker = ticker[:-1]
		if ticker in daily_tickers.keys():
			daily_tickers[ticker] += 1
		else:
			daily_tickers[ticker] = 1

	return daily_tickers


#gathers the daily ticker contenders and sends info about top 3 in an email 	
def aggregate_daily_tickers(reset=True):
	#set up another timer so this reruns daily
	delta_t = dt.timedelta(days=1)

	t = Timer(delta_t.total_seconds(), aggregate_daily_tickers)
	t.start()

	

	with open(os.path.join(BASE_DIR, "dailytickers.json")) as file:
		daily_tickers = json.load(file)

	#checks if the word/phrase is in the nyse registered ticker list
	nyse = []
	updated_daily_tickers = {}
	with open(os.path.join(BASE_DIR, "ticker_NYSE.txt")) as file:
		for line in file:
			nyse.append(line.strip())
	for tick, volume in daily_tickers.items():
		if tick in nyse:
			updated_daily_tickers[tick] = volume
	daily_tickers = update_daily_tickers



	email_string = "TOP DAILY TICKERS " + dt.datetime.today().isoformat() + "\n"
	sorted_tickers = sorted(daily_tickers.items(), key=lambda x: x[1], reverse=True)
	if len(sorted_tickers) < 3:
		print("Not enough tickers to send email")
		return


	for i in range(3):
		tick = sorted_tickers[i]
		if tick[1] < 3:
			break
		email_string += str(i+1)+". " + tick[0] + "\n"
		email_string += "\tvolume: " + str(tick[1]) + "\n"

	email_string += "\nWhole List: \n" +repr(sorted_tickers)

	#reset dailyticker file so it gathers new ones tomorrow
	with open(os.path.join(BASE_DIR, "dailytickers.json"), 'w') as file:
		file.write("{}")

	try:
		context = ssl.create_default_context()
		with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
			server.login(os.environ["FLAIL_MAIL_USER"], os.environ["FLAIL_MAIL_PSWD"])
			receivers = [
				"eamona.collins@gmail.com",
				"dv5mx@virginia.edu",
				"kb8vz@icloud.com"
			]
			server.sendmail('flaildailyupdates@gmail.com',receivers, email_string)
		print("SENT EMAIL")
		
	except smtplib.SMTPException as e:
		print("can't send mail: "+repr(e))



#Passes in an open database instance and a praw.Comment object and an open database instance
#should check to see if comment is in database or not
def add_new_comment(comment, tickerlist=None):
	if tickerlist is None:
		tickerlist = TICKERS

	#for now, try-except to watch out for attempt to add same comment twice.
	#might be best way to do it tbh.
	try:
		#edit down fields with extra info to booleans
		if comment.distinguished:
			comment.distinguished = True
		if not comment.author:
			author = "[deleted]"
		else:
			author = comment.author.name

		relevant_tickers = check_relevance(comment, tickerlist)
		#relevant_tickers = None

		if relevant_tickers or not FILTER_TICKER:
			newComment = Comment.objects.create(
				id = comment.id,
				author = author,
				body = comment.body,
				score = comment.score,
				edited = (not comment.edited==False),
				num_replies = len(comment.replies),
				distinguished = comment.distinguished,
				created_utc = comment.created_utc,
				link_id = comment.link_id,
				parent_id = comment.parent_id,
				subreddit = comment.subreddit.name,
				permalink = comment.permalink
				)
			newComment.save()
		if relevant_tickers:
			for ticker in relevant_tickers:
				newSentimentRating = SentimentRating.objects.create(
					ticker = Ticker.objects.get(ticker_symbol=ticker["ticker_symbol"]),
					created_utc = newComment.created_utc,
					source_comment = newComment
					)
				newSentimentRating.save()
		return 1
	#if id already exists we've already seen this, dont count as new
	except IntegrityError as e:
		return 0

def add_new_submission(submission, tickerlist=None):
	if tickerlist is None:
		tickerlist = TICKERS

	try:
		if submission.distinguished:
			submission.distinguished = True
		if submission.is_self:
			submission.is_self = True

		relevant_tickers = check_relevance(submission, tickerlist)
		#relevant_tickers = None

		if relevant_tickers or not FILTER_TICKER:
			newSubmission = Submission.objects.create(
				id = submission.id,
				author = submission.author.name,
				title = submission.title,
				score = submission.score,
				edited = (not submission.edited==False),
				is_self = submission.is_self,
				num_replies = submission.num_comments,
				distinguished = submission.distinguished,
				upvote_ratio = submission.upvote_ratio,
				created_utc = submission.created_utc,
				subreddit = submission.subreddit.name,
				permalink = submission.permalink
				)
			newSubmission.save()
		if relevant_tickers:
			for ticker in relevant_tickers:
				newSentimentRating = SentimentRating.objects.create(
					ticker = Ticker.objects.get(ticker_symbol=ticker["ticker_symbol"]),
					created_utc = newSubmission.created_utc,
					source_submission = newSubmission
					)		
		return 1
	except ValidationError as e:
		raise e
	except IntegrityError as e: #comment with same global id already recorded
		return 0


#checks if environment vars are set, if not it
#ingests the secrets file and sets them as environment variables
def load_secrets():
	if not "REDDIT_KEY" in os.environ:
		with open(os.path.join(BASE_DIR, 'SECRETS.json')) as f:
			secrets = json.load(f)
		secrets = secrets["REDDIT"]
		os.environ["REDDIT_AGENT"] = secrets["user_agent"]
		os.environ["REDDIT_ID"] = secrets["client_id"]
		os.environ["REDDIT_KEY"] = secrets["client_secret"]

	if not "FLAIL_MAIL_USER" in os.environ:
		with open(os.path.join(BASE_DIR, 'SECRETS.json')) as f:
			secrets = json.load(f)
		secrets = secrets["FLAIL_MAIL"]
		os.environ["FLAIL_MAIL_USER"] = secrets["gmail_user"]
		os.environ["FLAIL_MAIL_PSWD"] = secrets["gmail_pswd"]

def load_tickers(filepath=None):
	with open(filepath) as file:
		tickers = json.load(file)
	#make sure we have these in database
	for company, data in tickers.items():
		newTicker, created = Ticker.objects.update_or_create(
			ticker_symbol = data["ticker_symbol"],
			keywords = json.dumps(data["keywords"])
			#defaults = {"keywords":data["keywords"]}
			)

	global TICKERS 
	TICKERS = tickers
	return tickers

#checks if the post contains any listed keywords
#currently submission/comment agnostic, but add check if you're adding
#source types
def check_relevance(post, tickerlist=None):
	relevant_tickers = []

	if tickerlist is None:
		tickerlist = TICKERS

	#print(tickers)
	if hasattr(post, 'body'): #post is a comment
		for company, data in tickerlist.items():
			for kw in data["keywords"]:
				if kw in post.body:
					if data not in relevant_tickers:
						relevant_tickers.append(data)
					break
	elif hasattr(post, 'is_self'): #post is a submission
		for company, data in tickerlist.items():
			for kw in data["keywords"]:
				if kw in post.title:
					if data not in relevant_tickers:
						relevant_tickers.append(data)
					break
	elif isinstance(post, dict) and "retweetCount" in post.keys(): #post is tweet json
		for company, data in tickerlist.items():
			for kw in data["keywords"]:
				if kw in post["content"]:
					if data not in relevant_tickers:
						relevant_tickers.append(data)
	return relevant_tickers

#not intended to be run as a script necessarily, but effectively this 
#should be the central function for most use of this module
def central_reddit_fetch():
	#make sure we have secrets
	load_secrets()
	#load the ticker list in
	#global TICKERS 
	#TICKERS = load_tickers(os.path.join(BASE_DIR, 'tickerlist.json'))

	#create client
	if client is None:
		client = praw.Reddit(
			client_id=os.environ["REDDIT_ID"],
			client_secret=os.environ["REDDIT_KEY"],
			user_agent=os.environ["REDDIT_AGENT"]
			)


	print("Starting historical search")
	start = dt.datetime(2021,8,1)
	end = dt.datetime(2021,8,30) #30th of august
	fetch_historical_comments("wallstreetbets", start, end)

	#Currently scheduling this with a sufficient solution, but
	#airflow cronjobs would likely be better. Or a parallelized python library
	## Checkout django-celery
	while True:
		startTime = time.time()

		recent_wsb_comments, recent_wsb_submissions = fetch_recent("wallstreetbets", reddit)

		#close database connection so server thread can start anew
		connection.close()

		nowTime = time.time() - startTime
		print(nowTime)
		if (15.0 - nowTime) > 0:
			time.sleep(15.0 - nowTime)

def fuck_this_list():
	ticks = []
	with open(os.path.join(BASE_DIR, "ticker_NYSE.txt")) as file:
		for line in file:
			if line != "" and line != "\n" and "$" not in line and "." not in line:
				ticks.append(line)
	with open(os.path.join(BASE_DIR, "ticker_NYSE.txt"), 'w') as file:
		for line in ticks:
			file.write(line)


			

#anything that imports reddit module will have access to the TICKERS variable
#by using reddit.TICKERS
load_tickers(os.path.join(BASE_DIR, "tickerlist.json"))

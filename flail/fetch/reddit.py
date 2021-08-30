#Reddit client functions
import praw
from psaw import PushshiftAPI
import json
import os
import time
import datetime as dt
from django.db import models, transaction, connection, IntegrityError
from django.core.exceptions import ValidationError
from .models import Comment, Submission, SentimentRating, Ticker
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
def fetch_recent(subreddit, client=None):
	if client is None:
		client = praw.Reddit(
			client_id=os.environ["REDDIT_ID"],
			client_secret=os.environ["REDDIT_KEY"],
			user_agent=os.environ["REDDIT_AGENT"]
			)



	#we should find out a good minimum comments/second rate of the subreddits so we dont
	#get too many repeated, but also should always be higher so we never miss a comment
	#either way, database insertion method should check if the comment exists in our records and do nothing if so
	num_new_comments = 0
	for comment in client.subreddit(subreddit).comments(limit=50):
		num_new_comments += add_new_comment(comment)

	num_new_submissions = 0
	for submission in client.subreddit(subreddit).new(limit=20):
		num_new_submissions += add_new_submission(submission)

	return num_new_comments, num_new_submissions

#fetches comments about the tickers in tickerlist from the specified time range/subreddit
#start and end_time are datetime objects specifying a time range
#end_time is input as +60 to make sure we get all comments in time range, may get a minute more
#uses the psaw api wrapper to search historical reddit data
def fetch_historical_comments(subreddit, start_time, end_time=None):
	global client
	if client is None:
		client = praw.Reddit(
			client_id=os.environ["REDDIT_ID"],
			client_secret=os.environ["REDDIT_KEY"],
			user_agent=os.environ["REDDIT_AGENT"]
			)

	psawAPI = PushshiftAPI(client)


	
	start_time = int(start_time.timestamp())
	if end_time:
		end_time = int(end_time.timestamp())
	else:
		end_time = int(dt.utcnow().timestamp())

	last_comment_time = start_time + 1
	num_new_comments = 0

	while last_comment_time < end_time:
		comments = psawAPI.search_comments(subreddit=subreddit,
							after=start_time, 
							before=end_time+60,
							size=500
							)

		for c in comments:
			num_new_comments += add_new_comment(c)

		#update our end condition and also make sure we get a new batch next request
		if comments:
			last_comment_time = comments[-1].created_utc
			start_time = comments[-1].created_utc
		else:
			print("No comments found, exiting historical search")
			break

#Passes in an open database instance and a praw.Comment object and an open database instance
#should check to see if comment is in database or not
def add_new_comment(comment):

	#for now, try-except to watch out for attempt to add same comment twice.
	#might be best way to do it tbh.
	try:
		#edit down fields with extra info to booleans
		if comment.distinguished:
			comment.distinguished = True
		if comment.author is None:
			author = "None/Deleted"
		else:
			author = comment.author.name

		relevant_tickers = check_relevance(comment)
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
		return 1
	#if id already exists we've already seen this, dont count as new
	except IntegrityError as e:
		return 0

def add_new_submission(submission):

	try:
		if submission.distinguished:
			submission.distinguished = True
		if submission.is_self:
			submission.is_self = True

		relevant_tickers = check_relevance(submission)
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
def check_relevance(post):
	relevant_tickers = []
	#print(tickers)
	if hasattr(post, 'body'): #post is a comment
		for company, data in TICKERS.items():
			for kw in data["keywords"]:
				if kw in post.body:
					relevant_tickers.append(data)
					break
	else: #post is a submission
		for company, data in TICKERS.items():
			for kw in data["keywords"]:
				if kw in post.title:
					relevant_tickers.append(data)
					break
	return relevant_tickers

#not intended to be run as a script necessarily, but effectively this 
#should be the central function for most use of this module
def central_reddit_fetch():
	#make sure we have secrets
	load_secrets()
	#load the ticker list in
	global TICKERS 
	TICKERS = load_tickers(os.path.join(BASE_DIR, 'tickerlist.json'))

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

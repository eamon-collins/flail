#Reddit client functions
import praw
import json
import os
import time
from django.db import models
from .models import Comment, Submission


#make reddit effectively a global variable. 
#if we're not calling through the main function, you need to 
#pass a client to any function in to any function that makes requests
reddit = None

#fetches recent comments from the specified subreddit
#takes a subreddit name and optionally a client instance
#returns a 
def fetch_recent(subreddit, client=None):
	if client is None and reddit is None:
		raise RuntimeError("Need to call from central function or pass in reddit instance")
	elif client is None:
		client = reddit


	#we should find out a good minimum comments/second rate of the subreddits so we dont
	#get too many repeated, but also should always be higher so we never miss a comment
	#either way, database insertion method should check if the comment exists in our records and do nothing if so
	num_new_comments = 0
	for comment in client.subreddit(subreddit).comments(limit=100):
		num_new_comments += add_new_comment(comment)

	num_new_submissions = 0
	for submission in client.subreddit(subreddit).new():
		num_new_submissions += add_new_submission(submission)

	return num_new_comments, num_new_submissions

#Passes in an open database instance and a praw.Comment object and an open database instance
#should check to see if comment is in database or not
def add_new_comment(comment):

	#for now, try-except to watch out for attempt to add same comment twice.
	#might be best way to do it tbh.
	try:
		newComment = Comment.objects.create(
			id = comment.id,
			author = comment.author.name,
			body = comment.body,
			score = comment.score,
			edited = comment.edited,
			num_replies = len(comment.replies),
			distinguished = comment.distinguished,
			created_utc = comment.created_utc,
			# link_id = comment.link_id,
			# parent_id = comment.parent_id,
			subreddit = comment.subreddit.name,
			permalink = comment.permalink
			)
		newComment.save()
		return 1
	except Exception as e:
		print(str(e))
		return 0

def add_new_submission(submission):
	try:
		newSubmission = Submission.objects.create(
			id = submission.id,
			author = submission.author.name,
			title = submission.title,
			score = submission.score,
			edited = submission.edited,
			num_replies = submission.num_comments,
			distinguished = submission.distinguished,
			upvote_ratio = submission.upvote_ratio,
			created_utc = submission.created_utc,
			subreddit = submission.subreddit.name,
			permalink = submission.permalink
			)
		newSubmission.save()
		return 1
	except Exception as e:
		print(repr(e))
		return 0


#checks if environment vars are set, if not it
#ingests the secrets file and sets them as environment variables
def load_secrets():
	if not "REDDIT_KEY" in os.environ:
		with open('./SECRETS.json') as f:
			secrets = json.load(f)
		secrets = secrets["REDDIT"]
		os.environ["REDDIT_AGENT"] = secrets["user_agent"]
		os.environ["REDDIT_ID"] = secrets["client_id"]
		os.environ["REDDIT_KEY"] = secrets["client_secret"]


#not intended to be run as a script necessarily, but effectively this 
#should be the central function for most use of this module
def central_reddit_fetch():
	#make sure we have secrets
	load_secrets()

	#create client
	reddit = praw.Reddit(
		client_id=os.environ["REDDIT_ID"],
		client_secret=os.environ["REDDIT_KEY"],
		user_agent=os.environ["REDDIT_AGENT"]
		)

	#Currently scheduling this with a sufficient solution, but
	#airflow cronjobs would likely be better. Or a parallelized python library
	starttime = time.time()
	while True:
		recent_wsb_comments, recent_wsb_submissions = fetch_recent("wallstreetbets", reddit)

		if (10.0 - (time.time() - starttime)) > 0:
			time.sleep(10.0 - (time.time() - starttime)) 

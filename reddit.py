#Reddit client functions


import praw
import json
import os



#make reddit effectively a global variable. 
#if we're not calling through the main function, you need to 
#pass a client to any function in to any function that makes requests
reddit = None

#fetches recent comments from the specified subreddit
#takes a subreddit name and optionally a client instance
#returns a 
def fetch_recent(subreddit, client=None):
	if client is None and reddit is None:
		raise RunTimeError("Need to call from central function or pass in reddit instance")
	elif client is None:
		client = reddit


	#we should find out a good minimum comments/second rate of the subreddits so we dont
	#get too many repeated, but also should always be higher so we never miss a comment
	#either way, database insertion method should check if the comment exists in our records and do nothing if so
	for comment in client.subreddit(subreddit).comments(limit=100):
		add_new_comment(comment)

#Passes in an open database instance and a praw.Comment object and an open database instance
#should check to see if comment is in database or not
def add_new_comment(comment):
	pass


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
def main():
	#make sure we have secrets
	load_secrets()

	#create client
	reddit = praw.Reddit(
		client_id=os.environ["REDDIT_ID"],
		client_secret=os.environ["REDDIT_KEY"],
		user_agent=os.environ["REDDIT_AGENT"]
		)

	recent_wsb = fetch_recent("wallstreetbets")
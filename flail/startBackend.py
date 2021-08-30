#Main script to start backend timed tasks



#get settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flail.settings')
import django
django.setup()

import fetch.reddit as reddit
import analyze.sentiment as sentiment
from flail.settings import BASE_DIR

import praw
import datetime as dt
import time

TICKERS = None


def main():


	#make sure we have secrets
	reddit.load_secrets()
	#load the ticker list in
	global TICKERS 
	TICKERS = reddit.load_tickers(os.path.join(BASE_DIR, 'tickerlist.json'))

	#create client
	redditClient = praw.Reddit(
		client_id=os.environ["REDDIT_ID"],
		client_secret=os.environ["REDDIT_KEY"],
		user_agent=os.environ["REDDIT_AGENT"]
		)

	print("Fetching historical data")
	start = dt.datetime(2021, 8, 1)
	end = dt.datetime(2021, 8, 30)
	reddit.fetch_historical_comments("wallstreetbets", start, end)

	startTime = time.time()
	#makes it so it generates a graph right when you start for convenience
	lastGraph = startTime - 600
	while(True):
		loopTime = time.time()
		
		recent_wsb_comments, recent_wsb_submissions = reddit.fetch_recent("wallstreetbets", redditClient)
		fetch_time = time.time()
		print("Fetched "+repr(recent_wsb_comments) +" new comments and "+repr(recent_wsb_submissions)+" new submissions in "+repr(round(fetch_time-loopTime, 2))+" seconds")

		num_in_queue = sentiment.analyze_queue()
		print("Analyzed "+repr(num_in_queue)+" new relevant entries in "+repr(round(time.time()-fetch_time, 2))+" seconds")

		#every 10 mins prepare graphs and update longer term diagnostic
		#info like volume of relevant 
		if loopTime - lastGraph >= 600:
			for company, data in TICKERS.items():
				sentiment.prepare_sentiment_graph(data)

			lastGraph = time.time()
			print("Produced new graphs")

		nowTime = time.time() - loopTime
		if (15.0 - nowTime) > 0:
			time.sleep(15.0 - nowTime)


if __name__ == '__main__':
	main()
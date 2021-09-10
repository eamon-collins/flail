#Main script to start backend timed tasks



#get settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flail.settings')
import django
django.setup()

import fetch.reddit as reddit
import fetch.twitter as twitter
import analyze.sentiment as sentiment
from flail.settings import BASE_DIR

import praw
import datetime as dt
import time
from threading import Timer

TICKERS = None


def main():


	#make sure we have secrets
	reddit.load_secrets()
	#load the ticker list in
	#should now be done whenever you import fetch.reddit
	# global TICKERS 
	# TICKERS = reddit.load_tickers(os.path.join(BASE_DIR, 'tickerlist.json'))

	#create client
	redditClient = praw.Reddit(
		client_id=os.environ["REDDIT_ID"],
		client_secret=os.environ["REDDIT_KEY"],
		user_agent=os.environ["REDDIT_AGENT"]
		)

	# print("Fetching historical data")
	# start = dt.datetime(2021, 9, 1, hour=15, minute=50)
	# end = dt.datetime(2021, 9, 9)
	# reddit.fetch_historical_comments("wallstreetbets", start, end)

	# twitter.ingest_twitter_json("/home/eamon/Downloads/text-query-tweets2.json")
	# return

	#set up a timer to handle aggregating the top tickers and emailing the info out
	#20 because that's 4pm EST specified in UTC
	x = dt.datetime.today()
	today = 1 if x.hour >= 20 else 0
	y = (x + dt.timedelta(days=today)).replace(hour=20,minute=0,second=0,microsecond=0) 
	delta_t = y-x

	print(delta_t.total_seconds())

	t = Timer(delta_t.total_seconds(), reddit.aggregate_daily_tickers)
	t.start()

	startTime = time.time()
	#makes it so it generates a graph right when you start for convenience
	lastGraph = startTime - 600
	while(True):
		loopTime = time.time()
		
		recent_wsb_comments, recent_wsb_submissions = reddit.fetch_recent("wallstreetbets", redditClient, )
		fetch_time = time.time()
		print("Fetched "+repr(recent_wsb_comments) +" new comments and "+repr(recent_wsb_submissions)+" new submissions in "+repr(round(fetch_time-loopTime, 2))+" seconds")

		num_in_queue = sentiment.analyze_queue()
		print("Analyzed "+repr(num_in_queue)+" new relevant entries in "+repr(round(time.time()-fetch_time, 2))+" seconds")

		#every 10 mins prepare graphs and update longer term diagnostic
		#info like volume of relevant 
		if loopTime - lastGraph >= 600:
			for company, data in reddit.TICKERS.items():
				sentiment.prepare_sentiment_graph(data)

			lastGraph = time.time()
			print("Produced new graphs")

			#also use this time to send 

		nowTime = time.time() - loopTime
		if (15.0 - nowTime) > 0:
			time.sleep(15.0 - nowTime)


if __name__ == '__main__':
	main()
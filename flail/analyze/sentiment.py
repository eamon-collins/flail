#Sentiment analysis functions

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
from matplotlib.dates import drange, DateFormatter
import numpy as np
from os import path
import json

from django.db import models, transaction, connection, IntegrityError
from django.core.exceptions import ValidationError
from fetch.models import Comment, Submission, SentimentRating, Ticker
#want this so we can use TICKERS
import fetch.reddit as reddit
from flail.settings import BASE_DIR
from django.utils.timezone import make_aware

#this method is duplicated here so it can execute within it's own thread
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

	return tickers

#checks for new, unevaluated comments straight from the autist's fingers
def analyze_queue():
	analyzer = SentimentIntensityAnalyzer()

	start_time = datetime(2021,9,2,hour=10)
	new_sentiments = SentimentRating.objects.filter(sentiment_rating__isnull=True, created_utc__gte=start_time)
	num_new = new_sentiments.count()

	for sentimentRating in new_sentiments:
		if sentimentRating.source_comment is not None:
			text = sentimentRating.source_comment.body
		elif sentimentRating.source_submission is not None:
			text = sentimentRating.source_submission.title
		elif sentimentRating.source_tweet is not None:
			text = sentimentRating.source_tweet.body 
		else:
			print("no source text to analyze")
			continue
			

		keywords = sentimentRating.ticker.get_keywords()

		tokenized = text.split('.')

		sentence_indices = set()
		for index, sentence in enumerate(tokenized):
			for kw in keywords:
				if kw in sentence:
					sentence_indices.add(index)
					sentence_indices.add(index+1)
					

		sentiments = []
		for index in sentence_indices:
			try:
				sentence = tokenized[index]
			except IndexError:
				continue
			sentiments.append(analyzer.polarity_scores(sentence)['compound'])

		if len(sentiments):
			sentimentRating.sentiment_rating = sum(sentiments) / len(sentiments)
		else:
			sentimentRating.sentiment_rating = 0 

	if num_new > 0:
		SentimentRating.objects.bulk_update(new_sentiments, ['sentiment_rating'])

	return num_new

#for specified ticker object, get relevant sentiment ratings from 
#last 24 hour period and put on a graph gapped into 10 min segments
def prepare_sentiment_graph(ticker, time_increment=10):
	delta = timedelta(days=1)
	x_time_segment = timedelta(minutes=time_increment)
	#make_aware is djangos UTC conversion
	now_time = make_aware(datetime.now())

	tickerObject = Ticker.objects.get(ticker_symbol=ticker['ticker_symbol'])
	current_days_posts = SentimentRating.objects.filter(ticker=tickerObject, 
		created_utc__gte=now_time-delta,
		sentiment_rating__isnull=False)

	num_x_segments = int(delta / x_time_segment)
	x_positive = np.zeros(num_x_segments)
	x_neutral = np.zeros(num_x_segments)
	x_negative = np.zeros(num_x_segments)
	
	time_counter = now_time - delta
	more_now_time = datetime.now()
	#x_axis = drange(more_now_time-delta, more_now_time, x_time_segment)
	x_axis = np.arange(num_x_segments)
	print("start: "+time_counter.strftime('%d:%H:%M') + "  end: "+now_time.strftime('%d:%H:%M'))
	#print("numxseg " + repr(num_x_segments)+ "lenxaxis "+repr(len(x_axis)))
	index = 0
	while not (time_counter >= now_time):
		increment = current_days_posts.filter(created_utc__gte=time_counter, created_utc__lt=time_counter+x_time_segment)
		#increment = increment.order_by('-created_utc')

		for sentimentRating in increment:
			if sentimentRating.sentiment_rating >= .2:
				x_positive[index] += 1
			elif sentimentRating.sentiment_rating <= -.2:
				x_negative[index] += 1
			else:
				x_neutral[index] += 1

		index +=1
		time_counter += x_time_segment

	# print(x_axis)
	# print(x_positive)
	# print(x_negative)
	#extend x axis
	#plt.figure(figsize=(12,3))
	#ax = plt.subplot(111)
	fig, ax = plt.subplots(figsize=(12,3))
	ax.xaxis_date(tz='EST')
	ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
	ax.bar(x_axis, x_positive, color= 'g', align='center')
	ax.bar(x_axis, x_neutral, color= 'grey', bottom = x_positive, align='center')
	ax.bar(x_axis, x_negative, color='r', bottom = x_positive+x_neutral, align='center')

	
	plt.savefig(path.join(BASE_DIR, 'static/graphs/'+repr(tickerObject.id)+'_sentiment.png'))

def prepare_all_graphs():
	while True:
		startTime = time.time()

		TICKERS = load_tickers(path.join(BASE_DIR,"tickerlist.json"))

		for company, data in TICKERS.items():
			prepare_sentiment_graph(data)


		#not sure if this is really needed, but probably at least 
		#best to keep doing it until we get a non-file db solution up
		connection.close()

		nowTime = time.time() - startTime
		print("Finished making graphs")
		if (300 - nowTime) > 0:
			time.sleep(300 - nowTime)
	




def central_queue_analyze():
	while True:
		startTime = time.time()

		num_in_queue = analyze_queue()

		#not sure if this is really needed, but probably at least 
		#best to keep doing it until we get a non-file db solution up
		#connection.close()

		nowTime = time.time() - startTime
		if num_in_queue > 0:
			print("Analysis of queue took "+repr(nowTime)+" secs and analyzed "+repr(num_in_queue)+" new entries.")
		if (30 - nowTime) > 0:
			time.sleep(30 - nowTime)
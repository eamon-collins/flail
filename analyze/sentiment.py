#Sentiment analysis functions

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import numpy as np
from os import path

from django.db import models, transaction, connection, IntegrityError
from django.core.exceptions import ValidationError
from fetch.models import Comment, Submission, SentimentRating, Ticker
from fetch.reddit import load_tickers
from flail.settings import BASE_DIR
from django.utils.timezone import make_aware

#checks for new, unevaluated comments straight from the autist's fingers
def analyze_queue():
	analyzer = SentimentIntensityAnalyzer()

	new_sentiments = SentimentRating.objects.filter(sentiment_rating__isnull=True)
	num_new = new_sentiments.count()

	for sentimentRating in new_sentiments:
		if sentimentRating.source_comment is not None:
			text = sentimentRating.source_comment.body
		elif sentimentRating.source_submission is not None:
			text = sentimentRating.source_submission.title 
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

		sentimentRating.sentiment_rating = sum(sentiments) / len(sentiments)

	if num_new > 0:
		SentimentRating.objects.bulk_update(new_sentiments, ['sentiment_rating'])

	return num_new

#for specified ticker object, get relevant sentiment ratings from 
#last 24 hour period and put on a graph gapped into 5 min segments
def prepare_sentiment_graph(ticker):
	delta = timedelta(days=1)
	x_time_segment = timedelta(minutes=5)
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
	x_axis = np.arange(num_x_segments)
	time_counter = now_time - delta
	while not (time_counter >= now_time):
		increment = current_days_posts.filter(created_utc__gte=time_counter, created_utc__lt=time_counter+x_time_segment)
		increment = increment.order_by('-created_utc')

		for index, sentimentRating in enumerate(increment):
			if sentimentRating.sentiment_rating >= .2:
				x_positive[index] += 1
			elif sentimentRating.sentiment_rating <= -.2:
				x_negative[index] += 1
			else:
				x_neutral[index] += 1

		time_counter += x_time_segment


	plt.bar(x_axis, x_positive, color= 'g')
	plt.bar(x_axis, x_neutral, color= 'grey', bottom = x_positive)
	plt.bar(x_axis, x_negative, color='r', bottom = x_positive+x_neutral)

	#plt.show()
	print(path.join(BASE_DIR, 'static/graphs/'+repr(tickerObject.id)+'_sentiment.png'))
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
		connection.close()

		nowTime = time.time() - startTime
		print("Analysis of queue took "+repr(nowTime)+" secs and analyzed "+repr(num_in_queue)+" new entries.")
		if (30 - nowTime) > 0:
			time.sleep(30 - nowTime)
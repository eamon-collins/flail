#Sentiment analysis functions

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

from django.db import models, transaction, connection, IntegrityError
from django.core.exceptions import ValidationError
from fetch.models import Comment, Submission, SentimentRating, Ticker


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
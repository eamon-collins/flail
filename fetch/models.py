from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

# Create your models here.

class Submission(models.Model):
	id = models.CharField(max_length=15, unique=True, primary_key=True)
	author = models.CharField(max_length=30)
	title = models.CharField(max_length=300)
	created_utc = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
	is_self = models.BooleanField(null=True)
	score = models.IntegerField()
	edited = models.BooleanField()
	num_replies = models.IntegerField()
	distinguished = models.BooleanField(null=True)
	upvote_ratio = models.FloatField()
	subreddit = models.CharField(max_length=50)#may want to make this an enum kind of thing for easy sorting idk
	permalink = models.CharField(max_length=200)

class Comment(models.Model):
	id = models.CharField(max_length=15, unique=True, primary_key=True)
	author = models.CharField(max_length=30)
	body = models.CharField(max_length=40000)
	score = models.IntegerField()
	edited = models.BooleanField()
	num_replies = models.IntegerField()
	distinguished = models.BooleanField(null=True)
	created_utc = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
	link_id = models.CharField(max_length=15, null=True)
	parent_id = models.CharField(max_length=15, null=True)
	subreddit = models.CharField(max_length=50)#may want to make this an enum kind of thing for easy sorting idk
	permalink = models.CharField(max_length=200)



#represents one post that was judged to contain information relevant
#to an identifiable ticker
class SentimentRating(models.Model):
	id = models.AutoField(primary_key=True)
	ticker = models.ForeignKey('Ticker', on_delete=models.SET_NULL, null=True)
	created_utc = models.DateTimeField()
	sentiment_rating = models.FloatField(null=True)
	influence_rating = models.FloatField(null=True)
	source_comment = models.ForeignKey('Comment', on_delete=models.SET_NULL, null=True)
	source_submission = models.ForeignKey('Submission', on_delete=models.SET_NULL, null=True)

class Ticker(models.Model):
	id = models.AutoField(primary_key=True)
	ticker_symbol = models.CharField(max_length=5)
	keywords = models.CharField(max_length=400)
	latest_sentiment = models.FloatField(null=True)

	def set_keywords(self, x):
		self.keywords = json.dumps(x)

	def get_keywords(self):
		return json.loads(self.keywords)
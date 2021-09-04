from django.contrib import admin
from fetch.models import Comment, Submission, SentimentRating, Ticker, Tweet
# Register your models here.


admin.site.register(Comment)
admin.site.register(Submission)
admin.site.register(SentimentRating)
admin.site.register(Ticker)
admin.site.register(Tweet)
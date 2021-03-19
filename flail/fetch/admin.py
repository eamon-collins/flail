from django.contrib import admin
from fetch.models import Comment, Submission, SentimentRating, Ticker
# Register your models here.


admin.site.register(Comment)
admin.site.register(Submission)
admin.site.register(SentimentRating)
admin.site.register(Ticker)
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, \
                                 UpdateView, TemplateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from fetch.reddit import load_tickers
from os import path
from flail.settings import BASE_DIR
from fetch.models import Ticker

TICKERS = None

class HomeView(TemplateView):
    template_name = 'home/base.html'




def index(request):

	TICKERS = load_tickers(path.join(BASE_DIR,"tickerlist.json"))

	context = {'tickers':[]}
	for company, data in TICKERS.items():
		ticker_dict = {}
		#for right now this is kind of overkill when we only need the 
		#symbol, but later will have things like volume, last stock price, etc to get from this object
		tickerObject = Ticker.objects.get(ticker_symbol=data['ticker_symbol'])
		ticker_dict['name'] = tickerObject.ticker_symbol
		ticker_dict['image_path'] = "graphs/"+repr(tickerObject.id)+"_sentiment.png"
		context['tickers'].append(ticker_dict)
	return render(request, 'index.html', context)
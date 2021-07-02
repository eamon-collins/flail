# flail
Sentiment analysis gone wrong

## To Get Working
after a clone, in top level flail:
./docker/build.sh -f base
./docker/build.sh -f app
Will need to rerun the 'app' command if you change package versions/add a new package to setup.py, or even potentially just change the files

then cd ./docker and run: docker-compose up

then, if you want bash access on the running container, (for example to run the top_tickers.py script with access to the database)
docker exec -it flail /bin/bash
and then you can navigate around and run scripts like python top_tickers.py or whatever (or startBackend.py, but first check top to see if a python process is already running)


## TODO:

My plan so far is to get MVP out the door as Kaustabh says, we want to jump on this shit quick. I think minimal interface is ok, maybe generate a markdown report with matplotlib graphs or something every 5 or so minutes. However, generate these from a sliding window of at least 24 hours worth of comments, at least for reddit sources.
Keep track of the summary metrics from prior intervals (could store every hour or something) so we can have a change over time of prevailing sentiment surrounding different tickers


overall expressed sentiment: take all (relevant) comments we can get our hands on, classify as -1 or 1 and average. Easyish

Influence/Social credibility index: classify a subset of relevant comments as "socially credible" if they have influence, receive rewards, are well upvoted, etc. Binary classification and only use those deemed credible are used to form an average sentiment. Could set a low threshold as an attempt to filter out bots with no actual friends and anomolies like that. Could be hard

Weighted influence index: use a basic measure of how many people interacted (positively or negatively) with the post. Simply weight each post by that. Multiply by upvotes on reddit, weighted scoring for retweets/likes such on twitter, you get the deal. Could factor in both the danger of bot networks reposting to sway sentiment scores and the larger power of someone like Elon posting about bitcoin rather than just you or I. I think this is the best plan.
Tricky for numerous reasons, chief among them is you'd have to keep rechecking and updating information.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 16:10:06 2021

@author: user
"""

import os

import praw

import pandas as pd 

import json

import numpy as np

from flail.settings import BASE_DIR
def load_secrets():

        if not "REDDIT_KEY" in os.environ:

                with open(os.path.join(BASE_DIR, 'SECRETS.json')) as f:
                        secrets = json.load(f)

                secrets = secrets["REDDIT"]

                os.environ["REDDIT_AGENT"] = secrets["user_agent"]

                os.environ["REDDIT_ID"] = secrets["client_id"]

                os.environ["REDDIT_KEY"] = secrets["client_secret"]

load_secrets()

reddit = praw.Reddit(client_id=os.environ["REDDIT_ID"],client_secret=os.environ["REDDIT_KEY"],user_agent=os.environ["REDDIT_AGENT"],check_for_async=False)
subreddit = reddit.subreddit('wallstreetbets')
 
list = []

list_comments = []

for submission in subreddit.new():

        list.append(submission.title)

        submission.comments.replace_more(limit = None)

        for comment in submission.comments.list():

                list_comments.append(comment.body)



list1 = []

list2 = []



for i in range(1, len(list)):

        for w in range(0, len(list[i])):

                list1.append(list[i][w:w+3])

three_letter = pd.DataFrame(np.array(list1).reshape(len(list1),1))





for i in range(1, len(list)):

        for w in range(0, len(list[i])):

                list2.append(list[i][w:w+4])

four_letter = pd.DataFrame(np.array(list2).reshape(len(list2),1))

print(len(three_letter))

def threshold_counts(s, threshold=0):

    counts = s.value_counts(normalize=True, dropna=False)

    if (counts >= threshold).any():

        return False

    return True



text_file = open("ticker_NYSE.txt", "r")

Lines = text_file.read().split()



trim_3 = three_letter.apply(threshold_counts, threshold = .01)

clean_df3 = three_letter.loc[:, trim_3]

clean_df3 = clean_df3[clean_df3[0].isin(Lines)]





trim_4 = four_letter.apply(threshold_counts, threshold = .75)

clean_df4 = four_letter.loc[:, trim_4]

clean_df4 = clean_df4[clean_df4[0].isin(Lines)]



clean_df = clean_df3.append(clean_df4)

clean_df = clean_df.loc[clean_df[0].str.len()>2].drop_duplicates()

clean_df.to_csv(r'clean_df.txt')



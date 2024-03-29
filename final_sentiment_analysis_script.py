import re
import sys

import pandas as pd
import tweepy as tw
#"""
consumer_key = "oRhCAcSvL0KVUe6RX1NNGoFwB";
consumer_secret = "F1SwfaACjgkg8wONzIcWKXNibxdi2zZ0bBQ7nmKWnjp6flEL3i";
access_token = "1299382645755838464-nJgeF4AhUI11xIPOqayacqmo2li35P";
access_token_secret = "yNC4izAroCuBZYLpIQaxTPnrKICfZWN6BEHbVCX8DsMoe";

auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)

print("please select what kind of extract you want:")
print("enter 1 for hashtag related extract")
print("enter 2 for user related extract")
user_select = input()

if user_select == '1':
    print("Please enter the #hashtag with #, else file will not be populated")
    search_words = input()
    date_since = "2020-03-31"
    print("Please enter the number of tweets to be fetched")
    z = int(input())
    new_search = search_words + " -filter:retweets"
    tweets = tw.Cursor(api.search,
                       q=new_search,
                       lang="en",
                       since=date_since, tweet_mode='extended').items(z)
    users_info = [[tweet.user.id, tweet.user.created_at,
                   tweet.user.screen_name, tweet.user.location, tweet.full_text.replace('\n', ' ').encode('utf-8'),
                   tweet.favorite_count, tweet.retweet_count, tweet.user.followers_count,
                   [e['text'] for e in tweet._json['entities']['hashtags']]
                   ] for tweet in tweets]

    tweet_text = pd.DataFrame(data=users_info,
                              columns=['id', 'created_at', 'User_name', "location", 'tweet_details',
                                       'favorite', 'retweet', 'followers', 'All_hashtags'])
    fname = '_'.join(re.findall(r"#(\w+)", search_words))

    tweet_text.to_csv(r'C:\Twitter_extract\%s.csv' % (fname), index=False)

elif user_select == '2':
    print("Please enter the username you want to find with @ format, else file will not be populated")
    userID = input()

    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tw.API(auth)

    tweets = api.user_timeline(screen_name=userID,
                               count=200,
                               include_rts=False, lang="en",
                               tweet_mode='extended'
                               )

    all_tweets = []
    all_tweets.extend(tweets)
    oldest_id = tweets[-1].id
    while len(tweets) < 3000:
        tweets = api.user_timeline(screen_name=userID,
                                   count=200,
                                   include_rts=False,
                                   max_id=oldest_id - 1,
                                   tweet_mode='extended'
                                   )
        if len(tweets) == 0:
            break
        oldest_id = tweets[-1].id
        all_tweets.extend(tweets)
        print('Please wait extraction is in progress')

    outtweets = [[tweet.user.id, tweet.user.created_at,
                  tweet.user.screen_name, tweet.user.location, tweet.full_text.replace('\n', ' ').encode('utf-8'),
                  tweet.favorite_count, tweet.retweet_count, tweet.user.followers_count,
                  [e['text'] for e in tweet._json['entities']['hashtags']]
                  ] for idx, tweet in enumerate(all_tweets)]

    df_user = pd.DataFrame(outtweets, columns=['id', 'created_at', 'User_name', "location", 'tweet_details',
                                               'favorite', 'retweet', 'followers', 'All_hashtags'])
    fname = '_'.join(re.findall(r"@(\w+)", userID))
    df_user.to_csv(r'%s.csv' % (fname), index=False)
else:
    print("error in input -- exit!!!")
    sys.exit()

print("Extraction complete")
#""" #OFF for output
import string
import sys
import re
import nltk

try:
    in_fname = input("Please enter the filename without extension:")
    df_tid = pd.read_csv('C:\Twitter_extract\%s.csv' % (in_fname))
except:
    print("Incorrect file name")
    sys.exit()

hmc = int(input("How many records you want to see:"))

df_tid['tweet_details'] = df_tid['tweet_details'].replace("b'", '', regex=True)
df_tid['tweet_details'] = df_tid['tweet_details'].replace('b"', '', regex=True)


def remove_punct(text):
    text = "".join([char for char in text if char not in string.punctuation])
    text = re.sub('[0-9]+', '', text)
    return text


df_tid['tweet_details_punc_removed'] = df_tid['tweet_details'].apply(lambda x: remove_punct(x))


def tokenization(text):
    text = re.split('\W+', text)
    return text


df_tid['Tweet_tokenized'] = df_tid['tweet_details_punc_removed'].apply(lambda x: tokenization(x.lower()))

stopword = nltk.corpus.stopwords.words('english')


def remove_stopwords(text):
    text = [word for word in text if word not in stopword]
    return text


df_tid['Tweet_nonstop'] = df_tid['Tweet_tokenized'].apply(lambda x: remove_stopwords(x))

ps = nltk.PorterStemmer()


def stemming(text):
    text = [ps.stem(word) for word in text]
    return text


df_tid['Tweet_stemmed'] = df_tid['Tweet_nonstop'].apply(lambda x: stemming(x))

wn = nltk.WordNetLemmatizer()


def lemmatizer(text):
    text = [wn.lemmatize(word) for word in text]
    return text


df_tid['Tweet_lemmatized'] = df_tid['Tweet_nonstop'].apply(lambda x: lemmatizer(x))

df_tid_tokenizer = df_tid
df_tid_stich = df_tid_tokenizer['Tweet_lemmatized']

for i in range(len(df_tid_stich)):
    df_tid_stich[i] = ' '.join(df_tid_stich.loc[i])

df_tid_tokenizer['Tweet_lemma'] = df_tid_stich
del df_tid_tokenizer['Tweet_lemmatized']
df_tid_tokenizer.head(hmc)

from textblob import TextBlob

df_tid_polarity = df_tid_tokenizer.copy(deep=False)

for i in range(len(df_tid_polarity)):
    analysis = TextBlob(df_tid_polarity.loc[i, 'Tweet_lemma'])
    df_tid_polarity.loc[i, 'Tweet_polarity'] = analysis.sentiment[0]
    df_tid_polarity.loc[i, 'Tweet_subjectivity'] = analysis.sentiment[1]
    if analysis.sentiment[0] > 0:
        df_tid_polarity.loc[i, 'Polarity_indication'] = 'Positive'
    elif analysis.sentiment[0] < 0:
        df_tid_polarity.loc[i, 'Polarity_indication'] = 'Negative'
    else:
        df_tid_polarity.loc[i, 'Polarity_indication'] = 'Neutral'

df_tid_polarity.head()

#z = 400
#user_select = 1

# Weightage function for hashtag
tweet_weight = []
for i in range(0, z):
    follower_length: int = len(str(df_tid_polarity.followers[i]))
    tweet_weight.append(follower_length * df_tid_polarity.Tweet_polarity[i])

df_tid_polarity["Weight (Follower Count)"] = tweet_weight

# df_tid_polarity.head()

# retweet function for @

tweet_retweet = []
for i in range(0, z):
    retweet_length: int = len(str(df_tid_polarity.retweet[i]))
    tweet_retweet.append(retweet_length * df_tid_polarity.Tweet_polarity[i])

df_tid_polarity["Weight (No. of Retweets"] = retweet_length

if user_select == 1:
    final_df_tid_polarity = df_tid_polarity.sort_values(by=['Weight (Follower Count)'], ascending=False)
    final_df_tid_polarity.head()
    final_df_tid_polarity.to_csv('final_df_tid_polarity.csv', encoding='utf-8') #OFF

elif user_select == 2:
    final_df_tid_polarity = df_tid_polarity.sort_values(by=['Weight (No. of Retweets1'
                                                            ''], ascending=False)
    final_df_tid_polarity.head()
    final_df_tid_polarity.to_csv('final_df_tid_polarity.csv', encoding='utf-8')
"""

import matplotlib.pyplot as plt

# Pie chart
labels = ['Frogs', 'Hogs', 'Dogs', 'Logs']
sizes = [15, 30, 45, 10]
# only "explode" the 2nd slice (i.e. 'Hogs')
explode = (0, 0.1, 0, 0)  
fig1, ax1 = plt.subplots()
ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)
# Equal aspect ratio ensures that pie is drawn as a circle
ax1.axis('equal')  
plt.tight_layout()
plt.show()


"""

import matplotlib.pyplot as plt
from wordcloud import WordCloud

print("1. For Histogram details")
print("2. For All tweets Cloudword")
print("3. For negative tweets Cloudword")
print("4. For positive tweets Cloudword")
print("5. For neutral tweets Cloudword")
in_val = input()
print("Please enter y if you want to save file else n")
image_save_choice = input()

if image_save_choice == 'y':
    image_fname = input("Enter image name without extension:")
else:
    print("Only image view")

if in_val == "1":
    fig, ax = plt.subplots(figsize=(8, 6))
    df_tid_polarity['Tweet_polarity'].hist(bins=[-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1],
                                           ax=ax,
                                           color="yellow")

    plt.title("Sentiments from Tweets")
    if image_save_choice == 'y':
        plt.savefig('C:\Twitter_extract\%s.jpg' % (image_fname), dpi=300)
    else:
        plt.show()

elif in_val == "2":
    all_words = ' '.join([text for text in df_tid_polarity['tweet_details_punc_removed']])
    wordcloud = WordCloud(width=800, height=500, random_state=21, max_font_size=110).generate(all_words)
    plt.figure(figsize=(10, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    if image_save_choice == 'y':
        plt.savefig('C:\Twitter_extract\%s.jpg' % (image_fname), dpi=300)
    else:
        plt.show()

elif in_val == "3":
    normal_words = ' '.join([text for text in df_tid_polarity['Tweet_lemma'][df_tid_polarity['Tweet_polarity'] < 0]])
    wordcloud = WordCloud(width=800, height=500, random_state=21, max_font_size=110).generate(normal_words)
    plt.figure(figsize=(10, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    if image_save_choice == 'y':
        plt.savefig('C:\Twitter_extract\%s.jpg' % (image_fname), dpi=300)
    else:
        plt.show()

elif in_val == "4":
    normal_words = ' '.join([text for text in df_tid_polarity['Tweet_lemma'][df_tid_polarity['Tweet_polarity'] > 0]])
    wordcloud = WordCloud(width=800, height=500, random_state=21, max_font_size=110).generate(normal_words)
    plt.figure(figsize=(10, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    if image_save_choice == 'y':
        plt.savefig('C:\Twitter_extract\%s.jpg' % (image_fname), dpi=300)
    else:
        plt.show()

elif in_val == "5":
    normal_words = ' '.join([text for text in df_tid_polarity['Tweet_lemma'][df_tid_polarity['Tweet_polarity'] == 0]])
    wordcloud = WordCloud(width=800, height=500, random_state=21, max_font_size=110).generate(normal_words)
    plt.figure(figsize=(10, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    if image_save_choice == 'y':
        plt.savefig('C:\Twitter_extract\%s.jpg' % (image_fname), dpi=300)
    else:
        plt.show()

else:
    print("Wrong input")
#"""
from nltk import bigrams
import itertools
import collections

print("Please enter the number of common words you want to see")
in_val_cw = int(input())

print("1. for Bigram detalis")
print("2. for word count detalis")
print("3. for word count plot")
in_val = input()

if in_val == "1":
    terms_bigram = [list(bigrams(tweet)) for tweet in df_tid_tokenizer['Tweet_nonstop']]

    bigrams = list(itertools.chain(*terms_bigram))

    bigram_counts = collections.Counter(bigrams)

    bigram_counts.most_common(in_val_cw)

    bigram_df = pd.DataFrame(bigram_counts.most_common(in_val_cw),
                             columns=['bigram', 'count'])

    print(bigram_df.head(in_val_cw))

elif in_val == "2":
    words_in_tweet = [tweet.lower().split() for tweet in df_tid_tokenizer['Tweet_lemma']]

    all_words_t = list(itertools.chain(*words_in_tweet))

    counts_of_words = collections.Counter(all_words_t)

    cow_tweets = pd.DataFrame(counts_of_words.most_common(in_val_cw),
                              columns=['words', 'count'])
    print(cow_tweets.head(in_val_cw))

elif in_val == "3":
    print("Please enter y if you want to save file for word count plot else n")
    word_save_choice = input()

    words_in_tweet_p = [tweet.lower().split() for tweet in df_tid_tokenizer['Tweet_lemma']]

    all_words_t_p = list(itertools.chain(*words_in_tweet_p))

    counts_of_words_p = collections.Counter(all_words_t_p)

    cow_tweets_p = pd.DataFrame(counts_of_words_p.most_common(in_val_cw),
                                columns=['words', 'count'])

    if word_save_choice == 'y':
        image_fname = input("Enter image name without extension:")
    else:
        print("Only image view")

    fig, ax = plt.subplots(figsize=(8, 8))

    cow_tweets_p.sort_values(by='count').plot.barh(x='words',
                                                   y='count',
                                                   ax=ax,
                                                   color="purple")

    ax.set_title("Common Words Found in Tweets (Including All Words)")

    if word_save_choice == 'y':
        plt.savefig('C:\Twitter_extract\%s.jpg' % (image_fname), dpi=300)
    else:
        plt.show()
else:
    print("Wrong choice entered")

from sklearn.feature_extraction.text import CountVectorizer

df_tid_formvector = df_tid_tokenizer.copy(deep=False)

vectorizer = CountVectorizer()
for i in range(len(df_tid_tokenizer)):
    v_text = df_tid_formvector.loc[i, 'Tweet_stemmed']
    vectorizer.fit(v_text)
    text = list((vectorizer.vocabulary_).items())
    df_tid_formvector.loc[i, 'Tweet_vcetor_list'] = str(text)
    vector = vectorizer.transform(v_text)
    print(vector.shape)
    print(type(vector))
    print(vector.toarray())

from sklearn.feature_extraction.text import TfidfVectorizer

vector_presentation_list = []

for i in range(len(df_tid_tokenizer)):
    l_text = df_tid_tokenizer.loc[i, 'Tweet_lemma']
    vector_presentation_list.append(l_text)
    print(vector_presentation_list)

vectorizer = TfidfVectorizer()

vectorizer.fit(vector_presentation_list)
vector = vectorizer.transform(vector_presentation_list)
print(vector.shape)
print(type(vector))
print(vector.toarray())

import sys

outfname = input("Please assign name without extension to the file before loading: ")

print("Please enter your choice which file you want to load:")
print("1.Preprocessed file")
print("2.Polarity details")
print("3.Vector details")

your_selection = input()

if your_selection == "1":
    df_tid_tokenizer.to_csv(r'C:\Twitter_extract\%s.csv' % (outfname), index=False)
elif your_selection == "2":
    final_df_tid_polarity.to_csv(r'C:\Twitter_extract\%s.csv' % (outfname), index=False)
elif your_selection == "3":
    df_tid_formvector.to_csv(r'C:\Twitter_extract\%s.csv' % (outfname), index=False)
else:
    print("wrong choice entered")
    sys.exit()

print("Loading complete")
#""" #OFF

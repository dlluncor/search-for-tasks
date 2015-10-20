import json, sys, time, twitter
from functools import partial
from models import Tweet, User
from urllib2 import URLError
from httplib import BadStatusLine

# NOTICE: Go to http://dev.twitter.com/apps/new to create an app and get values
# for these credentials, which you'll need to provide in place of these
# empty string values that are defined as placeholders.
# See https://dev.twitter.com/docs/auth/oauth for more information
# on Twitter's OAuth implementation.

CONSUMER_KEY = 'BVVaueNzf8yr9Z4e4GozyXd1w'
CONSUMER_SECRET = 'ZF8ZAK3KiMRm5FDnAgUgZQxm3nbNkmlXMmOSu1PkDhSSmRAG9c'
OAUTH_TOKEN = '3322576890-FljbPNB66U36q9hTls8FKHNszOlnNiIdc8m2ZqS'
OAUTH_TOKEN_SECRET = 'HIVNlfcpedyX6yfc55AxyFk6mzcx2ivgducqlNhJcWAsM'
auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

twitter_api = twitter.Twitter(auth=auth)

def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw):
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):

        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.')
            raise e

        # See https://dev.twitter.com/docs/error-codes-responses for common codes
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)')
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)')
            return None
        elif e.e.code == 429:
            print('Encountered 429 Error (Rate Limit Exceeded)')
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...")
                time.sleep(60*15 + 5)
                print('...ZzZ...Awake now and trying again.')
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered %i Error. Retrying in %i seconds' % (e.e.code, wait_period))
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    wait_period = 5
    error_count = 0
    while True:
        try:
            response = twitter_api_func(*args, **kw)
            time.sleep(wait_period)
            return response
        except twitter.api.TwitterHTTPError, e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError, e:
            error_count += 1
            print("URLError encountered. Continuing.")
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.")
                raise
        except BadStatusLine, e:
            error_count += 1
            print("BadStatusLine encountered. Continuing.")
            if error_count > max_errors:
                # Sample usage
                print("Too many consecutive errors...bailing out.")
                raise

def search(q, count=1):
    if not count > 0:
        return

    items_per_request = 10
    kwargs = {
        #'geocode': '37.4238253802915,-122.0829009197085,1000mi', # seems wrong usage
        'lang': 'en',
        'q': q,
    }

    tweets = []
    while count > 0:
        print("remain %s statuses" % count)
        if count < items_per_request:
            items_per_request = count

        kwargs['count'] = items_per_request

        # twitter_api.search.tweets(q='insurance', count=1,geocode='37.4238253802915,-122.0829009197085,1000mi', lang='en')
        search_results = make_twitter_request(twitter_api.search.tweets, **kwargs)

        print(json.dumps(search_results, indent=2))
        if not search_results:
            break

        statuses = search_results['statuses']
        tweets += statuses

        try:
            next_results = search_results['search_metadata'].get('next_results', None)

            if not next_results:
                break
        except KeyError, e:
            print("Oooooops, we got an error!")
            break

        kwargs = dict([kv.split('=') for kv in next_results[1:].split("&")])
        count -= items_per_request

    return tweets
    print("DONE")

def get_user_profile(screen_name=None, users_id=None):
    if screen_name is None and users_id is None:
        return

    kwargs = {
        'skip_status': True,
        'include_user_entities': False
    }
    users = {}

    if screen_name:
        kwargs['screen_name'] = screen_name
    else:
        kwargs['user_id'] = user_id

    fetch_profile = partial(make_twitter_request, twitter_api.users.show, **kwargs)
    response = fetch_profile()

    return response

def get_followers(screen_name=None, user_id=None, save_in_time=True):
    if screen_name is None and users_id is None:
        return

    kwargs = {
        'skip_status': True,
        'include_user_entities': False,
        'count': 200
    }

    fetch_followers = partial(make_twitter_request, twitter_api.followers.list, **kwargs)

    followers = []
    cursor = -1
    while cursor != 0:
        if screen_name:
            response = fetch_followers(screen_name=screen_name, cursor=cursor)
        else:
            response = fetch_followers(user_id=user_id, cursor=cursor)

        if response:
            if save_in_time:
                save_users(response['users'])
            else:
                followers += response['users']
            cursor = response['next_cursor']

            print("Fetch {0} total followers for {1}".format(len(followers), (screen_name or user_id)))
        else:
            break

    return followers

# https://dev.twitter.com/rest/reference/get/statuses/user_timeline
# max_count should less than 3200
def harvest_user_timeline(screen_name=None, user_id=None, max_count=2000, save_in_time=True):
    if screen_name is None and users_id is None:
        return

    kwargs = {
        'count': 200,
        'trim_user': True,
        'include_rts': True,
        'since_id': 1
    }
    if screen_name:
        kwargs['screen_name'] = screen_name
    else:
        kwargs['user_id'] = user_id

    fetch_tweets = partial(make_twitter_request, twitter_api.statuses.user_timeline, **kwargs)

    max_id = None
    results = []
    while len(results) < max_count:
        if max_id:
            tweets = fetch_tweets(max_id=max_id)
        else:
            tweets = fetch_tweets()

        if not tweets:
            break

        if save_in_time:
            save_tweets(tweets)
        else:
            results += tweets

        max_id = min(tweet['id'] for tweet in tweets) - 1
        print('Fetch total {0} tweets'.format(len(results)))

    return results

# tweets are list of tweet in dict
def save_tweets(tweets):
    print("save %s tweets" % len(tweets))
    for item in tweets:
        tweet = Tweet(**item)
        tweet.save()
        #print(json.dumps(item, indent=4))

# tweets are list of tweet in dict
def save_users(users):
    print("save %s users" % len(users))
    for item in users:
        save_user(item)

def save_user(item):
    user = User(**item)
    user.save()
    #print(json.dumps(item, indent=4))

# See https://dev.twitter.com/rest/reference/get/search/tweets for
# twitter_api.search.tweets
#response = search(q='asdfasdfassadfsadfsadd', count=95)
#response = get_user_profile(twitter_api, screen_name='earthquakessf')
#rint(response)
#followers = get_follower(screen_name='usgsearthquakes')
#print(json.dumps(followers, indent=2))
#tweets = harvest_user_timeline(screen_name='kainoa_devices')
#print(json.dumps(tweets[-1], indent=2))

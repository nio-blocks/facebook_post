import requests
import json
from urllib.parse import quote_plus
import oauth2 as oauth
from requests_oauthlib import OAuth1

from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties.object import ObjectProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.metadata.properties.expression import ExpressionProperty
from nio.metadata.properties.string import StringProperty
from nio.modules.threading.imports import Thread


POST_URL = ("https://graph.facebook.com/{0}/feed?"
            "access_token={1}")
TOKEN_URL_FORMAT = ("https://graph.facebook.com/oauth"
                    "/access_token?client_id={0}&client_secret={1}"
                    "&grant_type=client_credentials")
MAX_TWEET_LEN = 140


class FacebookCreds(PropertyHolder):

    """ Property holder for Facebook OAuth credentials.

    """
    consumer_key = StringProperty()
    app_secret = StringProperty()
    oauth_token = StringProperty()
    oauth_token_secret = StringProperty()


@Discoverable(DiscoverableType.block)
class FacebookPost(Block):
    
    message = ExpressionProperty(default='')
    feed_id = StringProperty(default='me')
    creds = ObjectProperty(FacebookCreds)
    
    def __init__(self):
        super().__init__()
        self._auth = None
        self._access_token = None
    
    def start(self):
        super().start()
        self._authenticate()

    def process_signals(self, signals):
        for s in signals:
            try:
                status = self.message(s)
                if len(status) > MAX_TWEET_LEN:
                    raise RuntimeError(
                        "Status update exceeds {0} character limit".format(
                            MAX_TWEET_LEN))
            except Exception as e:
                self._logger.error(
                    "Status evaluation failed: {0}: {1}".format(
                        type(e).__name__, str(e))
                )
                continue
                
            data = {'status': status}
            self._post_tweet(data)

    def _post_tweet(self, payload):
        url = POST_URL.format(self.feed_id, self._access_token)
        print("THE URL", url)
        response = requests.post(url, data=payload)
                                 
        status = response.status_code
        if status != 200:
            self._logger.error(
                "Facebook post failed with status {0}".format(status)
            )
        else:
            self._logger.debug(
                "Posted '{0}' to Facebook!".format(data['status'])
            )

    def _authenticate(self):
        """ Generates and records the access token for pending requests.

        """
        if self.creds.consumer_key is None or self.creds.app_secret is None:
            self._logger.error("You need a consumer key and app secret, yo")
        else:
            self._access_token = self._request_access_token()

    def _request_access_token(self):
        """ Request an access token directly from facebook.

        Args:
            None

        Returns:
            token (str): The access token, which goes on the end of a request.

        """
        resp = requests.get(TOKEN_URL_FORMAT.format(
            self.creds.consumer_key, self.creds.app_secret)
        )
        status = resp.status_code

        # If the token request fails, try to use the configured app id
        # and secret. This probably won't work, but the docs say that it
        # should. for more info, see:
        # https://developers.facebook.com/docs/facebook-login/access-tokens
        token = "%s|%s" % (self.creds.consumer_key, self.creds.app_secret)
        if status == 200:
            token = resp.text.split('access_token=')[1]
        else:
            self._logger.error(
                "Facebook token request failed with status %d" % status
            )
        return token

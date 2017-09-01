from urllib.parse import quote_plus

import requests
from nio import TerminatorBlock
from nio.properties import (ObjectProperty, PropertyHolder, Property,
                            StringProperty, VersionProperty)


POST_URL = ("https://graph.facebook.com/{0}/feed?"
            "message={1}&access_token={2}")
PERMISSIONS_URL = ("https://graph.facebook.com/{0}/permissions?"
                   "access_token={1}")
TOKEN_URL_FORMAT = ("https://graph.facebook.com/oauth"
                    "/access_token?client_id={0}&client_secret={1}"
                    "&grant_type=client_credentials")
MAX_TWEET_LEN = 140


class FacebookCreds(PropertyHolder):

    """ Property holder for Facebook OAuth credentials.

    """
    consumer_key = StringProperty(title='Consumer Key',
                                  default='[[FACEBOOK_CONSUMER_KEY]]')
    app_secret = StringProperty(title='App Secret',
                                default='[[FACEBOOK_APP_SECRET]]')


class FacebookPost(TerminatorBlock):

    version = VersionProperty("1.0.0")
    message = Property(title='Message', default='')
    feed_id = StringProperty(title='Feed ID (user, group, etc.)', default='me')
    creds = ObjectProperty(FacebookCreds, title='Credentials')

    def __init__(self):
        super().__init__()
        self._auth = None
        self._access_token = None

    def start(self):
        super().start()
        self._authenticate()

    def process_signals(self, signals):
        if self._check_permissions():
            for s in signals:
                try:
                    message = self.message(s)
                except Exception as e:
                    self.logger.exception("Message evaluation failed:")
                    continue
                self._post_to_feed(quote_plus(message))
        else:
            self.logger.error(
                "Insufficient permissions for id: {0}".format(self.feed_id())
            )

    def _post_to_feed(self, message):
        url = POST_URL.format(self.feed_id(), message, self._access_token)
        response = requests.post(url)
        status = response.status_code

        if status != 200:
            self.logger.error(
                "Facebook post failed with status {0}".format(status)
            )
        else:
            self.logger.debug("Posted to Facebook!")

    def _authenticate(self):
        """ Generates and records the access token for pending requests.

        """
        if self.creds().consumer_key() is None or \
                self.creds().app_secret() is None:
            self.logger.error("You need a consumer key and app secret")
        else:
            self._access_token = self._request_access_token()

    def _check_permissions(self):
        result = False
        url = PERMISSIONS_URL.format(self.feed_id(), self._access_token)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get('data')[0] or {}
            if data.get('publish_actions') == 1:
                result = True
        return result

    def _request_access_token(self):
        """ Request an access token directly from facebook.

        Args:
            None

        Returns:
            token (str): The access token, which goes on the end of a request.

        """
        resp = requests.get(TOKEN_URL_FORMAT.format(
            self.creds().consumer_key(), self.creds().app_secret())
        )
        status = resp.status_code

        # If the token request fails, try to use the configured app id
        # and secret. This probably won't work, but the docs say that it
        # should. for more info, see:
        # https://developers.facebook.com/docs/facebook-login/access-tokens
        token = "{}.{}".format(
            self.creds().consumer_key(), self.creds().app_secret())
        if status == 200:
            token = resp.text.split('access_token=')[1]
        else:
            self.logger.error(
                "Facebook token request failed with status %d" % status
            )
        return token

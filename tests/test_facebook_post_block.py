import responses
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase

from ..facebook_post_block import FacebookPost


class SetPublishAction(object):

    def setUp(self):
        super().setUp()
        responses.add(
            responses.GET,
            'https://graph.facebook.com/me/permissions?access_token=mytoken',
            json={
                'data': [{'publish_actions': 1}]
            },
        )


class UnsetPublishAction(object):

    def setUp(self):
        super().setUp()
        responses.add(
            responses.GET,
            'https://graph.facebook.com/me/permissions?access_token=mytoken',
            json={
                'data': [{'publish_actions': 0}]
            },
        )


class FacebookPostTest(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        responses.add(
            responses.GET,
            (
                'https://graph.facebook.com/oauth/access_token?'
                'client_id=[[FACEBOOK_CONSUMER_KEY]]&'
                'client_secret=[[FACEBOOK_APP_SECRET]]&'
                'grant_type=client_credentials'
            ),
            body='access_token=mytoken',
        )
        responses.add(responses.POST, 'https://graph.facebook.com/me/feed')


class TestFacebookPostWithPermissions(SetPublishAction, FacebookPostTest):

    @responses.activate
    def test_process_post(self):
        signals = [Signal({'foo': 'test signal'})]
        blk = FacebookPost()
        self.configure_block(blk, {
            "message": "{{$foo}}"
        })
        blk.start()
        blk.process_signals(signals)
        blk.stop()
        self.assertEqual(len(responses.calls), 3)
        self.assertTrue('test+signal' in responses.calls[2].request.url)

    @responses.activate
    def test_process_multiple(self):
        signals = [
            Signal({'foo': 'test signal'}),
            Signal({'foo': 'another test'}),
            Signal({'foo': 'one more time'})
        ]
        blk = FacebookPost()
        self.configure_block(blk, {
            "message": "{{$foo}}"
        })
        blk.start()
        blk.process_signals(signals)
        blk.stop()
        self.assertEqual(len(responses.calls), 5)
        self.assertTrue('test+signal' in responses.calls[2].request.url)
        self.assertTrue('another+test' in responses.calls[3].request.url)
        self.assertTrue('one+more+time' in responses.calls[4].request.url)


class TestFacebookPostWithoutPermissions(UnsetPublishAction, FacebookPostTest):

    @responses.activate
    def test_permission_fail(self):
        signals = [
            Signal({'foo': 'test signal'}),
            Signal({'foo': 'another test'}),
            Signal({'foo': 'one more time'})
        ]
        blk = FacebookPost()
        self.configure_block(blk, {
            "message": "{{$foo}}"
        })
        blk.start()
        blk.process_signals(signals)
        blk.stop()
        self.assertEqual(len(responses.calls), 2)

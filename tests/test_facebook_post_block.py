from ..facebook_post_block import FacebookPost
import json
from urllib.parse import quote_plus
from unittest.mock import patch
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase


class TestFacebookPost(NIOBlockTestCase):

    @patch.object(FacebookPost, '_authenticate')
    @patch.object(FacebookPost, '_post_to_feed')
    @patch.object(FacebookPost, '_check_permissions')
    def test_process_post(self, mock_check, mock_post, mock_auth):
        mock_check.return_value = True
        signals = [Signal({'foo': 'test signal'})]
        blk = FacebookPost()
        self.configure_block(blk, {
            "message": "{{$foo}}"
        })
        blk.start()
        mock_auth.assert_called_once()

        blk.process_signals(signals)
        mock_post.assert_called_once_with(quote_plus(signals[0].foo))
        blk.stop()

    @patch.object(FacebookPost, '_authenticate')
    @patch.object(FacebookPost, '_post_to_feed')
    @patch.object(FacebookPost, '_check_permissions')
    def test_process_multiple(self, mock_check, mock_post, mock_auth):
        mock_check.return_value = True
        signals = [
            Signal({'foo': 'test signal'}),
            Signal({'foo': 'another test'}),
            Signal({'foo': 'one more time'})
        ]
        blk = FacebookPost()
        # self.configure_block(blk, {
        #     "message": "{{$foo}}"
        # })
        blk.start()
        mock_auth.assert_called_once()
        blk.process_signals(signals)
        self.assertEqual(mock_post.call_count, len(signals))

        blk.stop()

    @patch.object(FacebookPost, '_authenticate')
    @patch.object(FacebookPost, '_post_to_feed')
    @patch.object(FacebookPost, '_check_permissions')
    def test_permission_fail(self, mock_check, mock_post, mock_auth):
        mock_check.return_value = False
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
        mock_auth.assert_called_once()
        blk.process_signals(signals)
        self.assertEqual(mock_post.call_count, 0)

        blk.stop()

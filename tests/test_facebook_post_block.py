import json
from unittest.mock import patch
from twitter_post.twitter_post_block import TwitterPost
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase


class TestTwitterPost(NIOBlockTestCase):
    
    @patch('twitter_post.twitter_post_block.TwitterPost._authorize')
    @patch('twitter_post.twitter_post_block.TwitterPost._post_tweet')
    def test_process_post(self, mock_post, mock_auth):
        signals = [Signal({'foo': 'test signal'})]
        blk = TwitterPost()
        self.configure_block(blk, {
            "status": "{{$foo}}"
        })
        blk.start()
        mock_auth.assert_called_once()

        blk.process_signals(signals)
        mock_post.assert_called_once_with({'status': signals[0].foo})
        blk.stop()

    @patch('twitter_post.twitter_post_block.TwitterPost._authorize')
    @patch('twitter_post.twitter_post_block.TwitterPost._post_tweet')
    def test_process_multiple(self, mock_post, mock_auth):
        signals = [
            Signal({'foo': 'test signal'}),
            Signal({'foo': 'another test'}),
            Signal({'foo': 'one more time'})
        ]
        blk = TwitterPost()
        self.configure_block(blk, {
            "status": "{{$foo}}"
        })
        blk.start()
        mock_auth.assert_called_once()
        blk.process_signals(signals)
        self.assertEqual(mock_post.call_count, len(signals))
        
        blk.stop()
        
                             
                             

import unittest,io,urllib.error
from unittest.mock import patch
from beesky.agent import AgentService,_post_json
class ClockTests(unittest.TestCase):
 def test_desktop_clock_offset_is_applied_to_snapshot(self):
  service=AgentService(lambda:[],cloud_url='https://cloud.invalid',key='private-fixture-key',site='server-site')
  with patch('beesky.agent.time.time',return_value=1065),patch('beesky.agent._get_json',return_value={'serverTime':1000}),patch('beesky.agent._post_json') as post:
   self.assertTrue(service._deliver_snapshot([]));self.assertEqual(post.call_args.args[1]['ts'],1000)
 def test_cloud_validation_error_is_readable_and_redacts_credentials(self):
  error=urllib.error.HTTPError('https://cloud.invalid',400,'Bad Request',{'Content-Type':'application/json'},io.BytesIO(b'{"detail":"Timestamp invalid: private-fixture-key"}'))
  with patch('beesky.agent.urllib.request.build_opener') as opener:
   opener.return_value.open.side_effect=error
   with self.assertRaises(ValueError) as caught:_post_json('https://cloud.invalid',{},'private-fixture-key')
   self.assertIn('Timestamp invalid',str(caught.exception));self.assertNotIn('private-fixture-key',str(caught.exception))
if __name__=='__main__':unittest.main()

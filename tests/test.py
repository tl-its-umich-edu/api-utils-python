# -*- coding: future_fstrings -*- 

import logging, json, unittest, os, sys

from dotenv import load_dotenv

from datetime import datetime

from autologging import logged, traced

# Add this path first so it picks up the newest changes without having to rebuild
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, this_dir + "/..")
from umich_api.api_utils import ApiUtil

load_dotenv(dotenv_path=this_dir + "/.env")
logging.basicConfig(level=os.getenv("log_level", "DEBUG"))

@logged
class TestApiCalls(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.url = os.getenv("url")
        self.client_id = os.getenv("client_id")
        self.secret = os.getenv("secret")
        self.apiutil = ApiUtil(self.url, self.client_id, self.secret)
        # This line is needed so pylint doesn't complain about this variable not existing.
        self.__log = self.__log
        self.__log.info("URL is %s" % self.url)

    # Tests API mcommunity calls
    def test_mcommunity(self):
        uniqname = "uniqname"
        self.assertEqual(self.apiutil.api_call(f"MCommunity/People/{uniqname}", "mcommunity").status_code, 200)

    def test_token_renewal(self):
        uniqname = "uniqname"
        client_scope = "mcommunity"
        with self.assertLogs(level="INFO") as cm:
            api_result = self.apiutil.api_call(f"MCommunity/People/{uniqname}", client_scope)
        # Asserts that it gets a token, need to match the substring against all output. It will contain a time
        self.assertTrue(any(f'INFO:umich_api.api_utils.ApiUtil:The token for {client_scope} will expire at' for elem in cm.output))
        self.assertEqual(api_result.status_code, 200)
        # Expire the token, verify this still works by checking the debug messages
        self.apiutil.tokens[client_scope]['expires_time'] = datetime.now()
        with self.assertLogs(level="INFO") as cm:
            api_result = self.apiutil.api_call(f"MCommunity/People/{uniqname}", client_scope)
        # This is the message that the token was renewed
        self.assertIn(f'INFO:umich_api.api_utils.ApiUtil:Token for {client_scope} expired, renewing token', cm.output)
        # Assert this api resulted in 200
        self.assertEqual(api_result.status_code, 200)

    # Tests API pagination
    def test_pagination(self):
        # Try a course site that has no next page
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/1/users",'canvasreadonly')
        next = self.apiutil.get_next_page(resp)
        self.assertEqual(next,None)

        #Now try one that does have a next page
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/245665/users",'canvasreadonly')
        next = self.apiutil.get_next_page(resp)
        self.assertEqual(self.apiutil.get_next_page(resp),{'page': ['2'], 'per_page': ['10']})
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/245664/users",'canvasreadonly', payload=next)
        self.__log.debug(resp)
        
    # Tests API canvasreadonly calls
    def test_canvasreadonly(self):
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/brand_variables",'canvasreadonly')
        self.assertEqual(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()

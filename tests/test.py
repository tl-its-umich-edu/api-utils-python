# -*- coding: future_fstrings -*- 

from umich_api.api_utils import ApiUtil
import logging, json, unittest, os

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

logging.basicConfig(level="WARNING")

class TestApiCalls(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.url = os.getenv("url")
        self.client_id = os.getenv("client_id")
        self.secret = os.getenv("secret")
        print ("URL is %s" % self.url)

    def test_mcommunity(self):
        mcommunity_api = ApiUtil(self.url, self.client_id, self.secret, "mcommunity")
        uniqname = "uniqname"
        self.assertEqual(mcommunity_api.api_call(f"MCommunity/People/{uniqname}").status_code, 200)

    def test_canvasreadonly(self):
        canvas_api = ApiUtil(self.url, self.client_id, self.secret, "canvasreadonly")
        self.assertEqual(canvas_api.api_call(f"aa/CanvasReadOnly/brand_variables").status_code, 200)

if __name__ == '__main__':
    unittest.main()
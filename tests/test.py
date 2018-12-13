# -*- coding: future_fstrings -*- 

from umich_api.api_utils import ApiUtil
import logging, json, unittest, os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level="TRACE")

load_dotenv(dotenv_path=os.path.dirname(os.path.abspath(__file__))+"/.env")

class TestApiCalls(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.url = os.getenv("url")
        self.client_id = os.getenv("client_id")
        self.secret = os.getenv("secret")
        self.apiutil = ApiUtil(self.url, self.client_id, self.secret)
        print ("URL is %s" % self.url)

    def test_mcommunity(self):
        uniqname = "uniqname"
        self.assertEqual(self.apiutil.api_call(f"MCommunity/People/{uniqname}", "mcommunity").status_code, 200)

    def test_pagination(self):
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/1/users",'canvasreadonly')
        logger.info(resp.headers)

    def test_canvasreadonly(self):
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/brand_variables",'canvasreadonly')
        self.assertEqual(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()

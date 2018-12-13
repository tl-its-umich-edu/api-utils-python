# -*- coding: future_fstrings -*- 

from umich_api.api_utils import ApiUtil
import logging, json, unittest, os

from dotenv import load_dotenv

from autologging import logged, traced

logging.basicConfig(level="TRACE")

load_dotenv(dotenv_path=os.path.dirname(os.path.abspath(__file__))+"/.env")

@logged
class TestApiCalls(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.url = os.getenv("url")
        self.client_id = os.getenv("client_id")
        self.secret = os.getenv("secret")
        self.apiutil = ApiUtil(self.url, self.client_id, self.secret)
        self.__log.info("URL is %s" % self.url)

    def test_mcommunity(self):
        uniqname = "uniqname"
        self.assertEqual(self.apiutil.api_call(f"MCommunity/People/{uniqname}", "mcommunity").status_code, 200)

    def test_pagination(self):
        # Try a course site that has no next page
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/1/users",'canvasreadonly')
        next = self.apiutil.get_next_page(resp)
        self.assertEqual(next,None)
        #Now try one that does have a next page
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/245664/users",'canvasreadonly')
        next = self.apiutil.get_next_page(resp)
        self.assertEqual(self.apiutil.get_next_page(resp),{'page': ['2'], 'per_page': ['10']})
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/courses/245664/users",'canvasreadonly', payload=next)
        self.__log.debug(resp)
        
        

    def test_canvasreadonly(self):
        resp = self.apiutil.api_call(f"aa/CanvasReadOnly/brand_variables",'canvasreadonly')
        self.assertEqual(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()

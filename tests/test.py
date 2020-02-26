# -*- coding: future_fstrings -*- 

import logging, json, unittest, os, sys

from dotenv import load_dotenv


from autologging import logged


# Add this path first so it picks up the newest changes without having to rebuild
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, this_dir + "/..")
from umich_api.api_utils import ApiUtil

load_dotenv(dotenv_path=this_dir + "/.env")
logging.basicConfig(level=os.getenv("log_level", "TRACE"))

@logged
class TestApiCalls(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.url = os.getenv("url")
        cls.client_id = os.getenv("client_id")
        cls.secret = os.getenv("secret")
        cls.apiutil = ApiUtil(cls.url, cls.client_id, cls.secret)
        # This line is needed so pylint doesn't complain about this variable not existing.
        cls.__log = cls.__log
        cls.__log.info("URL is %s" % cls.url)

    # Tests API mcommunity calls
    def test_mcommunity(self):
        uniqname = "uniqname"
        self.assertEqual(self.apiutil.api_call(f"MCommunity/People/{uniqname}", "mcommunity").status_code, 200)

    # Tests API mcommunity calls
    def test_umscheduleofclasses(self):
        self.assertEqual(self.apiutil.api_call(f"Curriculum/SOC/Terms", "umscheduleofclasses").status_code, 200)

    # TODO replace this API with more genric placement exam api
    def test_placement_batch_upload(self):
        payload = {'putPlcExamScore': {'Student': [{'Form': 'S', 'ID': 'asffs', 'GradePoints': '34.4'},
                                        {'Form': 'S', 'ID': 'rrrs', 'GradePoints': '40.4'}]}}

        headers = [{"Content-Type" : "application/json"}]
        call = self.apiutil.api_call(f"aa/SpanishPlacementScores/Scores",
                                     "spanishplacementscores", "PUT",  json.dumps(payload), api_specific_headers=headers)
        self.__log.info(call.text)
        self.assertEqual(call.status_code, 200)
        resp_body = json.loads(call.text)
        len__ = list(resp_body['putPlcExamScoreResponse']['putPlcExamScoreResponse']['Success']).__len__()
        self.assertEqual(2, len__)

    def test_token_renewal(self):
        uniqname = "uniqname"
        client_scope = "mcommunity"
        token_url = self.apiutil.scopes.get(client_scope, {}).get("token_url")
        api_result = self.apiutil.api_call(f"MCommunity/People/{uniqname}", client_scope)
        self.assertEqual(api_result.status_code, 200)
        # Expire the token, verify this still works by checking the debug messages
        self.assertTrue(self.apiutil.expire_token(client_scope=client_scope))
        # This test can't run in python 2, just skip it as it's just extra protection
        if sys.version_info >= (3, 4):
            with self.assertLogs(level="INFO") as cm:
                api_result = self.apiutil.api_call(f"MCommunity/People/{uniqname}", client_scope)
            # This is the message that the token was renewed
            self.assertIn(f'INFO:umich_api.api_utils.ApiUtil:Token for {token_url}/{client_scope} expired, renewing token', cm.output)
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

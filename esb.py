from ratelimit import limits, sleep_and_retry
import requests, os

from dotenv import load_dotenv
load_dotenv()

class EsbUtil:
    access_token = ""

    def __init__(self, base_url, client_id, client_secret, client_scope, limits_calls=1, limits_period=60):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_scope = client_scope
        self.api_call = sleep_and_retry(limits(calls=limits_calls, period=limits_period)(self._api_call))

    def _api_call(self, api_call):
        print ("api_call")
        if (not self.access_token):
            raise Exception("No access token yet, must call get_access_token first")

        headers = {
            "accept" : "application/json",
            "Authorization" : f"Bearer {self.access_token}",
            "x-ibm-client-id" : self.client_id,
        }
        resp = requests.get(f"{self.base_url}/{api_call}", headers=headers)
        if (resp.ok):
            print (resp.text)
        else:
            print (resp.status_code)
            print (resp.text)
    

    def get_access_token(self):
        print ("get_access_token")
        payload = {
            "grant_type" : "client_credentials",
            "client_id" : self.client_id,
            "client_secret" : self.client_secret,
            "scope" : self.client_scope,
        }
        headers = {
            "accept" : "application/json",
        }
        resp = requests.post(f"{self.base_url}/aa/oauth2/token", data=payload, headers=headers)
        try:
            if (resp.ok):
                self.access_token = resp.json().get('access_token')
        except (ValueError):
            print ("Error obtaining access token with credentials")

url = os.getenv("url")
id = os.getenv("id")
secret = os.getenv("secret")
scope = os.getenv("scope")

esb = EsbUtil(url, id, secret, scope, limits_calls=1)
esb.get_access_token()
for i in range(0, 50):
    esb.api_call("Curriculum/SOC/Terms")
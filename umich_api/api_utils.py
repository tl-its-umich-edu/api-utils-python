from ratelimit import limits, sleep_and_retry
import requests, logging

log = logging.getLogger(__name__)

class ApiUtil():
    access_token = ""

    def __init__(self, base_url, client_id, client_secret, client_scope, limits_calls=200, limits_period=60):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_scope = client_scope
        self.api_call = sleep_and_retry(limits(calls=limits_calls, period=limits_period)(self._api_call))

    def _api_call(self, api_call):
        log.debug("api_call")
        if (not self.access_token):
            raise Exception("No access token yet, must call get_access_token first")

        headers = {
            "accept" : "application/json",
            "Authorization" : f"Bearer {self.access_token}",
            "x-ibm-client-id" : self.client_id,
        }
        log.info(headers)
        resp = requests.get(f"{self.base_url}/{api_call}", headers=headers)
        if (resp.ok):
            log.debug(resp.text)
        else:
            log.debug(resp.status_code)
            log.debug(resp.text)
    

    def get_access_token(self, token_url):
        log.debug ("get_access_token")
        payload = {
            "grant_type" : "client_credentials",
            "client_id" : self.client_id,
            "client_secret" : self.client_secret,
            "scope" : self.client_scope,
        }
        headers = {
            "accept" : "application/json",
        }
        resp = requests.post(f"{self.base_url}/{token_url}", data=payload, headers=headers)
        try:
            if (resp.ok):
                self.access_token = resp.json().get('access_token')
        except (ValueError):
            log.error ("Error obtaining access token with credentials")
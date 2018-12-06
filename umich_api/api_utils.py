from ratelimit import limits, sleep_and_retry
import requests, logging, json, pkg_resources

log = logging.getLogger(__name__)

class ApiUtil():
    access_token = ""

    def __init__(self, base_url: str, client_id: str, client_secret: str, client_scope: str, api_json: str = None):
        """[Init method used to create an Api Class for making api calls]
        
        :param base_url: Base URL of the API service
        :type base_url: str
        :param client_id: Client ID of the application
        :type client_id: str
        :param client_secret: Secret of the application
        :type client_secret: str
        :param client_scope: Client scope, must be present in the api_json file
        :type client_scope: str
        :param api_json: API file defining all JSON limits and calls, defaults to None because it will use the default
        :param api_json: str, optional
        :raises Exception: If this cannot be configured with parameters used
        """

        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_scope = client_scope

        # If the user doesn't pass an alternate API file use the included one
        if not api_json:
            api_json = pkg_resources.resource_filename(__name__, 'apis.json')

        with open(api_json, encoding='utf-8') as api_file:
            apis = json.loads(api_file.read())

        if client_scope in apis: 
            api = apis.get(client_scope)
            self.token_url = api.get('token_url')
            self.api_call = sleep_and_retry(limits(calls=api.get('limits_calls'), period=api.get('limits_period'))(self._api_call))
            self.get_access_token(self.token_url)
        else: 
            raise Exception(f"Scope {client_scope} not in known API dict")

    def _api_call(self, api_call:str, method:str="GET"):
        """Calls the specified API with the optional method
        
        :param api_call: API to call on this application
        :type api_call: str
        :param method: Which HTTP method to use, defaults to "GET"
        :param method: str, optional
        :raises Exception: No Access Token
        """

        log.debug("api_call")
        if (not self.access_token):
            raise Exception("No access token yet, must call get_access_token first")

        headers = {
            "accept" : "application/json",
            "Authorization" : f"Bearer {self.access_token}",
            "x-ibm-client-id" : self.client_id,
        }
        log.info(headers)
        if method == "GET":
            resp = requests.get(f"{self.base_url}/{api_call}", headers=headers)
        # TODO Implement/Test other methods, currently all we are doing is GET
        else:
            raise Exception("Methods other than GET are currently unsupported")
            
        if (resp.ok):
            return resp
        else:
            log.debug(resp.status_code)
            log.debug(resp.text)

    def get_access_token(self, token_url:str):
        """Retrieves an access token from the specified URL
        
        :param token_url: Full URL to retrieve access token
        :type token_url: str
        """

        
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

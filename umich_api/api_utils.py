install_aliases()

from builtins import *
from ratelimit import limits, sleep_and_retry
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

from autologging import logged, traced

import requests, json, pkg_resources

from collections import defaultdict

@logged
@traced
class ApiUtil():
    """ Class to hold one application to make API calls against
        Must init with the appropriate values
    """

    def __init__(self, base_url, client_id, client_secret, api_json = None, token_expires_percent=5):
        # type: (str, str, str, str, str) -> None
        """[Init method used to create an Api Class for making api calls]
        
        :param base_url: Base URL of the API service
        :type base_url: str
        :param client_id: Client ID of the application
        :type client_id: str
        :param client_secret: Secret of the application
        :type client_secret: str
        :param api_json: API file defining all JSON limits and calls, defaults to None because it will use the default
        :type api_json: str, optional
        :param token_expires_percent: This is a percentage of time to take off the token renewal to ensure it doesn't run out. For instance 5(%) of 3600 is 180. 
        :type token_expires_percent: int, optional
        :raises Exception: If this cannot be configured with parameters used
        :raises AttributeError: If the apis.json file is empty
        """

        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_expires_percent = int(100-token_expires_percent)/100

        # This line is needed so pylint doesn't complain about this variable not existing.
        self.__log = self.__log

        # If the user doesn't pass an alternate API file use the included one
        if not api_json:
            api_json = pkg_resources.resource_filename(__name__, 'apis.json')

        with open(api_json, encoding='utf-8') as api_file:
            apis = json.loads(api_file.read())
        
        # If the string is empty
        if not apis:
            raise AttributeError("fFile {api_file} loaded is empty")

        # Create a dict to hold details of scopes (from json)
        self.scopes = defaultdict(dict)
        # Create a dict to cache the tokens
        self.tokens = defaultdict(dict)

        # Setup all of the calls to the apis with the limits
        for (client_scope, api) in viewitems(apis): 
            self.scopes[client_scope]["api_call"] = sleep_and_retry(limits(calls=api.get('limits_calls'), period=api.get('limits_period'))(self._api_call))
            # Store the token url associated with this client scope for later
            self.scopes[client_scope]["token_url"] = api.get('token_url')

    def api_call(self, api_call, client_scope, method="GET", payload=None, api_specific_headers=None):
        # type: (str, str, Dict[str, str], str, str) -> requests.Response
        """Calls the specified API with the optional method
        
        :param api_specific_headers:
        :param api_call: certain API to call has specific header so letting application pass the headers as they need
        :type api_call: str
        :param client_scope: Client scope, must be present in the api_json file
        :type client_scope: str
        :param method: Which HTTP method to use, defaults to "GET", optional
        :type method: str
        :param query: Optional query parameter to make against the API call
        :type method: str
        :param payload: Payload for POST/GET methods, optional. Can be a query parameter for next page!
        :type payload: Dict[str, str]  
        :returns Requests object with response from API (or an Exception)
        :raises Exception: No Access Token
        """
        this_scope = self.scopes.get(client_scope)
        return this_scope.get("api_call")(api_call, self.get_access_token(this_scope.get("token_url"), client_scope), method, payload, api_specific_headers)

    def _api_call(self, api_call, access_token, method="GET", payload=None, api_specific_headers=None):
        # type: (str, str, Dict[str, str], str, str) -> requests.Response
        """ Internal method for making api calls 
        """

        if access_token is None:
            raise Exception("Must obtain an access token before making API Call")

        headers = {
            "accept" : "application/json",
            "Authorization" : f"Bearer {access_token}",
            "x-ibm-client-id" : self.client_id,
        }
        if not (api_specific_headers is None):
            for header in api_specific_headers:
                headers.update(header)

        self.__log.debug(headers)
        api_url = f"{self.base_url}/{api_call}"

        self.__log.debug(f"Calling {api_url} with method {method}")
        if method == "GET":
            resp = requests.get(api_url, headers=headers, params=payload)
        elif method == "POST":
            resp = requests.post(api_url, headers=headers, data=payload)
        elif method == "PUT":
            resp = requests.put(api_url, headers=headers, data=payload)
        elif method == "DELETE":
            resp = requests.delete(api_url, headers=headers)
        elif method == "HEAD":
            resp = requests.head(api_url, headers=headers)
        elif method == "OPTIONS":
            resp = requests.options(api_url, headers=headers)
        else:
            raise Exception(f"The method {method} is unsupported")
            
        if (resp.ok):
            return resp
        else:
            self.__log.debug(resp.status_code)
            self.__log.debug(resp.text)
            return resp

    def get_next_page(self, response):
        #type: (requests.Response) -> Dict
        if not 'next' in response.links:
            return None
        self.__log.debug(response.links)
        return parse_qs(urlparse(response.links['next']['url']).query)

    def get_access_token(self, token_url, client_scope):
        # type: (str, str) -> str
        """Retrieves access token from the local tokens dictionary
           If it's expired it will attempt to renew it
        :param token_url: Full URL to retrieve access token
        :type token_url: str
        :param client_scope: Client scope to retrieve this token for
        :type client_scope: str
        :returns Access token str
        :raises AttributeError If the oauth token could not be found
        """
        token = self.get_oauth_token(token_url, client_scope)
        if token is None:
            raise AttributeError(f"Could not find oauth token for {token_url} {client_scope}")
        return token.get("access_token")

    def expire_token(self, token_url=None, client_scope=None):
        """ Expires the token, given the token_url or the scope. For the scope it will expire all the tokens if given
        
        :param token_url: Token URL to expire
        :type token_url: str
        :param client_scope: Client scope to expire, will expire all tokens that use this 
        :type client_scope: str 
        :returns True if the token could be expired, False if there was some problem with the parameters or finding the token
        """
        # Try to get the tokenurl from the api for the client scope
        if token_url is None:
           token_url = self.scopes.get(client_scope, {}).get("token_url")

        token_key = token_url + '/' + client_scope

        if token_key in self.tokens:
            self.tokens[token_key]["expires_time"] = datetime.now()
            self.__log.info(f"Token {token_key} has been expired")
            return True
        return False

    def get_oauth_token(self, token_url, client_scope):
        # type: (str, str) -> Dict
        """Retrieves an access token from the specified URL, also caches the token in self.tokens dict
        :param token_url: Full URL to retrieve access token
        :type token_url: str
        :param client_scope: Client scope to retrieve this token for
        :type client_scope: str
        :returns Dict (from json) generated from the response containing token information
        """
        
        token_key = token_url + '/' + client_scope

        if token_key in self.tokens:
            cached_token = self.tokens.get(token_key)
            # Check expires_time, if this is valid just return the token other-wise renew it, have a fallback incase this cam't be looked up
            token_expire_time = cached_token.get("expires_time", datetime.min)
            self.__log.debug(f"Now is {datetime.now()} token expires in {token_expire_time}")
            if (datetime.now() < token_expire_time):
                # Not expired return the token, otherwise continue on
                self.__log.debug(f"Token for {token_key} found and valid, returning cached token")
                return cached_token
            else:
                self.__log.info(f"Token for {token_key} expired, renewing token")

        # Otherwise we have to retrieve it
        payload = {
            "grant_type" : "client_credentials",
            "client_id" : self.client_id,
            "client_secret" : self.client_secret,
            "scope" : client_scope,
        }
        headers = {
            "accept" : "application/json",
        }
        resp = requests.post(f"{self.base_url}/{token_url}", data=payload, headers=headers)
        if (resp.ok):
            r_json = resp.json()
            # If expires_in is a parameter on the return, add the value to "now" and store it as a new value expires_time
            if 'expires_in' in r_json:
                expire_seconds = int(r_json['expires_in'])*self.token_expires_percent
                expires_time = datetime.now() + timedelta(seconds=expire_seconds)
                r_json['expires_time'] = expires_time
                self.__log.info(f"The new token for {client_scope} will expire at {expires_time} after {expire_seconds} seconds")
            # Cache the token
            self.tokens[token_key] = r_json
            return r_json
        else:
            self.__log.warn(f"Token generation failed with code {resp.status_code}")
            self.__log.debug(resp.text)
            return None


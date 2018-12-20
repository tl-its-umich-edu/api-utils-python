# -*- coding: future_fstrings -*- 

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from future.standard_library import install_aliases
from future.utils import viewitems

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

    def __init__(self, base_url, client_id, client_secret, api_json = None):
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
        :raises Exception: If this cannot be configured with parameters used
        """

        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        # This line is needed so pylint doesn't complain about this variable not existing.
        self.__log = self.__log

        # If the user doesn't pass an alternate API file use the included one
        if not api_json:
            api_json = pkg_resources.resource_filename(__name__, 'apis.json')

        with open(api_json, encoding='utf-8') as api_file:
            apis = json.loads(api_file.read())

        # Create a dict to hold details of scopes (from json)
        self.scopes = defaultdict(dict)
        # Create a dict to cache the tokens
        self.tokens = defaultdict(dict)

        # Setup all of the calls to the apis with the limits
        for (client_scope, api) in viewitems(apis): 
            self.scopes[client_scope]["api_call"] = sleep_and_retry(limits(calls=api.get('limits_calls'), period=api.get('limits_period'))(self._api_call))
            # Store the token url associated with this client scope for later
            self.scopes[client_scope]["token_url"] = api.get('token_url')

    def api_call(self, api_call, client_scope, method="GET", payload=None):
        # type: (str, str, Dict[str, str], str, str) -> requests.Response
        """Calls the specified API with the optional method
        
        :param api_call: API to call on this application
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
        return this_scope.get("api_call")(api_call, self.get_access_token(this_scope.get("token_url"), client_scope), method, payload)

    def _api_call(self, api_call, access_token, method="GET", payload=None):
        # type: (str, str, Dict[str, str], str, str) -> requests.Response
        """ Internal method for making api calls 
        """

        headers = {
            "accept" : "application/json",
            "Authorization" : f"Bearer {access_token}",
            "x-ibm-client-id" : self.client_id,
        }
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
        """
        
        return self.get_oauth_token(token_url, client_scope).get("access_token")

    def get_oauth_token(self, token_url, client_scope):
        # type: (str, str) -> Dict
        """Retrieves an access token from the specified URL, also caches the token in self.tokens dict
        :param token_url: Full URL to retrieve access token
        :type token_url: str
        :param client_scope: Client scope to retrieve this token for
        :type client_scope: str
        :returns Dict (from json) generated from the response containing token information
        """
        if client_scope in self.tokens:
            cached_token = self.tokens.get(client_scope)
            # Check expires_time, if this is valid just return the token other-wise renew it
            if (datetime.now() < cached_token.get("expires_at")):
                # Not expired return the token, otherwise continue on
                return cached_token
            else:
                self.__log.info(f"Token for {client_scope} expired, renewing token")

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
        try:
            if (resp.ok):
                r_json = resp.json()
                # If expires_at is a parameter on the return, add the value to "now" and store it as a new value expires_time
                if 'expires_at' in r_json:
                    r_json['expires_time'] = datetime.now() + timedelta(seconds=r_json['expires_at'])
                # Cache the token
                self.tokens[token_url] = r_json
                return r_json
        except (ValueError):
            self.__log.error ("Error obtaining access token with credentials")

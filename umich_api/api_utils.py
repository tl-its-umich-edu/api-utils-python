# -*- coding: future_fstrings -*- 

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from future.standard_library import install_aliases
from future.utils import viewitems

install_aliases()

from builtins import *
from ratelimit import limits, sleep_and_retry
from urllib.parse import urlparse, parse_qs

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

        # If the user doesn't pass an alternate API file use the included one
        if not api_json:
            api_json = pkg_resources.resource_filename(__name__, 'apis.json')

        with open(api_json, encoding='utf-8') as api_file:
            apis = json.loads(api_file.read())

        self.scopes = defaultdict(dict)
        # Setup all of the calls to the apis with the limits
        for (client_scope, api) in viewitems(apis): 
            self.scopes[client_scope]["api_call"] = sleep_and_retry(limits(calls=api.get('limits_calls'), period=api.get('limits_period'))(self._api_call))
            # Each client_scope seems to need it's own access token. Just get them all here first
            if "access_token" not in self.scopes[client_scope]:
                self.scopes[client_scope]["access_token"] = self.get_access_token(api.get('token_url'), client_scope)

    def api_call(self, api_call, client_scope, method="GET", payload=None):
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
        return self.scopes[client_scope]["api_call"](api_call, self.scopes[client_scope]["access_token"], method, payload)

    def _api_call(self, api_call, access_token, method="GET", payload=None):
        # type: (str, str, Dict[str, str]) -> requests.Response
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
            resp = requests.post(api_url, headers=header, data=payload)
        elif method == "PUT":
            resp = requests.put(api_url, headers=header, data=payload)
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
        if not 'next' in response.links:
            return None
        try:
            self.__log.debug(response.links)
            return parse_qs(urlparse(response.links['next']['url']).query)
        except:
            raise

    def get_access_token(self, token_url, client_scope):
        # type: (str) -> str
        """Retrieves an access token from the specified URL
        
        :param token_url: Full URL to retrieve access token
        :type token_url: str
        :param client_scope: Client scope to retrieve this token for
        :type client_scope: str
        """

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
                return resp.json().get('access_token')
        except (ValueError):
            self.__log.error ("Error obtaining access token with credentials")
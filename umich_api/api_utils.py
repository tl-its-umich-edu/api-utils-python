# -*- coding: future_fstrings -*- 

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from future.standard_library import install_aliases
install_aliases()

from builtins import *
from ratelimit import limits, sleep_and_retry
from urllib.parse import urlparse
from autologging import logged, traced

import requests, json, pkg_resources

from typing import Dict

@logged
@traced
class ApiUtil():
    access_token = ""

    def __init__(self, base_url, client_id, client_secret, client_scope, api_json = None):
        # type: (str, str, str, str, str) -> None
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
            self.access_token = self.get_access_token(self.token_url)
        else: 
            raise Exception(f"Scope {client_scope} not in known API dict")

    def _api_call(self, api_call, method="GET", payload=None):
        # type: (str, str, Dict[str, str]) -> requests.Response
        """Calls the specified API with the optional method
        
        :param api_call: API to call on this application
        :type api_call: str
        :param method: Which HTTP method to use, defaults to "GET", optional
        :type method: str
        :param payload: Payload for POST/GET methods, optional
        :type payload: Dict[str, str]  
        :returns Requests object with response from API (or an Exception)
        :raises Exception: No Access Token
        """

        headers = {
            "accept" : "application/json",
            "Authorization" : f"Bearer {self.access_token}",
            "x-ibm-client-id" : self.client_id,
        }
        self.__log.debug(headers)
        api_url = f"{self.base_url}/{api_call}"

        self.__log.debug(f"Calling {api_url} with method {method}")
        if method == "GET":
            resp = requests.get(api_url, headers=headers)
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

    def get_pagination_query(self, headers):
        return None

    def get_access_token(self, token_url):
        # type: (str) -> str
        """Retrieves an access token from the specified URL
        
        :param token_url: Full URL to retrieve access token
        :type token_url: str
        """

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
                return resp.json().get('access_token')
        except (ValueError):
            self.__log.error ("Error obtaining access token with credentials")
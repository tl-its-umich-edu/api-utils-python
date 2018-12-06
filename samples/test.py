# -*- coding: future_fstrings -*- 

from umich_api.api_utils import ApiUtil
import logging, json

logging.basicConfig(level="DEBUG")

with open(".config.json") as json_config:
    config = json.loads(json_config.read())

url = config.get("url")
client_id = config.get("client_id")
secret = config.get("secret")

print (url)
mcommunity_api = ApiUtil(url, client_id, secret, "mcommunity")

uniqname = "uniqname"
mcommunity_api.api_call(f"MCommunity/People/{uniqname}")
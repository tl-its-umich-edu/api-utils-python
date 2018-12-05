import os
from umich_api.api_utils import ApiUtil
import logging
import os
 
logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

from dotenv import load_dotenv
load_dotenv()

url = os.getenv("url")
id = os.getenv("id")
secret = os.getenv("secret")

scope = "mcommunity"
mcommunity_api = ApiUtil(url, id, secret, scope, limits_calls=200, limits_period=60)
mcommunity_api.get_access_token("inst/oauth2/token")
uniqname = "uniqname"
mcommunity_api.api_call(f"MCommunity/People/{uniqname}")
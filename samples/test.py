import os
from umich_api.api_utils import ApiUtil
import logging
import os
 
logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

from dotenv import load_dotenv
load_dotenv()

url = os.getenv("url")
client_id = os.getenv("client_id")
secret = os.getenv("secret")

mcommunity_api = ApiUtil(url, client_id, secret, "mcommunity")

uniqname = "uniqname"
mcommunity_api.api_call(f"MCommunity/People/{uniqname}")
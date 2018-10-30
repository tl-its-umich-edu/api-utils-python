import os
from umich_api.api_utils import ApiUtil

from dotenv import load_dotenv
load_dotenv()

url = os.getenv("url")
id = os.getenv("id")
secret = os.getenv("secret")
scope = os.getenv("scope")

esb = ApiUtil(url, id, secret, scope, limits_calls=1)
esb.get_access_token()
for i in range(0, 50):
    esb.api_call("Curriculum/SOC/Terms")
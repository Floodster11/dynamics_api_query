import json
import adal
import requests
from flask import Flask
import logging
import os


class Dynamics365Auth(object):
    LOGIN_ENDPOINT = "https://login.microsoftonline.com"
    RESOURCE = "https://management.core.windows.net/"

    def get_access_token_with_client_credentials(self, tenant_id, client_id, client_secret):
        context = adal.AuthenticationContext(self.LOGIN_ENDPOINT + '/' + tenant_id)

        token = context.acquire_token_with_client_credentials(resource=self.RESOURCE, client_id=client_id,
                                                              client_secret=client_secret)

        return token

    def get_access_token_with_username_password(self, dyn365_url, tenant_id, username, password, client_id,
                                                client_secret):
        AUTH_ENDPOINT = "https://login.microsoftonline.com/{tenant_id}/oauth2/token".format(tenant_id=tenant_id)

        POST_TOKEN_REQUEST = {
            "client_id": client_id,
            "client_secret": client_secret,
            "resource": dyn365_url,
            "username": username,
            "password": password,
            "grant_type": "password"
        }

        response = requests.post(AUTH_ENDPOINT, data=POST_TOKEN_REQUEST)

        token = response.json()  # ["access_token"]

        return token

    def get_auth_params(self, json_file):
        error = None
        try:
            json_data = json.load(open(json_file))
        except Exception as e:
            json_data = None
            error = e

        return json_data, error


def main():
    # TENANT_ID = "6871727a-5747-424a-b9d4-39a621930267"
    # CLIENT_ID = "012b7898-6c8b-41c0-bb58-11817fb6d6f7"
    # CLIENT_SECRET = "DFDZYSZKMJR62wp9shiWVUQaRlLEglXpRGX6ofdglus="
    # USER_NAME = "jflood@lixar.com"
    # PASSWORD = "Fl00dst3r11"
    # DYN365_URL = "https://lixarqa.crm3.dynamics.com/"

    app = Flask("Dynamics365Auth")

    logger = logging.getLogger("Dynamics365Auth")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("dyn365auth.log", mode="w")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Starting Dynamics365Auth service...")

    dynamics365Auth = Dynamics365Auth()

    logger.info("Getting Dynamics365Auth params...")
    json_data, error = dynamics365Auth.get_auth_params(json_file="dyn365auth_params.json")

    if json_data != None:
        TENANT_ID = json_data["tenant_id"]
        CLIENT_ID = json_data["client_id"]
        CLIENT_SECRET = json_data["client_secret"]
        USER_NAME = json_data["user_name"]
        PASSWORD = json_data["password"]
        DYN365_URL = json_data["dyn365_url"]

        logger.info("TENANT_ID = %s", TENANT_ID)
        logger.info("CLIENT_ID = %s", CLIENT_ID)
        logger.info("USER_NAME = %s", USER_NAME)
    else:
        logger.info("Unexpected error: %s", error)

    @app.route("/")
    def index():
        return "Dynamics365Auth RESTful service"

    @app.route("/api/v2.0/token", methods=["GET"])
    def get_token2():
        access_token_info = None

        try:
            logger.info("The 'access_token_info' is requested.")

            access_token_info = dynamics365Auth.get_access_token_with_username_password(
                tenant_id=TENANT_ID,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                username=USER_NAME,
                password=PASSWORD,
                dyn365_url=DYN365_URL)
            access_token = access_token_info['access_token']
            token_type   = access_token_info['token_type']
            # print(access_token)
            # print(token_type)
            # print(json.dumps(access_token_info))
            logger.info("The 'access_token_info' was received.")
        except Exception as e:
            logger.info("Unexpected error: %s", e)
        output = json.dumps(access_token_info)
        return output

    # run application
    app.run(host="0.0.0.0", debug=True, port=5001)
    #---------- PERHAPS INSERT THE crm_request function from auth.py here. -----------
    teeest="yahoo" + access_token
    return teeest

# IF I RUN THIS AND hit http://localhost:5001/api/v2.0/token - it returns a valid token
#Next, must do this via script. and substring out the access token
# curl -X GET http://localhost:5001/api/v2.0/token works as well. Obvi same with Postman.
if __name__ == "__main__":
    tester = main()
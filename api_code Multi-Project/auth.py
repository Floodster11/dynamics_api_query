#!/usr/bin/python

# GRABS CORRECT AUTH TOKEN BUT IT NEEDS TO USE USER/PASSWORD AUTHENTICATION INSTEAD OF CLIENT

import adal
import requests
import json
from flask import Flask

dyn365_auth_url = 'http://dyn365auth:5001/api/v2.0/token'
dyn365_base_url = 'https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/'
TENANT_ID = "6871727a-5747-424a-b9d4-39a621930267"
CLIENT_ID = "012b7898-6c8b-41c0-bb58-11817fb6d6f7"
CLIENT_SECRET = "DFDZYSZKMJR62wp9shiWVUQaRlLEglXpRGX6ofdglus="
LOGIN_ENDPOINT = 'https://login.microsoftonline.com'
RESOURCE = "https://management.core.windows.net/"
DYN365_URL = "https://lixarqa.crm3.dynamics.com/"


def get_access_token_with_client_credentials():
    context = adal.AuthenticationContext(LOGIN_ENDPOINT + '/' + TENANT_ID)
    token   = context.acquire_token_with_client_credentials(RESOURCE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    print(token)
    return token


def extract_access_token(token):
    access_token = ''
    token = json.dumps(token)
    try:
        test = json.loads(token)
        access_token = test['accessToken']
        print(access_token)
    except(KeyError):
        # handle any missing key errors
        print('Could not get access token')
    return access_token


def check_access_token_for_dyn365_fn(token):
    if token != None:
        next_operator_name = "dyn365_access_token_ok"
    else:
        next_operator_name = "dyn365_access_token_not_ok"
    print(next_operator_name)
    return next_operator_name

def crm_request(accessToken):
    query = 'psa_projects'
    if(accessToken != ''):
        crmrequestheaders = {
            'Authorization': 'Bearer ' + accessToken,
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'Prefer': 'odata.maxpagesize=500',
            'Prefer': 'odata.include-annotations=OData.Community.Display.V1.FormattedValue'
        }
        crmresponse = requests.get(dyn365_base_url + query, headers=crmrequestheaders)
    print(crmresponse)
    return crmresponse




token = get_access_token_with_client_credentials()
good  = check_access_token_for_dyn365_fn(token)
token1 = extract_access_token(token)
res   = crm_request(token1)
#!/usr/bin/python

import sys
import requests
import json
##############################################################################################################
dyn365_auth_url   = 'http://localhost:5001/api/v2.0/token'
dyn365_base_url   = 'https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/'
access_token_key = "access_token"
response = requests.get(url=dyn365_auth_url)
test_opportunityid       = 'fa62735a-c3eb-e711-812f-480fcfeaf991'


def get_access_token():
    try:
        response_json = response.json()
        access_token = response_json[access_token_key]
        # print('Token: ' + access_token)
        return access_token
    except Exception as e:
        dyn365_access_token = None


def check_access_token_for_dyn365_fn(dyn365_access_token):
    if dyn365_access_token is not None:
        status = "Valid"
    else:
        status = "Not-Valid"
    return status


# Get user input for desired OpportunityID
def get_user_input():
    opportunityid = input('Enter the Opportunity ID of desired Data:')
    return opportunityid


def process_web_api_fn(status, opportunityid, access_token):
    if status == "Valid":
        ########### CALL OPPORTUNITIES API ###########
        # https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/opportunities(d5bda00a-4ea2-e711-811c-480fcfea20c1)?$selec
        # t=name,salesstage,stepname --> returns that oppid with name field
        search               = dyn365_base_url + 'opportunities(' + opportunityid + ')?$select=name,_customerid_value,' \
                                                                                    'salesstage,stepname'

        header               = {
            "Authorization": "Bearer " + access_token,
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'Prefer': 'odata.maxpagesize=1',
            'Prefer': 'odata.include-annotations=OData.Community.Display.V1.FormattedValue'
        }
        opp_response         = requests.get(url=search, headers=header)
        opp_string           = opp_response.text  # Turns to a dict so we can't replace
        # print('Opp: ' + opp_string)

        ########### CALL PROJECT API ###########
        # https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/psa_projects?$select=psa_name,_psa_opportunity_value&$filter=_psa_opportunity_value%20eq%20d50424ed-cada-e711-8127-480fcfea20c1
        project_search_base = 'https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/psa_projects/'
        project_query       = 'psa_name,_psa_opportunity_value,psa_tobeinvoiced,psa_forecastcostamount&$filter=_psa_opportunity_value eq ' + test_opportunityid

        # Queries Projects based on OppId
        project_search      = project_search_base + '?$select=' + project_query
        project_response    = requests.get(url=project_search, headers=header)
        project_string      = project_response.text
        # print('Project String: ' + project_string)

        ### GET JSON TO GRAB PROJECT ID ###
        # proj_hits          = get_number_of_proj_hits(project_string)
        project_json       = convert_to_json(project_string)

        ## ENABLE THIS WHEN COMPLETED TO TAKE CORRECT PROJ ID FOR INVOICE ##
        # psa_projectid = project_json['value'][0]['psa_projectid']


        # ########### CALL INVOICE API ###########
        test_psa_projectid = '0a991dbd-88ec-e711-812f-480fcfeaf991'
        psa_projectid         = test_psa_projectid

        invoice_search_base   = 'https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/invoices'
        invoice_query    = '_psa_project_value,datedelivered,totallineitemamount&$filter=_psa_project_value%20eq%20'+ psa_projectid
        invoice_search   = invoice_search_base + '?$select=' + invoice_query
        invoice_response = requests.get(url=invoice_search, headers=header)
        invoice_string   = invoice_response.text


        return opp_string, project_string, project_json, invoice_string
    else:
        print("Token Not Valid")
        sys.exit(0)


def convert_to_json(input_string):
    output_json             = json.loads(input_string)
    return output_json

def convert_dict_to_json(input_string_dict, proj_hits):
    output_json_dict = {}
    temp             = {}
    for x in proj_hits:
        # temp[x]             = json.dumps(input_string_dict)
        # output_json_dict[x] = json.loads(temp[x])
        output_json_dict = json.dumps(input_string_dict)
        output_json_dict = json.loads(output_json_dict)
    return output_json_dict

def get_vars_based_from_json(opp_json, project_json, invoice_json):
    ##### GET VARS FROM OPP JSON #####
    opportunityid           = opp_json['opportunityid']            # OppId from Opps
    _customerid_value       = opp_json['_customerid_value']        # _customerid from Opps
    salesstage              = opp_json['salesstage']               # Sales stage from Opps
    stepname                = opp_json['stepname']                 # stepname (2-Qualified) from Opps
    # print('\n' + opportunityid)

    opp_dict = {
        'opportunityid'    : opportunityid,
        '_customerid_value': _customerid_value,
        'salesstage'       : salesstage,
        'stepname'         : stepname
    }

    ##### GET VARS FROM PROJECT JSON #####
    psa_name            = project_json['value'][0]['psa_name']
    psa_projectid       = project_json['value'][0]['psa_projectid']

    ###------MAY NOT NEED THESE------###
    if (project_json['value'][0]['psa_tobeinvoiced']) is not None:
        psa_tobeinvoiced_dict = project_json['value'][0]['psa_tobeinvoiced@OData.Community.' \
                                                            'Display.V1.FormattedValue']
    else:
        psa_tobeinvoiced_dict = project_json['value'][0]['psa_tobeinvoiced']
    if (project_json['value'][0]['psa_forecastcostamount']) is not None:
        psa_forecastcostamount_dict = project_json['value'][0]['psa_forecastcostamount@OData.Community.' \
                                                                  'Display.V1.FormattedValue']
    else:
        psa_forecastcostamount_dict = project_json['value'][0]['psa_forecastcostamount']

    _psa_opportunity_value  = project_json['value'][0]['_psa_opportunity_value']

    proj_dict = {
        'psa_name'              : psa_name,
        'psa_projectid'         : psa_projectid,
        '_psa_opportunity_value': _psa_opportunity_value,
        'psa_tobeinvoiced'      : psa_tobeinvoiced_dict,
        'psa_forecastcostamount': psa_forecastcostamount_dict
    }
    # print(proj_dict)


# ---------Good to here -----------
    ##### GET VARS FROM INVOICES JSON #####

    if (invoice_json['value'][0]['invoiceid']) is not None:
        invoiceid = invoice_json['value'][0]['invoiceid']
        _psa_project_value  = invoice_json['value'][0]['_psa_project_value']
        datedelivered = invoice_json['value'][0]['datedelivered']
        totallineitemamount = invoice_json['value'][0]['totallineitemamount@OData.Community.Display.V1.FormattedValue']

    if _psa_project_value is not None:
        project_name    = invoice_json['value'][0]['_psa_project_value@OData.Community.Display.V1.FormattedValue']
        project_id      = invoice_json['value'][0]['_psa_project_value']
    else:
        project_name    = None
        project_id      = _psa_project_value

    if datedelivered is not None:
        date            = invoice_json['value'][0]['datedelivered@OData.Community.Display.V1.FormattedValue']
    else:
        date            = datedelivered


    inv_dict = {
        'invoiceid'          : invoiceid,
        'project_id'         : project_id,
        'project_name'       : project_name,
        'date'               : date,
        'totallineitemamount': totallineitemamount
    }
    # print(inv_dict)
    return opp_dict, proj_dict, inv_dict

def get_number_of_proj_hits(project_string):
    proj_hits = project_string.count('@odata.etag')

    if proj_hits > 1:
        more_than_one_project_flag = 1
    else:
        more_than_one_project_flag = 0
    return more_than_one_project_flag


def get_number_of_inv_hits(invoice_string):
    inv_hits = invoice_string.count('@odata.etag')
    inv_hits = range(0, inv_hits)
    return inv_hits


def main():
    # opportunityid                                               = get_user_input()
    opportunityid                                                 = test_opportunityid
    access_token                                                  = get_access_token()
    status                                                        = check_access_token_for_dyn365_fn(access_token)
    opp_string, project_string, project_json, invoice_string      = process_web_api_fn(status, opportunityid, access_token)
    opp_json                                                      = convert_to_json(opp_string)
    invoice_json                                                  = convert_to_json(invoice_string)
    opp_dict, proj_dict, inv_dict                                 = get_vars_based_from_json(opp_json, project_json, invoice_json)



    ### TEST TO SEE DICTS WORKING ###
    print(opp_dict)
    print(proj_dict)
    print(inv_dict)

    # print(opp_string)
    # print(project_string)
    # print(invoice_string)

    # print(proj_hits)
    # print(inv_hits)

    # f = open('troubleshoot.txt', 'w')
    # f.write(opp_string + '\n' + project_string + '\n' + invoice_string)
    # f.close()


main()

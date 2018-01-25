#!/usr/bin/python

import sys
import requests
import json
# from   dyn365auth import Dynamics365Auth
# from   connectors.dyn365conn import Dynamics365RestConnector
# from   processors.dyn365map import Dynamics365Mapper

# dynamics365auth = Dynamics365Auth()
##############################################################################################################
dyn365_auth_url   = 'http://localhost:5001/api/v2.0/token'
dyn365_base_url   = 'https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/'
# dynamics365Mapper = Dynamics365Mapper()

# def get_created_by_fn(execution_date):
#     return DAG_NAME + "-" + get_created_date_fn(execution_date)
#
#
# def get_created_date_fn(execution_date):
#     return execution_date.strftime("%Y-%m-%dT%H:%M:%S")

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
        get_proj_id         = json.loads(project_string)
        # proj_id             = get_proj_id['value'][0]['psa_projectid']
        # print('projectID: ' + proj_id)
        print('Project String: ' + project_string)

        ### GET JSON TO GRAB PROJECT IDs ###
        proj_hits          = get_number_of_proj_hits(project_string)
        psa_projectid_dict = {}
        project_json       = convert_to_json(project_string)
        for x in proj_hits:
            psa_projectid_dict[x] = project_json['value'][x]['psa_projectid']
        # print('Dict: ')
        # print(psa_projectid_dict)

        # TODO TRY CONVERTING TO JSON HERE (AND AFTER OPP & INVOICE IF SUCCESSFUL) AND CONVERT TO DICT -->
        # TODO THEN WE CAN TRY TO CALL ALL INVOICES BASED ON ALL PROJECTS, NOT JUST ONE


        # ########### CALL INVOICE API ###########

        invoice_search_base   = 'https://lixarqa.api.crm3.dynamics.com/api/data/v8.2/invoices'
        invoice_query_dict    = {}
        # invoice_response_dict = {}
        invoice_string_dict   = {}
        for x in proj_hits:
            invoice_query_dict[x] = '_psa_project_value,datedelivered,totallineitemamount&$filter=_psa_project_value%20eq%20'+ psa_projectid_dict[x]
            invoice_search = invoice_search_base + '?$select=' + invoice_query_dict[x]
            invoice_response = requests.get(url=invoice_search, headers=header)
            invoice_string_dict[x] = invoice_response.text
        print(invoice_string_dict)

        # Queries Projects based on ProjID


        # print('Invoice: ------ ' + invoice_string)


        return opp_string, project_string, project_json, invoice_string_dict
    else:
        print("Token Not Valid")
        sys.exit(0)


# TODO Try to convert this to individual converts to be called in string def
# def convert_to_json(opp_string, project_string, invoice_string):
#     opp_json                = json.loads(opp_string)
#     project_json            = json.loads(project_string)
#     invoice_json            = json.loads(invoice_string)
#     # print(opp_string)
#     return opp_json, project_json, invoice_json

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

def get_vars_based_from_json(opp_json, project_json, invoice_json_dict, proj_hits):
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
    psa_name_dict               = {}
    psa_projectid_dict          = {}
    psa_tobeinvoiced_dict       = {}
    psa_forecastcostamount_dict = {}
    for x in proj_hits:
        psa_name_dict[x]            = project_json['value'][x]['psa_name']
        psa_projectid_dict[x]       = project_json['value'][x]['psa_projectid']

        ###------MAY NOT NEED THESE------###
        if (project_json['value'][x]['psa_tobeinvoiced']) is not None:
            psa_tobeinvoiced_dict[x] = project_json['value'][x]['psa_tobeinvoiced@OData.Community.' \
                                                                'Display.V1.FormattedValue']
        else:
            psa_tobeinvoiced_dict[x] = project_json['value'][x]['psa_tobeinvoiced']
        if (project_json['value'][0]['psa_forecastcostamount']) is not None:
            psa_forecastcostamount_dict[x] = project_json['value'][x]['psa_forecastcostamount@OData.Community.' \
                                                                      'Display.V1.FormattedValue']
        else:
            psa_forecastcostamount_dict[x] = project_json['value'][x]['psa_forecastcostamount']
        # print(psa_projectid + '\n' + psa_name + '\n' + _psa_opportunity_value)
        # print(psa_tobeinvoiced + '\n' + psa_forecastcostamount)

    # print(psa_name_dict)
    _psa_opportunity_value  = project_json['value'][0]['_psa_opportunity_value']

    proj_dict = {
        'psa_name'              : psa_name_dict,
        'psa_projectid'         : psa_projectid_dict,
        '_psa_opportunity_value': _psa_opportunity_value,
        'psa_tobeinvoiced'      : psa_tobeinvoiced_dict,
        'psa_forecastcostamount': psa_forecastcostamount_dict
    }
    print(proj_dict)


# TODO - HAVE TO CHANGE THESE TO DICTS POTENTIALLY AS DONE ABOVE WITH PROJECTS
    ##### GET VARS FROM INVOICES JSON #####
    invoiceid_dict = {}
    # m = invoice_json_dict[1]
    # print(m)


    for y in proj_hits:
        invoiceid_dict[x] = invoice_json_dict[x]['value'][0]['invoiceid']
        print('TEESSTT_________F_______')
        print(invoiceid_dict)



    _psa_project_value  = invoice_json['value'][0]['_psa_project_value']
    if _psa_project_value is not None:
        project_name    = invoice_json['value'][0]['_psa_project_value@OData.Community.Display.V1.FormattedValue']
        project_id      = invoice_json['value'][0]['_psa_project_value']
    else:
        project_name    = _psa_project_value

    datedelivered       = invoice_json['value'][0]['datedelivered']
    if datedelivered is not None:
        date            = invoice_json['value'][0]['datedelivered@OData.Community.Display.V1.FormattedValue']
    else:
        date            = datedelivered


    totallineitemamount = invoice_json['value'][0]['totallineitemamount@OData.Community.Display.V1.FormattedValue']

    # print('invid: ' + invoiceid + ' Proj ID: ' + project_id + ' Proj Name: ' +  project_name + ' date: ' + date + ' line Amount: ' + totallineitemamount)


    inv_dict = {
        'invoiceid'          : invoiceid,
        'project_id'         : project_id,
        'project_name'       : project_name,
        'date'               : date,
        'totallineitemamount': totallineitemamount
    }

    return opp_dict, proj_dict, inv_dict

def get_number_of_proj_hits(project_string):
    proj_hits = project_string.count('@odata.etag')
    proj_hits = range(0,proj_hits)
    return proj_hits


def get_number_of_inv_hits(invoice_string):
    inv_hits = invoice_string.count('@odata.etag')
    inv_hits = range(0, inv_hits)
    return inv_hits


def main():
    # opportunityid                             = get_user_input()
    opportunityid                                                 = test_opportunityid
    access_token                                                  = get_access_token()
    status                                                        = check_access_token_for_dyn365_fn(access_token)
    opp_string, project_string, project_json, invoice_string_dict = process_web_api_fn(status, opportunityid, access_token)
    opp_json                                                      = convert_to_json(opp_string)
    proj_hits                                                     = get_number_of_proj_hits(project_string)
    # invoice_json_dict                                             = convert_dict_to_json(invoice_string_dict, proj_hits)
    print('invoice dict')
    # print(invoice_json_dict)
    opp_dict, proj_dict, inv_dict                                 = get_vars_based_from_json(opp_json, project_json, invoice_string_dict, proj_hits)

    ### TEST TO SEE DICTS WORKING ###
    # print(opp_dict)
    # print(proj_dict)
    # print(inv_dict)

    # print(opp_string)
    # print(project_string)
    # print(invoice_string)

    # print(proj_hits)
    # print(inv_hits)


    # f = open('troubleshoot.txt', 'w')
    # f.write(opp_string + '\n' + project_string + '\n' + invoice_string)
    # f.close()


main()

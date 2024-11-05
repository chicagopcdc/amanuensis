from cdislogging import get_logger
from amanuensis.resources.userdatamodel.consortium_data_contributor import create_consortium
from amanuensis.auth.auth import get_jwt_from_header
import json
import requests
from amanuensis.errors import NotFound, InternalError
from amanuensis.config import config

logger = get_logger(__name__)

def get_consortium_list(src_filter, ids_list, path=None):
    if src_filter is None and ids_list is None:
        raise NotFound("There is no filter specified and associated with the project you are trying to create")

    if not path:
        path = config["GET_CONSORTIUMS_URL"]

    isFilter = True if src_filter else False
    transformed_filter = src_filter if isFilter else { "AND": [{"IN":{"subject_submitter_id":ids_list}}]}
    target_filter = {}
    target_filter["filter"] = transformed_filter
    try:
        url = path
        headers = {'Content-Type': 'application/json'} 
        body = json.dumps(target_filter, separators=(',', ':'))
        jwt = get_jwt_from_header()
        headers['Authorization'] = 'bearer ' + jwt

        r = requests.post(
            url, data=body, headers=headers # , proxies=flask.current_app.config.get("EXTERNAL_PROXIES")
        )
    except requests.RequestException as e:
        print(e.message)
       

    if r.status_code != 200:
        raise InternalError(f"Sorry could not complete request")

    else:
        return r.json()


def get_consortiums_from_fitersets(filter_sets, session):
    
    consortiums_from_guppy = set()

    return_consortiums = []

    #get consortiums in filter-sets from guppy
    for s in filter_sets:
        # Get a list of consortiums the cohort of data is from
        # example or retuned values - consoritums = ['INRG']
        # s.filter_object - you can use getattr to get the value or implement __getitem__ - https://stackoverflow.com/questions/11469025/how-to-implement-a-subscriptable-class-in-python-subscriptable-class-not-subsc
        consortiums_from_guppy.update(consortium.upper() for consortium in get_consortium_list(s.graphql_object, s.ids_list))  
    
    #find which consortiums already exist in DB
    for consortium in consortiums_from_guppy:
      return_consortiums.append(create_consortium(session, consortium, consortium))

    return return_consortiums


    


from amanuensis.resources.userdatamodel.search import get_filter_sets, update_filter_set
import requests
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
import os
import glob
from amanuensis.errors import NotFound, InternalError
import json
from cdislogging import get_logger
from amanuensis.config import config

logger = get_logger(__name__)


def _load_data_files(file_name):
    possible_configs = []

    for folder in CONFIG_SEARCH_FOLDERS:
        config_path = os.path.join(folder, file_name)
        possible_files = glob.glob(config_path)
        possible_configs.extend(possible_files)

    if len(possible_configs) == 1:
        file = possible_configs[0]
    else:
        raise NotFound(
            "Could not find {}. Searched in the following locations: "
            "{}".format(file_name, str(CONFIG_SEARCH_FOLDERS))
        )
    
    with open(file, 'r') as file:
        data = json.load(file)

    return data


def _get_explorer_selectable_values(portal_config):
    selectable_values = {}
    if len(portal_config["explorerConfig"]) == 0:
        raise InternalError("No sections found in portal_config.explorerConfig")
    for explorer in portal_config["explorerConfig"]:
        selectable_values_by_tab = set()
        for tab in explorer['filters']['tabs']:
            selectable_values_by_tab.update(tab["fields"])
        selectable_values[explorer["id"]] = selectable_values_by_tab

    return selectable_values

def _check_portal_config(filter_set, selectable_values):
    """
    This function will take the selectable explorer values
    and check a filter-sets selectable values to validate whether
    the filter-sets values are valid
    Only has to be true for one explorer section
    """
    selected_keys = filter_set.filter_object["value"].keys()
    filter_name = filter_set.name
    tab = filter_set.filter_source_internal_id
    for key in selected_keys:
        if key not in selectable_values[tab]:
            logger.info(f"The filter {filter_name} in the section {tab} contains a selected value {key} which is not a valid selectable value in the data portal's selectable values")
            return False

       
    logger.info(f"The filter {filter_name} is valid for the section {tab} of the data portal's selectable values")
    return True
        


def _check_es_to_dd_map(filter_set, es_to_dd_map):
    #first want to check if selected value exists in mapping keys
    #look in DD to look for value type
    #if the type is enum check if 
    #array ex: {studies.treatment_arm: {__type: "OPTION", selectedValues: ["some study"], isExclusion: false}}
    #enum ex: {"consortium": {"__type": "OPTION", "isExclusion": false, "selectedValues": ["HIBISCUS"]}
    #float ex: {tumor_assessments.longest_diam_dim1: {__type: "RANGE", lowerBound: 20, upperBound: 76}}

    filter_set_name = filter_set.name
    filter_object = filter_set.filter_object["value"]


    for key, selected_value in filter_object.items():
        if key not in es_to_dd_map:

            logger.info(f"The filter {filter_set_name} contains the element {key} which is not a valid element in elasticsearch")
            return False
        
        if not es_to_dd_map[key]["pointer"] and "type" not in es_to_dd_map[key] and "enum" not in es_to_dd_map[key]:
            logger.info(f"The filter {filter_set_name} contains the element {key} which is not a valid element in the data dictionary")
            return False
        
        try: 
            selected_type = selected_value["__type"]
            if selected_type == "OPTION":
                selected_values = selected_value["selectedValues"]
        except Exception as e:
            logger.info(f"The filter {filter_set_name} is not in a valid format")
            return False

        if selected_type == "OPTION":
            if "enum" in es_to_dd_map[key]:
                for value in selected_values:
                    if value not in es_to_dd_map[key]["enum"]:
                        logger.info(f"The filter {filter_set_name} has a selected value {value} for the filter {key} which is not a valid element in the data dictionary")
                        return False
                    
        elif selected_type != "RANGE":
            logger.info(f"The filter {filter_set_name} has a selected filter {key} which is not a valid format {selected_value}")
            return False
        
    logger.info(f"The filter {filter_set_name} is valid for the data dictionary")   
    return True   


def check_filter_sets(session, es_to_dd_map_file_name="es_to_dd_map.json", portal_config_file_name="gitops.json"):

    es_to_dd_map = _load_data_files(es_to_dd_map_file_name)
    
    portal_config = _load_data_files(portal_config_file_name)

    explorer_selectable_values = _get_explorer_selectable_values(portal_config)

    filter_sets = get_filter_sets(session, filter_by_active=False, filter_by_source_type=False)

    for filter_set in filter_sets:

        if "value" in filter_set.filter_object:
            
            is_valid = _check_portal_config(filter_set, explorer_selectable_values) 

            if is_valid:

                is_valid = _check_es_to_dd_map(filter_set, es_to_dd_map)
        else:
            is_valid = False


        if not is_valid:

            if filter_set.is_valid == True:

                logger.info(f"name: {filter_set.name} id: {filter_set.id} is invalid but marked as valid moving to invalid")

                update_filter_set(session, filter_set=filter_set, is_valid=False)

            else:

                logger.info(f"name: {filter_set.name} id: {filter_set.id} is invalid and already marked as invalid doing nothing")

        if is_valid:

            if filter_set.is_valid == False:

                logger.info(f"name: {filter_set.name} id: {filter_set.id} is valid but marked as invalid moving back to valid")

                update_filter_set(session, filter_set=filter_set, is_valid=True)

            else:

                logger.info(f"name: {filter_set.name} id: {filter_set.id} is valid and already marked as valid doing nothing")
            

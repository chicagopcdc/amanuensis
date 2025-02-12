from amanuensis.resources.userdatamodel.search import get_filter_sets, update_filter_set
import requests
from amanuensis.settings import CONFIG_SEARCH_FOLDERS
import os
import glob
from amanuensis.errors import NotFound, InternalError
import json
from cdislogging import get_logger
from amanuensis.config import config

logger = get_logger(__name__, log_level="info")


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


def _get_selectable_filters_from_data_portal(portal_config):
    selectable_filters = {}
    if len(portal_config["explorerConfig"]) == 0:
        raise InternalError("No sections found in portal_config.explorerConfig")
    for explorer_section in portal_config["explorerConfig"]:
        selectable_filters_by_section = set()
        for tab in explorer_section['filters']['tabs']:
            selectable_filters_by_section.update(tab["fields"])
        selectable_filters[explorer_section["id"]] = selectable_filters_by_section

    return selectable_filters


def _extract_selected_values_from_filter_set(graphql_object, selected_filters=None, node=None):
    #########ASSUMPTIONS#########
    #graphql_object is always a dictionary
    # if key is "OR" or "AND" value is a list
    # if key is "nested" value is dictionary containing key-values path: <node as string>, ("OR" or "AND"): list
    # if key is "IN", "GTE", "LTE", "!=" value is dictionary containing key-values <selectable_value>: <selectabled_value>
    # selected values can be either list of strings, string, or int
    #############################

    if selected_filters is None:
        selected_filters = {}

    if graphql_object == {}:
        return {}

    try:
        key, value = graphql_object.popitem()
        
        if key in ["IN", "GTE", "LTE", "!="]:

            filter, selected_value = value.popitem()

            if not selected_value or not filter:
                logger.error(f"Filter-set is malformed.")
                return False

            filter_name = node + "." + filter if node is not None else filter
            
            if not isinstance(selected_value, list):
                selected_value = [selected_value]

            if filter_name in selected_filters:
                selected_filters[filter_name] = selected_filters[filter_name] + selected_value

            else:
                selected_filters[filter_name] = selected_value
        
        elif key == "nested":

            # if filter-set is malformed and path isnt present, key error will be raised
            node = value.pop("path")

            selected_filters.update(_extract_selected_values_from_filter_set(value, selected_filters, node))


        elif key in ["OR", "AND"]:

            
            for filter in value:

                selected_filters.update(_extract_selected_values_from_filter_set(filter, selected_filters, node))
        
        else:
            # Unexpected key: log error and return False
            logger.error(f"Unexpected key in graphql_object {key}, {value}")
            return False
        
    except Exception as e:
        # dont log return value False up the stack
        if str(e) != "'bool' object is not iterable":
            logger.error(f"Error processing graphql_object: {type(e).__name__} - {str(e)} key: {key} value: {value}")
        
        return False

    return selected_filters


def _check_portal_config(selected_filters, filter_name, selectable_filters):
    """
    This function will take the explorer filters for a tab
    and check a filter-sets selected filters to validate whether
    the filters are currently available in the data portal via the provided portal config
    """
    invalid_filters = selected_filters.difference(selectable_filters)
    if invalid_filters:
        logger.info(f"The filter-set {filter_name} contains a selected filter {invalid_filters} which is not a valid selectable filter for the explorer in the data portal")
        return False

    else:
        logger.info(f"The filter-set {filter_name} is valid for the explorer in the data portal")
        return True
        


def _check_es_to_dd_map(selected_filters, filter_set_name, es_to_dd_map):
    
    for filter, selected_values in selected_filters.items():
        if filter not in es_to_dd_map:

            logger.error(f"The filter-set {filter_set_name} contains the filter {filter} which is not a valid element in elasticsearch")
            return False
        
        if all(key not in es_to_dd_map[filter] for key in ["type", "enum"]):
            
            if not es_to_dd_map[filter]["pointer"]:
                logger.error(f"The filter-set {filter_set_name} contains the element {filter} which does not exist in the data dictionary")
                return False
            else:
                raise InternalError(f"There is a problem with the Elastic search to data dictionary mapping for {filter} quitting job")      
        
        if "enum" in es_to_dd_map[filter]:
            
            for value in selected_values:

                if value not in es_to_dd_map[filter]["enum"]:

                    logger.error(f"The filter-set {filter_set_name} contains the value {value} which is not a valid value for the filter {filter} in the data dictionary")
                    return False
        
        else:
            #theres an edge case with vitals.submitter_id which has type ["string", "null"]
            text_options = ("string", ["string"], ["array"], ["string", "null"])
            #there no current value of type "number" but adding this here in case it gets added in future
            number_options = ("number", ["number"])
            if es_to_dd_map[filter]["type"] in text_options:
                
                if any(not isinstance(value, str) for value in selected_values):
                    logger.error(f"The filter-set {filter_set_name} contains the value {selected_values} for the filter {filter} which is not a valid value for the filter {filter} in the data dictionary")
                    return False

            elif es_to_dd_map[filter]["type"] in number_options:
                
                if any(not isinstance(value, int) and not isinstance(value, float) for value in selected_values):
                    logger.error(f"The filter-set {filter_set_name} contains the value {selected_values} for the filter {filter} which is not a valid value for the filter {filter} in the data dictionary")
                    return False
            
            else:
                logger.error(f"The filter-set {filter_set_name} contains the filter {filter} which has an unsupported type: {es_to_dd_map[filter]['type']}")
                return False
        
        
    logger.info(f"The filter {filter_set_name} is valid for the data dictionary")   
    return True   


def check_filter_sets(session, es_to_dd_map_file_name="es_to_dd_map.json", portal_config_file_name="gitops.json"):

    es_to_dd_map = _load_data_files(es_to_dd_map_file_name)
    
    portal_config = _load_data_files(portal_config_file_name)

    explorer_selectable_values = _get_selectable_filters_from_data_portal(portal_config)

    filter_sets = get_filter_sets(session, filter_by_active=False, filter_by_source_type=False)

    for filter_set in filter_sets:

        graphql_object = filter_set.graphql_object
        filter_set_name = filter_set.name
        filter_source_internal_id = filter_set.filter_source_internal_id
        filter_source = filter_set.filter_source

        separator_length = len(f"CHECKING FILTER SET: {filter_set_name} id: {filter_set.id}")
        logger.info("*" * separator_length)
        logger.info(f"CHECKING FILTER SET: {filter_set_name} id: {filter_set.id}")
        logger.info("*" * separator_length)
        logger.info(f"graphql_object: {graphql_object}")

        is_valid_portal = False
        is_valid_dd = False
            
        if graphql_object is None:

            logger.info(f"Filter-set {filter_set_name} has no graphql_object")
        
        else:
            
            extracted_values_from_filter_set = _extract_selected_values_from_filter_set(graphql_object)
        
            if extracted_values_from_filter_set is not False:
                
                if not filter_source_internal_id and filter_source == "manual":
                    logger.info(f"Filter-set {filter_set_name} is a manual filter-set, skipping validation against data portal explorer values")
                    is_valid_portal = True
                else:
                    is_valid_portal = (
                        _check_portal_config(set(extracted_values_from_filter_set.keys()), filter_set_name, explorer_selectable_values[filter_source_internal_id])
                    )

                is_valid_dd = _check_es_to_dd_map(extracted_values_from_filter_set, filter_set_name, es_to_dd_map)
            
            else:
                
                logger.info(f"Filter-set {filter_set_name} is malformed")

        
        
        is_valid = is_valid_portal and is_valid_dd
        
        
        message = f"name: {filter_set.name} id: {filter_set.id}, is_valid was evaluated to {is_valid}, "

        
        if not is_valid:

            if filter_set.is_valid == True:

                message += "but is currently True updating is_valid to False in DB"

                update_filter_set(session, filter_set=filter_set, is_valid=False)

            else:

                message += "and is currently False doing nothing"

        else:

            if filter_set.is_valid == False:

                message += "but is currently False updating is_valid to True in DB"

                update_filter_set(session, filter_set=filter_set, is_valid=True)

            else:

                message += "and is currently True doing nothing"

        
        logger.info(message)
            

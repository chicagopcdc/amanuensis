from amanuensis.resources.userdatamodel.project_datapoints import get_project_datapoints, update_project_datapoints
from amanuensis.resources.filter_sets import _load_data_files
from amanuensis.errors import InternalError
from cdislogging import get_logger

logger = get_logger(__name__, log_level="info")


def _get_data_dictionary_nodes(data_dictionary):
    """
    The data dictionary contains the nodes plus a few meta entries
    ("_definitions", "_terms", "_settings"), and a project_datapoints.term is
    always a node name.

    A node is an entry carrying an id and at least one property. This is the
    same rule the data portal uses to build the tables in the select attributes
    section, so a term the portal is currently offering can never be reported as
    missing here.

    Nodes are keyed by their id rather than by the key they arrived under, so
    the lookup does not depend on how the source keyed them.

    Note the job has to be pointed at the dictionary sheepdog serves, not at the
    raw schema.json artifact in global.dictionaryUrl. The artifact leaves links
    as unresolved {"$ref": "_definitions.yaml#/to_one"}, so every link-addressed
    value ("subjects.submitter_id") would fail to validate against it. Sheepdog
    resolves those refs before serving /_dictionary/_all.
    """
    nodes = {
        schema["id"]: schema
        for schema in data_dictionary.values()
        if isinstance(schema, dict) and schema.get("id") and schema.get("properties")
    }

    if not nodes:
        raise InternalError("No nodes found in the data dictionary, quitting job")

    return nodes


def _get_link_properties(property_schema):
    """
    A link property in the data dictionary is expressed as an "anyOf" of either a
    list of link objects or a single link object, where the link object properties
    are the fields a datapoint can address on the other side of the link
    (currently "id" and "submitter_id").

    Returns the set of addressable fields for a link property, or None when the
    property is a plain scalar property rather than a link.
    """
    any_of = property_schema.get("anyOf") if isinstance(property_schema, dict) else None

    if not isinstance(any_of, list):
        return None

    for option in any_of:
        if not isinstance(option, dict):
            continue

        items = option.get("items")

        if isinstance(items, dict) and isinstance(items.get("properties"), dict):
            return set(items["properties"].keys())

        if isinstance(option.get("properties"), dict):
            return set(option["properties"].keys())

    return None


def _check_data_dictionary(term, value_list, datapoint_name, data_dictionary_nodes):
    """
    A project datapoint is a whitelist/blacklist entry of the form
    term=<node>, value_list=[<field>, ..., <link>.<field>, ...].

    It is valid when the node still exists in the data dictionary and every
    entry in the value list still resolves to a property of that node, or to a
    field addressable through one of that node's links.
    """

    if term not in data_dictionary_nodes:
        logger.error(f"The project datapoint {datapoint_name} has the term {term} which is not a node in the data dictionary")
        return False

    node_properties = data_dictionary_nodes[term]["properties"]

    if not value_list:
        logger.info(f"The project datapoint {datapoint_name} has an empty value list, nothing to check against the data dictionary")
        return True

    for value in value_list:

        if not isinstance(value, str):
            logger.error(f"The project datapoint {datapoint_name} contains the value {value} which is not a string")
            return False

        if "." in value:

            link, link_field = value.split(".", 1)

            if link not in node_properties:
                logger.error(f"The project datapoint {datapoint_name} contains the value {value} but {term} has no link named {link} in the data dictionary")
                return False

            link_properties = _get_link_properties(node_properties[link])

            if link_properties is None:
                logger.error(f"The project datapoint {datapoint_name} contains the value {value} but {term}.{link} is not a link in the data dictionary")
                return False

            if link_field not in link_properties:
                logger.error(f"The project datapoint {datapoint_name} contains the value {value} which is not an addressable field of the link {term}.{link}, allowed values are: {sorted(link_properties)}")
                return False

        elif value not in node_properties:

            logger.error(f"The project datapoint {datapoint_name} contains the value {value} which is not a property of the node {term} in the data dictionary")
            return False

    logger.info(f"The project datapoint {datapoint_name} is valid for the data dictionary")
    return True


def check_project_datapoints(session, data_dictionary_file_name="data_dictionary.json"):

    data_dictionary = _load_data_files(data_dictionary_file_name)

    data_dictionary_nodes = _get_data_dictionary_nodes(data_dictionary)

    project_datapoints = get_project_datapoints(session, throw_not_found=False, many=True, filter_by_active=False)

    for project_datapoint in project_datapoints:

        term = project_datapoint.term
        value_list = project_datapoint.value_list
        datapoint_name = f"{term} ({'whitelist' if project_datapoint.type == 'w' else 'blacklist'}) for project {project_datapoint.project_id}"

        separator_length = len(f"CHECKING PROJECT DATAPOINT: {datapoint_name} id: {project_datapoint.id}")
        logger.info("*" * separator_length)
        logger.info(f"CHECKING PROJECT DATAPOINT: {datapoint_name} id: {project_datapoint.id}")
        logger.info("*" * separator_length)
        logger.info(f"value_list: {value_list}")

        is_valid = _check_data_dictionary(term, value_list, datapoint_name, data_dictionary_nodes)

        message = f"term: {term} id: {project_datapoint.id}, is_valid was evaluated to {is_valid}, "

        if not is_valid:

            if project_datapoint.is_valid == True:

                message += "but is currently True updating is_valid to False in DB"

                update_project_datapoints(session, project_datapoint=project_datapoint, is_valid=False)

            else:

                message += "and is currently False doing nothing"

        else:

            if project_datapoint.is_valid == False:

                message += "but is currently False updating is_valid to True in DB"

                update_project_datapoints(session, project_datapoint=project_datapoint, is_valid=True)

            else:

                message += "and is currently True doing nothing"

        logger.info(message)

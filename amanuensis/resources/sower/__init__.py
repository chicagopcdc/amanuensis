"""
Helpers for triggering sower jobs (e.g. the pelican export job) from amanuensis.

Adapted from run_sower_job.py in the project_request_scripts repo.
"""
import requests
from cdislogging import get_logger
from urllib.parse import urlparse

from amanuensis.config import config
from amanuensis.errors import InternalError, UserError

logger = get_logger(__name__)


def build_export_input(ids_list=None, graphql_object=None):
    """
    Build the `filter` payload for a single Search/filterset, from its
    `ids_list` or `graphql_object` fields.

    An empty `ids_list` or an empty `graphql_object` does not describe a cohort,
    so it is not treated as a usable filter. When neither field describes one we
    raise rather than fall through to an empty filter, which Guppy would answer
    with the entire dataset.
    """
    has_ids = bool(ids_list)
    has_filter = bool(graphql_object)

    if not has_ids and not has_filter:
        raise UserError(
            "The filter set must provide either `ids_list` or `graphql_object`."
        )

    if has_ids:
        return {
            "AND": [
                {
                    "IN": {
                        "subject_submitter_id": ids_list
                    }
                }
            ]
        }

    return graphql_object


def build_export_inputs(searches):
    """
    Build one `filter` payload per Search associated with a data request.

    A project can have several associated searches; the export job unions them
    into a single cohort, so the whole list is sent rather than just the first.
    """
    if not searches:
        raise UserError("At least one filter set is required to export a project.")

    return [
        build_export_input(
            ids_list=search.ids_list, graphql_object=search.graphql_object
        )
        for search in searches
    ]


def run_export_job(
    headers,
    data_request_id,
    searches,
    consortium_name=None,
    project_code=None,
):
    """
    Trigger a sower export job for every search associated with a data request
    and return its job UID.
    """
    hostname = config["HOSTNAME"]

    if not urlparse(hostname).scheme:
        hostname = f"https://{hostname}"
    url = f"{hostname}/job/dispatch"

    export_filters = build_export_inputs(searches)

    payload = {
        "action": "export",
        "input": {
            # `filters` is the multi-search payload. `filter` carries the first
            # one for backwards compatibility, so this keeps working against a
            # pelican image that predates multi-search support - drop it once
            # every environment is on a pelican that reads `filters`.
            "filters": export_filters,
            "filter": export_filters[0],
            "data_request_id": data_request_id,
            "consortium_name": consortium_name,
            "project_code": project_code,
        },
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        logger.error(
            "Failed to dispatch sower export job. Status code: {}, body: {}".format(
                response.status_code, response.text
            )
        )
        raise InternalError("Failed to dispatch export job.")

    data = response.json()
    return data["uid"]

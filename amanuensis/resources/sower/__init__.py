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
    Build the `filter` payload to send to the sower export job, based on
    a Search/filterset's `ids_list` or `graphql_object` fields.
    """
    has_ids = ids_list is not None
    has_filter = graphql_object is not None

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


def run_export_job(headers, data_request_id, ids_list=None, graphql_object=None):
    """
    Trigger a sower export job and return its job UID.
    """
    hostname = config["HOSTNAME"]

    if not urlparse(hostname).scheme:
        hostname = f"https://{hostname}"
    url = f"{hostname}/job/dispatch"

    payload = {
        "action": "export",
        "input": {
            "filter": build_export_input(
                ids_list=ids_list, graphql_object=graphql_object
            ),
            "data_request_id": data_request_id,
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

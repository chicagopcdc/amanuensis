import collections
import json
import logging
import re
import string
from os import environ
from email.contentmanager import get_text_content
from functools import wraps
from random import SystemRandom
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit



import flask
import requests
from cdislogging import get_logger
import html2text
from userportaldatamodel.driver import SQLAlchemyDriver
from werkzeug.datastructures import ImmutableMultiDict

from amanuensis.auth.auth import get_jwt_from_header
from amanuensis.config import config
from amanuensis.errors import NotFound, UserError

from pcdc_aws_client.boto import BotoManager


rng = SystemRandom()
alphanumeric = string.ascii_uppercase + string.ascii_lowercase + string.digits
logger = get_logger(__name__)


def random_str(length):
    return "".join(rng.choice(alphanumeric) for _ in range(length))

def json_res(data):
    return flask.Response(json.dumps(data), mimetype="application/json")

def to_underscore(s):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

def strip(s):
    if isinstance(s, str):
        return s.strip()
    return s

def get_error_params(error, description):
    params = ""
    if error:
        args = {"error": error, "error_description": description}
        params = urlencode(args)
    return params

def append_query_params(original_url, **kwargs):
    """
    Add additional query string arguments to the given url.

    Example call:
        new_url = append_query_params(
            original_url, error='this is an error',
            another_arg='this is another argument')
    """
    scheme, netloc, path, query_string, fragment = urlsplit(original_url)
    query_params = parse_qs(query_string)
    if kwargs is not None:
        for key, value in kwargs.items():
            query_params[key] = [value]

    new_query_string = urlencode(query_params, doseq=True)
    new_url = urlunsplit((scheme, netloc, path, new_query_string, fragment))
    return new_url

def split_url_and_query_params(url):
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    url = urlunsplit((scheme, netloc, path, None, fragment))
    return url, query_params


# Convert filter obj into GQL filter format
# @param {object | undefined} filter

#TODO Consider importing it from data-portal or executing it in guppy instead of translating it here - https://medium.com/analytics-vidhya/run-javascript-from-python-c0fe8f8aeb1e
def getGQLFilter(src_filter):
    #TODO Translate filter to ES format
    # {
    #     "AND":[
    #         {
    #             "IN":{
    #                 "consortium":["INRG"]
    #             }
    #         }
    #     ]
    # }
    # FROM:
    # {
    #     "race": {
    #         "selectedValues": [
    #             "Black or African American"
    #         ]
    #     },
    #     "consortium": {
    #         "selectedValues": [
    #             "INRG"
    #         ]
    #     }
    # }

    # If filter is empty, not a dictionary or undefined
    # or not isinstance(filter, dict) ?? TODO check this 
    if (filter is None or not bool(filter)):
        return {}

    facetsList = []

    for field,filterValues in src_filter.items():
        fieldSplitted = field.split('.')
        fieldName = fieldSplitted[len(fieldSplitted) - 1]
        isRangeFilter = ('lowerBound' in filterValues and filterValues["lowerBound"]) or ('upperBound' in filterValues and filterValues["upperBound"])
        hasSelectedValues = len(filterValues["selectedValues"]) > 0 if filterValues and 'selectedValues' in filterValues else False

        if not isRangeFilter and not hasSelectedValues:
            if '__combineMode' in filterValues:
                # This filter only has a combine setting so far. We can ignore it.
                return None;
            else:
                raise UserError(
                    "Invalid filter object '{}'. ".format(filterValues)
                )

        # @type {{ AND?: any[]; IN?: { [x: string]: string[] }}} 
        facetsPiece = {}
        if isRangeFilter:
            facetsPiece["AND"] = [
                { '>=': { fieldName: filterValues["lowerBound"] } },
                { '<=': { fieldName: filterValues["upperBound"] } },
            ]
        elif hasSelectedValues:
            if '__combineMode' in filterValues and filterValues["__combineMode"] == 'AND':
                facetsPiece["AND"] = map(lambda selectedValue: { "IN": { fieldName: selectedValue },}, filterValues["selectedValues"])
            # combine mode defaults to OR when not set.
            else: 
                facetsPiece["IN"] = { fieldName: filterValues["selectedValues"] }

        facetsList.append(
            facetsPiece if len(fieldSplitted) == 1 else { "nested": { "path": '.'.join(fieldSplitted[0:-1]), **facetsPiece, }, }
        )
    

    return { "AND": facetsList }

def getGQLFilterIdsList(ids_list):
    # {
    #     "AND":[
    #         {
    #             "IN":{
    #                 "subject_submitter_id":["{subject_submitter_i}"]
    #             }
    #         }
    #     ]
    # }
    # ids_list = ["COG_0xA4CE42BAEAFFD85A5A573F7C0488647D", "COG_0x2B1D2E3C4648236211D982AA60BAC9BD", "COG_0xE23B0F16F4B158D1A417B2B422AEB303"]

    return { "AND": [{"IN":{"subject_submitter_id":ids_list}}]} 


    # if r.status_code == 200:
    #     return r.json()
    # return []

def _print_func_name(function):
    return "{}.{}".format(function.__module__, function.__name__)

def _print_kwargs(kwargs):
    return ", ".join("{}={}".format(k, repr(v)) for k, v in list(kwargs.items()))

def log_backoff_retry(details):
    args_str = ", ".join(map(str, details["args"]))
    kwargs_str = (
        (", " + _print_kwargs(details["kwargs"])) if details.get("kwargs") else ""
    )
    func_call_log = "{}({}{})".format(
        _print_func_name(details["target"]), args_str, kwargs_str
    )
    logging.warning(
        "backoff: call {func_call} delay {wait:0.1f} seconds after {tries} tries".format(
            func_call=func_call_log, **details
        )
    )


def log_backoff_giveup(details):
    args_str = ", ".join(map(str, details["args"]))
    kwargs_str = (
        (", " + _print_kwargs(details["kwargs"])) if details.get("kwargs") else ""
    )
    func_call_log = "{}({}{})".format(
        _print_func_name(details["target"]), args_str, kwargs_str
    )
    logging.error(
        "backoff: gave up call {func_call} after {tries} tries; exception: {exc}".format(
            func_call=func_call_log, exc=sys.exc_info(), **details
        )
    )

def exception_do_not_retry(error):
    def _is_status(code):
        return (
            str(getattr(error, "code", None)) == code
            or str(getattr(error, "status", None)) == code
            or str(getattr(error, "status_code", None)) == code
        )

    if _is_status("409") or _is_status("404"):
        return True

    return False

# Default settings to control usage of backoff library.
DEFAULT_BACKOFF_SETTINGS = {
    "on_backoff": log_backoff_retry,
    "on_giveup": log_backoff_giveup,
    "max_tries": 3,
    "giveup": exception_do_not_retry,
}

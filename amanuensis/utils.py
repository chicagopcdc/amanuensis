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


import bcrypt
import boto3
import flask
import requests
from cdislogging import get_logger
import html2text
from userportaldatamodel.driver import SQLAlchemyDriver
from werkzeug.datastructures import ImmutableMultiDict

from amanuensis.auth.auth import get_jwt_from_header
from amanuensis.config import config
from amanuensis.errors import NotFound, UserError
# from amanuensis.models import Client, User, query_for_user
from amanuensis.models import query_for_user

rng = SystemRandom()
alphanumeric = string.ascii_uppercase + string.ascii_lowercase + string.digits
logger = get_logger(__name__)


def random_str(length):
    return "".join(rng.choice(alphanumeric) for _ in range(length))


def json_res(data):
    return flask.Response(json.dumps(data), mimetype="application/json")


def create_client(
    username,
    urls,
    DB,
    name="",
    description="",
    auto_approve=False,
    is_admin=False,
    grant_types=None,
    confidential=True,
    arborist=None,
    policies=None,
    allowed_scopes=None,
):
    client_id = random_str(40)
    if arborist is not None:
        arborist.create_client(client_id, policies)
    grant_types = grant_types
    driver = SQLAlchemyDriver(DB)
    client_secret = None
    hashed_secret = None
    if confidential:
        client_secret = random_str(55)
        hashed_secret = bcrypt.hashpw(
            client_secret.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
    auth_method = "client_secret_basic" if confidential else "none"
    allowed_scopes = allowed_scopes
    if "openid" not in allowed_scopes:
        allowed_scopes.append("openid")
        logger.warning('Adding required "openid" scope to list of allowed scopes.')
    with driver.session as s:
        user = query_for_user(session=s, username=username)

        # if not user:
        #     user = User(username=username, is_admin=is_admin)
        #     s.add(user)
        if s.query(Client).filter(Client.name == name).first():
            if arborist is not None:
                arborist.delete_client(client_id)
            raise Exception("client {} already exists".format(name))
        # client = Client(
        #     client_id=client_id,
        #     client_secret=hashed_secret,
        #     user=user,
        #     redirect_uris=urls,
        #     _allowed_scopes=" ".join(allowed_scopes),
        #     description=description,
        #     name=name,
        #     auto_approve=auto_approve,
        #     grant_types=grant_types,
        #     is_confidential=confidential,
        #     token_endpoint_auth_method=auth_method,
        # )
        # s.add(client)
        # s.commit()
    return client_id, client_secret


def hash_secret(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        has_secret = "client_secret" in flask.request.form
        has_client_id = "client_id" in flask.request.form
        if flask.request.form and has_secret and has_client_id:
            form = flask.request.form.to_dict()
            with flask.current_app.db.session as session:
                client = (
                    session.query(Client)
                    .filter(Client.client_id == form["client_id"])
                    .first()
                )
                if client:
                    form["client_secret"] = bcrypt.hashpw(
                        form["client_secret"].encode("utf-8"),
                        client.client_secret.encode("utf-8"),
                    ).decode("utf-8")
                flask.request.form = ImmutableMultiDict(form)

        return f(*args, **kwargs)

    return wrapper


def wrap_list_required(f):
    @wraps(f)
    def wrapper(d, *args, **kwargs):
        data_is_a_list = False
        if isinstance(d, list):
            d = {"data": d}
            data_is_a_list = True
        if not data_is_a_list:
            return f(d, *args, **kwargs)
        else:
            result = f(d, *args, **kwargs)
            return result["data"]

    return wrapper


@wrap_list_required
def convert_key(d, converter):
    if isinstance(d, str) or not isinstance(d, collections.Iterable):
        return d

    new = {}
    for k, v in d.items():
        new_v = v
        if isinstance(v, dict):
            new_v = convert_key(v, converter)
        elif isinstance(v, list):
            new_v = list()
            for x in v:
                new_v.append(convert_key(x, converter))
        new[converter(k)] = new_v
    return new


@wrap_list_required
def convert_value(d, converter):
    if isinstance(d, str) or not isinstance(d, collections.Iterable):
        return converter(d)

    new = {}
    for k, v in d.items():
        new_v = v
        if isinstance(v, dict):
            new_v = convert_value(v, converter)
        elif isinstance(v, list):
            new_v = list()
            for x in v:
                new_v.append(convert_value(x, converter))
        new[k] = converter(new_v)
    return new


def to_underscore(s):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def strip(s):
    if isinstance(s, str):
        return s.strip()
    return s


def clear_cookies(response):
    """
    Set all cookies to empty and expired.
    """
    for cookie_name in list(flask.request.cookies.keys()):
        response.set_cookie(cookie_name, "", expires=0, httponly=True)


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



def get_consortium_list(path, src_filter):
    transformed_filter = getGQLFilter(src_filter)
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

        print("LUCA PRIMNTTTTTTTTTT")
    except requests.HTTPError as e:
        print(e.message)

    return r.json()
    # if r.status_code == 200:
    #     return r.json()
    # return []


def send_email(from_email, to_emails, subject, text, smtp_domain):
    """
    Send email to group of emails using mail gun api.

    https://app.mailgun.com/

    Args:
        from_email(str): from email
        to_emails(list): list of emails to receive the messages
        text(str): the text message
        smtp_domain(dict): smtp domain server

            {
                "smtp_hostname": "smtp.mailgun.org",
                "default_login": "postmaster@mailgun.planx-pla.net",
                "api_url": "https://api.mailgun.net/v3/mailgun.planx-pla.net",
                "smtp_password": "password",
                "api_key": "api key"
            }

    Returns:
        Http response

    Exceptions:
        KeyError

    """
    if smtp_domain not in config["GUN_MAIL"] or not config["GUN_MAIL"].get(
        smtp_domain
    ).get("smtp_password"):
        raise NotFound(
            "SMTP Domain '{}' does not exist in configuration for GUN_MAIL or "
            "smtp_password was not provided. "
            "Cannot send email.".format(smtp_domain)
        )

    api_key = config["GUN_MAIL"][smtp_domain].get("api_key", "")
    email_url = config["GUN_MAIL"][smtp_domain].get("api_url", "") + "/messages"

    return requests.post(
        email_url,
        auth=("api", api_key),
        data={"from": from_email, "to": to_emails, "subject": subject, "text": text},
    )


def send_email_ses(body, to_emails, subject):
    """
    Send email to group of emails using AWS SES api.

    Args:
        body: html or text message
        to_emails(list): list of emails to receive the messages
        subject(str): email subject
        smtp_domain(dict): smtp domain server

    Returns:
        Http response

    Exceptions:
        KeyError

    """

    # DON'T SEND EMAILS IN DEBUG MODE
    if bool(environ.get('GEN3_DEBUG')):
        response = {
            'MessageId': 12345,
        }
        logger.info("send_email_ses:  Success!")
        return response


    #TODO add import for boto

    if not config["AWS_SES"]:
        raise NotFound("AWS SES '{}' does not exist in configuration. Cannot send email.")
    if "SENDER" not in config["AWS_SES"]:
        raise NotFound("AWS SES sender does not exist in configuration. Cannot send email.")
    if "AWS_ACCESS_KEY" not in config["AWS_SES"] or "AWS_SECRET_KEY" not in config["AWS_SES"]:
        raise NotFound("AWS SES credentials are missing in configuration. Cannot send email.")

    #TODO retrieve body from template (pass as external param above)
    if not body:
        raise Exception('You must provide a text or html body.')
    if not subject:
        raise Exception('You must provide a text subject for the email.')

    sender = config["AWS_SES"]["SENDER"]
    region = config["AWS_SES"]["AWS_REGION"] if config["AWS_SES"]["AWS_REGION"] is not None else "us-east-1"
    AWS_ACCESS_KEY = config["AWS_SES"]["AWS_ACCESS_KEY"]
    AWS_SECRET_KEY = config["AWS_SES"]["AWS_SECRET_KEY"]
    
    # if body is in html format, strip out html markup
    # otherwise body and body_text could have the same values
    body_text = html2text.html2text(body)
    
        
        # if not self._html:
        #     self._format = 'text'
        #     body = self._text

    client = boto3.client(
        'ses',
        region_name=region,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': to_emails,
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': body_text,
                    },
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': body,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=sender,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    logging.debug(json.dumps(response))
    return response


def is_valid_expiration(expires_in):
    """
    Throw an error if expires_in is not a positive integer.
    """
    try:
        expires_in = int(flask.request.args["expires_in"])
        assert expires_in > 0
    except (ValueError, AssertionError):
        raise UserError("expires_in must be a positive integer")


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

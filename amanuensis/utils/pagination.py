import math
from urllib.parse import urlencode

import flask

from amanuensis.errors import UserError


#TODO pass the request as an argument and don't extract it here from the flask object. 
def parse_page_and_per_page(default_per_page, max_per_page):
    """
    Parse pagination query params when present.

    Returns None if neither ``page`` nor ``per_page`` is in the query string
    (caller should return all results). Otherwise returns (page, per_page).
    """
    if "page" not in flask.request.args and "per_page" not in flask.request.args:
        return None

    try:
        page = int(flask.request.args.get("page", 1))
        per_page = int(flask.request.args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        raise UserError("page and per_page must be integers")
    if page < 1:
        raise UserError("page must be greater than or equal to 1")
    if per_page < 1 or per_page > max_per_page:
        raise UserError(f"per_page must be between 1 and {max_per_page}")
    return page, per_page

def build_link_header(page, per_page, total, extra_query_params=None):
    """Link header: first, prev, next, last."""
    if total == 0:
        return None

    total_pages = max(1, math.ceil(total / per_page))

    base_query = {"page": page, "per_page": per_page}
    if extra_query_params:
        for key, value in extra_query_params.items():
            if value is not None:
                base_query[key] = value
    
    def page_url(requested_page):
        query = dict(base_query)
        query["page"] = requested_page
        return f"{flask.request.path}?{urlencode(query)}"

    links = [(page_url(1), "first")]
    if page > 1:
        links.append((page_url(page - 1), "prev"))
    if page < total_pages:
        links.append((page_url(page + 1), "next"))
    links.append((page_url(total_pages), "last"))
    return ", ".join(f'<{url}>; rel="{rel}"' for url, rel in links)


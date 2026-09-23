import pytest
from unittest.mock import MagicMock, patch
import flask
import json
import os

from amanuensis.errors import InternalError, UserError
from amanuensis.models import ProjectDataPoints
from amanuensis.resources.project_datapoints import (
    _get_data_dictionary_nodes,
    _get_link_properties,
    _check_data_dictionary,
    check_project_datapoints,
)
from amanuensis.resources.userdatamodel.project import create_project
from amanuensis.scripting.validate_project_datapoints import main


def _link_property(*fields):
    """Shape the data dictionary uses for a link property."""
    return {
        "anyOf": [
            {"items": {"properties": {field: {} for field in fields}}},
            {"properties": {field: {} for field in fields}},
        ]
    }


DATA_DICTIONARY = {
    "_definitions": {"not": "a node"},
    "_terms": {"not": "a node"},
    "_settings": {"not": "a node"},
    # the portal offers metaschema as a table, so the job has to accept it too
    "metaschema": {"id": "metaschema", "properties": {"category": {}}},
    "person": {
        "id": "person",
        "properties": {
            "type": {},
            "submitter_id": {},
            "sex": {},
            "race": {},
            "projects": _link_property("id", "submitter_id"),
        }
    },
    "subject": {
        "id": "subject",
        "properties": {
            "type": {},
            "submitter_id": {},
            "consortium": {},
            "persons": _link_property("id", "submitter_id"),
        }
    },
    "histology": {
        "id": "histology",
        "properties": {
            "type": {},
            "submitter_id": {},
            "histology": {},
            "subjects": _link_property("id", "submitter_id"),
            "timings": _link_property("id", "submitter_id"),
        }
    },
    "node_without_properties": {"id": "node_without_properties"},
    "node_without_id": {"properties": {"type": {}}},
}


@pytest.fixture(scope="module", autouse=True)
def data_dictionary_file():
    """
    The job reads the data dictionary the same way the filter-set job reads
    es_to_dd_map.json, out of CONFIG_SEARCH_FOLDERS.
    """
    path = os.path.expanduser("~/.gen3/amanuensis/data_dictionary.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        f.write(json.dumps(DATA_DICTIONARY))

    yield path

    os.remove(path)


@pytest.fixture(scope="module", autouse=True)
def s3(app_instance):
    """
    Nothing here touches s3, so override the conftest fixture that reaches out to
    a real bucket.
    """
    mock_s3_client = MagicMock()
    mock_s3_client.create_bucket.return_value = None
    mock_s3_client.list_buckets.return_value = {'Buckets': []}
    mock_s3_client.delete_object.return_value = None
    mock_s3_client.list_objects_v2.return_value = {'Contents': []}

    with patch.object(app_instance.s3_boto, 's3_client', mock_s3_client):
        yield mock_s3_client


@pytest.fixture(scope="module", autouse=True)
def admin_user(register_user):
    admin_id, admin_email = register_user(email="admin@test_validate_project_datapoints.com", name="admin", role="admin")
    yield admin_id, admin_email


@pytest.fixture(scope="function")
def gen_project(login, admin_user):
    def _make_project(name):
        login(admin_user[0], admin_user[1])

        with flask.current_app.db.session as session:
            project = create_project(
                session,
                name=name,
                description=name,
                institution=name,
                user_id=admin_user[0],
            )
        return project.id

    yield _make_project


pytest.mark.order(1)
def test__get_data_dictionary_nodes():
    nodes = _get_data_dictionary_nodes(DATA_DICTIONARY)

    # a node carries an id and at least one property, which is the same rule the
    # data portal uses to build the select attributes tables
    assert set(nodes.keys()) == {"person", "subject", "histology", "metaschema"}

    with pytest.raises(InternalError):
        _get_data_dictionary_nodes({"_definitions": {}, "_terms": {}})


pytest.mark.order(2)
def test__get_link_properties():
    assert _get_link_properties(_link_property("id", "submitter_id")) == {"id", "submitter_id"}

    # a plain scalar property is not a link
    assert _get_link_properties({"type": "string"}) is None
    assert _get_link_properties({"enum": ["INRG"]}) is None
    assert _get_link_properties({"anyOf": "not a list"}) is None
    assert _get_link_properties("not a dict") is None


pytest.mark.order(3)
def test__check_data_dictionary():
    nodes = _get_data_dictionary_nodes(DATA_DICTIONARY)

    # plain properties
    assert _check_data_dictionary("person", ["type", "submitter_id", "sex", "race"], "valid", nodes)

    # link properties
    assert _check_data_dictionary("histology", ["histology", "subjects.submitter_id", "timings.id"], "valid_links", nodes)

    # an empty value list has nothing to go stale
    assert _check_data_dictionary("person", [], "empty", nodes)

    # the node was removed or renamed in the data dictionary
    assert _check_data_dictionary("not_a_node", ["type"], "bad_node", nodes) == False

    # entries without properties or without an id are not nodes
    assert _check_data_dictionary("node_without_properties", ["type"], "no_properties", nodes) == False
    assert _check_data_dictionary("node_without_id", ["type"], "no_id", nodes) == False

    # a property was removed or renamed in the data dictionary
    assert _check_data_dictionary("person", ["type", "not_a_property"], "bad_property", nodes) == False

    # the link itself was removed, which is the drift seen on real configs
    assert _check_data_dictionary("person", ["timings.submitter_id"], "bad_link", nodes) == False

    # the name resolves, but it is a scalar property rather than a link
    assert _check_data_dictionary("person", ["sex.submitter_id"], "not_a_link", nodes) == False

    # the link exists but the addressed field on the other side does not
    assert _check_data_dictionary("person", ["projects.not_a_field"], "bad_link_field", nodes) == False

    # value lists hold strings
    assert _check_data_dictionary("person", [42], "not_a_string", nodes) == False


pytest.mark.order(4)
def test_check_project_datapoints(session,
                                  pytestconfig,
                                  gen_project,
                                  admin_add_project_datapoints_post,
                                  admin_user,
                                  login):
    project_id = gen_project(name="test_check_project_datapoints")

    login(admin_user[0], admin_user[1])

    valid_whitelist = admin_add_project_datapoints_post(
        authorization_token=admin_user[0],
        term="person",
        value_list=["type", "submitter_id", "sex", "projects.submitter_id"],
        type="w",
        project_id=project_id,
    ).get_json()["id"]

    invalid_node = admin_add_project_datapoints_post(
        authorization_token=admin_user[0],
        term="not_a_node",
        value_list=["type"],
        type="w",
        project_id=project_id,
    ).get_json()["id"]

    invalid_value = admin_add_project_datapoints_post(
        authorization_token=admin_user[0],
        term="subject",
        value_list=["type", "was_renamed_in_the_data_dictionary"],
        type="w",
        project_id=project_id,
    ).get_json()["id"]

    # a blacklist that no longer matches is a leak, not a no-op, so it is checked too
    invalid_blacklist = admin_add_project_datapoints_post(
        authorization_token=admin_user[0],
        term="histology",
        value_list=["subjects.id", "timings.not_a_field"],
        type="b",
        project_id=project_id,
    ).get_json()["id"]

    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == valid_whitelist).first().is_valid
    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == invalid_node).first().is_valid == False
    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == invalid_value).first().is_valid == False
    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == invalid_blacklist).first().is_valid == False


pytest.mark.order(5)
def test_check_project_datapoints_covers_inactive_rows(session,
                                                       pytestconfig,
                                                       gen_project,
                                                       admin_add_project_datapoints_post,
                                                       admin_delete_project_datapoints_delete,
                                                       admin_user,
                                                       login):
    """
    Deleting a datapoint only flips active to False, so the row survives and can
    still be reactivated later. It has to be validated like any other row.
    """
    project_id = gen_project(name="test_check_project_datapoints_covers_inactive_rows")

    login(admin_user[0], admin_user[1])

    datapoint_id = admin_add_project_datapoints_post(
        authorization_token=admin_user[0],
        term="subject",
        value_list=["type", "was_renamed_in_the_data_dictionary"],
        type="w",
        project_id=project_id,
    ).get_json()["id"]

    admin_delete_project_datapoints_delete(authorization_token=admin_user[0], id=datapoint_id)

    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    datapoint = session.query(ProjectDataPoints).filter(ProjectDataPoints.id == datapoint_id).first()
    assert datapoint.active == False
    assert datapoint.is_valid == False


pytest.mark.order(6)
def test_manual_change_to_project_datapoint_auto_updates_is_valid(session,
                                                                  pytestconfig,
                                                                  gen_project,
                                                                  admin_add_project_datapoints_post,
                                                                  admin_modify_project_datapoints_put,
                                                                  admin_user,
                                                                  login):
    """
    An admin fixing a stale datapoint should not have to wait a day for the row
    to stop being flagged, and a fix that is still wrong must be re-flagged.
    """
    project_id = gen_project(name="test_manual_change_to_project_datapoint_auto_updates_is_valid")

    login(admin_user[0], admin_user[1])

    datapoint_id = admin_add_project_datapoints_post(
        authorization_token=admin_user[0],
        term="subject",
        value_list=["type", "was_renamed_in_the_data_dictionary"],
        type="w",
        project_id=project_id,
    ).get_json()["id"]

    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == datapoint_id).first().is_valid == False

    admin_modify_project_datapoints_put(
        authorization_token=admin_user[0],
        id=datapoint_id,
        value_list=["type", "consortium"],
    )

    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == datapoint_id).first().is_valid

    main(["--file_name", pytestconfig.getoption("--configuration-file")])

    assert session.query(ProjectDataPoints).filter(ProjectDataPoints.id == datapoint_id).first().is_valid


pytest.mark.order(7)
def test_check_project_datapoints_missing_data_dictionary(session):
    with pytest.raises(InternalError):
        check_project_datapoints(session, data_dictionary_file_name="not_real.json")

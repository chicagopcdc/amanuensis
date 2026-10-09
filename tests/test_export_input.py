import pytest

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from amanuensis.errors import UserError
from amanuensis.resources.sower import build_export_input, build_export_inputs


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


def search(ids_list=None, graphql_object=None):
    return SimpleNamespace(ids_list=ids_list, graphql_object=graphql_object)


def test_build_export_input_from_graphql_object():
    gql = {"AND": [{"IN": {"consortium": ["INRG"]}}]}

    assert build_export_input(graphql_object=gql) == gql


def test_build_export_input_from_ids_list():
    assert build_export_input(ids_list=["s1", "s2"]) == {
        "AND": [{"IN": {"subject_submitter_id": ["s1", "s2"]}}]
    }


def test_build_export_input_prefers_a_real_graphql_object_over_an_empty_ids_list():
    """
    create_filter_set stores an empty list/object rather than NULL, so an empty
    ids_list must not shadow the filter that actually describes the cohort.
    """
    gql = {"AND": [{"IN": {"consortium": ["INRG"]}}]}

    assert build_export_input(ids_list=[], graphql_object=gql) == gql


def test_build_export_input_rejects_a_filter_set_that_describes_no_cohort():
    """
    An empty filter would be answered by Guppy with the entire dataset, so a
    filter set carrying neither field is an error rather than an export of
    everything.
    """
    with pytest.raises(UserError):
        build_export_input(ids_list=[], graphql_object={})

    with pytest.raises(UserError):
        build_export_input(ids_list=None, graphql_object=None)


def test_build_export_inputs_returns_one_filter_per_search():
    first = {"AND": [{"IN": {"consortium": ["INRG"]}}]}
    second = {"AND": [{"IN": {"consortium": ["INSTRUCT"]}}]}

    assert build_export_inputs(
        [search(graphql_object=first), search(graphql_object=second)]
    ) == [first, second]


def test_build_export_inputs_mixes_ids_list_and_graphql_searches():
    gql = {"AND": [{"IN": {"consortium": ["INRG"]}}]}

    assert build_export_inputs(
        [search(ids_list=["s1"]), search(graphql_object=gql)]
    ) == [
        {"AND": [{"IN": {"subject_submitter_id": ["s1"]}}]},
        gql,
    ]


def test_build_export_inputs_rejects_an_empty_list_of_searches():
    with pytest.raises(UserError):
        build_export_inputs([])

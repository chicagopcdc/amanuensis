import pytest
from amanuensis.resources.userdatamodel import userdatamodel_filterset as filter_set
from amanuensis.models import *

def test_get_filter_sets(session, searches):
    data = filter_set.get_filter_sets(session, 1, False, [], 123)
    assert len(data) == 1
    assert data[0].id == searches[0].id

    data = filter_set.get_filter_sets(session, 2, True, [], 124)
    assert len(data) == 1
    assert data[0].id == searches[1].id

    #TODO
    # data = filter_set.get_filter_sets(session, 2, True, [searches[0], searches[1]], None)
    # assert len(data) == 2


def test_get_filter_sets_by_ids(session, searches):
    assert [] == filter_set.get_filter_sets_by_ids(session, [])
    data = filter_set.get_filter_sets_by_ids(session, [searches[0].id, searches[1].id])
    correct = [searches[0].id, searches[1].id]
    for search in data:
        if search.id not in correct:
            assert False
        else:
            correct.remove(search.id)
    assert True


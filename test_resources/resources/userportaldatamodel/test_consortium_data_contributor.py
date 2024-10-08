import pytest
from amanuensis.resources.userdatamodel.consortium_data_contributor import create_consortium, get_consortiums
from amanuensis.errors import NotFound, UserError
from amanuensis.models import ConsortiumDataContributor


def test_create_consortium(session):

    session.query(ConsortiumDataContributor).filter(ConsortiumDataContributor.code == f"{__name__}").delete()

    consortium = create_consortium(session, code=f"{__name__}", name=f"{__name__}")

    assert consortium.code == get_consortiums(session, code=f"{__name__}")[0].code

    assert consortium.name == get_consortiums(session, name=f"{__name__}", many=False).name


    session.commit()



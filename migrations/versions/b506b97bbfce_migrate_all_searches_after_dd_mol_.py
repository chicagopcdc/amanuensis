"""migrate_all_searches_after_dd_mol_analysis_changes

Revision ID: b506b97bbfce
Revises: 03ceab80c865
Create Date: 2022-10-20 08:49:09.830257

"""
from alembic import op
from sqlalchemy.orm.session import Session
import json

from userportaldatamodel.models import (Search)

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b506b97bbfce'
down_revision = '03ceab80c865'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Attach a sqlalchemy Session to the env connection
    session = Session(bind=conn)

    # query = session.query(Search).filter(
    #     # Search.filter_object.astext.like("%molecular_analysis.molecular_abnormality_result%")
    #     Search.filter_object.astext_type.like("%molecular_analysis.molecular_abnormality_result%")
    # )
    # searches = query.all()
    search_ids_raw = session.execute("SELECT id from search where filter_object::text like '%molecular_analysis.molecular_abnormality_result%'").fetchall()
    search_ids = [value for value, in search_ids_raw]

    query = session.query(Search).filter(
        # Search.filter_object.astext.like("%molecular_analysis.molecular_abnormality_result%")
        Search.id.in_(search_ids)
    )
    searches = query.all()

    for search in searches:
        filter_object = search.filter_object
        graphql_object = search.graphql_object

        ### START FILTER OBJECT UPDATE
        # TODO place positive negative with Present, Absent
        filter_object_str = json.dumps(filter_object)

        #Loop over string to find all the iterations of `molecular_analysis.molecular_abnormality_result`
        i = True
        start = 0
        end = len(filter_object_str)
        indexes = []
        while i:
            ret = filter_object_str.find("molecular_analysis.molecular_abnormality_result", start, end)
            if ret == -1:
                i = False
            else:
                indexes.append(ret)
                start = ret + 1
        indexes.reverse()

        #Replace all the instances starting from the end to avoid screwing the indexes
        for index in indexes:
            # lenght of max between old ("molecular_analysis.molecular_abnormality_result": {"selectedValues": ["Positive"]) and new (molecular_analysis.molecular_abnormality_result": {"__type": "OPTION", "selectedValues": ["Positive"]) format
            block_size = 100
            is_negative = True
            replace_idx = filter_object_str.find("Negative", index, index + block_size)
            if replace_idx == -1:
                is_negative = False
                replace_idx = filter_object_str.find("Positive", index, index + block_size)
            if replace_idx == -1:
                print("No obselete value found at index in substring: {}".format(filter_object_str[index:index + block_size]))
                continue
    
            filter_object_str = filter_object_str[:replace_idx] + filter_object_str[replace_idx:replace_idx + 8].replace("Negative" if is_negative else "Positive", "Absent" if is_negative else "Present") + filter_object_str[replace_idx + 8:]
    
        filter_object = json.loads(filter_object_str)
        print(filter_object_str)
        search.filter_object = filter_object
        ### END FILTER OBJECT UPDATE

        ### START GRAPHQL OBJECT UPDATE
        if graphql_object is None:
            graphql_object = {}
        graphql_object_str = json.dumps(graphql_object)

        i = True
        start = 0
        end = len(graphql_object_str)
        indexes = []
        while i:
            ret = graphql_object_str.find("molecular_abnormality_result", start, end)
            if ret == -1:
                i = False
            else:
                indexes.append(ret)
                start = ret + 1
        indexes.reverse()

        for index in indexes:
            # lenght of `molecular_abnormality_result": ["Negative"]}}`
            block_size = 45
            is_negative = True
            replace_idx = graphql_object_str.find("Negative", index, index + block_size)
            if replace_idx == -1:
                is_negative = False
                replace_idx = graphql_object_str.find("Positive", index, index + block_size)
            if replace_idx == -1:
                continue
            
            graphql_object_str = graphql_object_str[:replace_idx] + graphql_object_str[replace_idx:replace_idx+8].replace("Negative" if is_negative else "Positive", "Absent" if is_negative else "Present") + graphql_object_str[replace_idx+8:]
            
        graphql_object_str = json.loads(graphql_object_str)
        print(graphql_object_str)
        search.graphql_object = graphql_object
        ### END GRAPHQL OBJECT UPDATE
        
        # session.flush()
    session.commit()



def downgrade() -> None:
    conn = op.get_bind()
    # Attach a sqlalchemy Session to the env connection
    session = Session(bind=conn)

    search_ids_raw = session.execute("SELECT id from search where filter_object::text like '%molecular_analysis.molecular_abnormality_result%'").fetchall()
    search_ids = [value for value, in search_ids_raw]

    query = session.query(Search).filter(
        # Search.filter_object.astext.like("%molecular_analysis.molecular_abnormality_result%")
        Search.id.in_(search_ids)
    )
    searches = query.all()

    for search in searches:
        filter_object = search.filter_object
        graphql_object = search.graphql_object

        ### START FILTER OBJECT UPDATE
        # TODO place positive negative with Present, Absent
        filter_object_str = json.dumps(filter_object)

        #Loop over string to find all the iterations of `molecular_analysis.molecular_abnormality_result`
        i = True
        start = 0
        end = len(filter_object_str)
        indexes = []
        while i:
            ret = filter_object_str.find("molecular_analysis.molecular_abnormality_result", start, end)
            if ret == -1:
                i = False
            else:
                indexes.append(ret)
                start = ret + 1
        indexes.reverse()

        #Replace all the instances starting from the end to avoid screwing the indexes
        for index in indexes:
            # lenght of max between old ("molecular_analysis.molecular_abnormality_result": {"selectedValues": ["Positive"]) and new (molecular_analysis.molecular_abnormality_result": {"__type": "OPTION", "selectedValues": ["Positive"]) format
            block_size = 100
            is_negative = True
            replace_idx = filter_object_str.find("Absent", index, index + block_size)
            if replace_idx == -1:
                is_negative = False
                replace_idx = filter_object_str.find("Present", index, index + block_size)
            if replace_idx == -1:
                print("No obselete value found at index in substring: {}".format(filter_object_str[index:index + block_size]))
                continue
    
            filter_object_str = filter_object_str[:replace_idx] + filter_object_str[replace_idx:replace_idx + 8].replace("Absent" if is_negative else "Present", "Negative" if is_negative else "Positive") + filter_object_str[replace_idx + 8:]
    
        filter_object = json.loads(filter_object_str)
        print(filter_object_str)
        search.filter_object = filter_object
        ### END FILTER OBJECT UPDATE

        ### START GRAPHQL OBJECT UPDATE
        if graphql_object is None:
            graphql_object = {}
        graphql_object_str = json.dumps(graphql_object)

        i = True
        start = 0
        end = len(graphql_object_str)
        indexes = []
        while i:
            ret = graphql_object_str.find("molecular_abnormality_result", start, end)
            if ret == -1:
                i = False
            else:
                indexes.append(ret)
                start = ret + 1
        indexes.reverse()

        for index in indexes:
            # lenght of `molecular_abnormality_result": ["Negative"]}}`
            block_size = 45
            is_negative = True
            replace_idx = graphql_object_str.find("Absent", index, index + block_size)
            if replace_idx == -1:
                is_negative = False
                replace_idx = graphql_object_str.find("Present", index, index + block_size)
            if replace_idx == -1:
                continue
            
            graphql_object_str = graphql_object_str[:replace_idx] + graphql_object_str[replace_idx:replace_idx+8].replace("Absent" if is_negative else "Present", "Negative" if is_negative else "Positive") + graphql_object_str[replace_idx+8:]
            
        graphql_object_str = json.loads(graphql_object_str)
        print(graphql_object_str)
        search.graphql_object = graphql_object
        ### END GRAPHQL OBJECT UPDATE
        
        # session.flush()
    session.commit()



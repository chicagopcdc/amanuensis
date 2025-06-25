"""update_filters_from_old_version

Revision ID: fca96219902c
Revises: c6059263d6b9
Create Date: 2025-05-29 15:18:46.492260

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from userportaldatamodel.models import (Search)
from cdislogging import get_logger
logger = get_logger(__name__)
# revision identifiers, used by Alembic.
revision = 'fca96219902c'
down_revision = 'c6059263d6b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    #write a query to 
    conn = op.get_bind()
    session = Session(bind=conn)
    searches = session.query(Search.id, Search.filter_object, Search.name).all()

    updates = []

    def option_filter_setter(selected_filter):
        """Helper function to set the filter_object for OPTION type filters."""
        return {
            "__type": "OPTION",
            "isExclusion": selected_filter.get("isExclusion", False),
            "selectedValues": selected_filter["selectedValues"]
        }
    
    def range_filter_setter(selected_filter):
        """Helper function to set the filter_object for RANGE type filters."""
        return {
            "__type": "RANGE",
            "lowerBound": selected_filter["lowerBound"],
            "upperBound": selected_filter["upperBound"]
        }

    def anchor_filter_setter(selected_filter):
        """Helper function to set the filter_object for ANCHOR type filters."""
        return {
            "__type": "ANCHOR",
            "value": proccess_filter_object(selected_filter["filter"])
        }

    def proccess_filter_object(filter_object):
        selected_filters = {}  
        for key, value in filter_object.items():
            if "disease_phase" in key:
                # Handle disease_phase filters with anchor type
                selected_filters[key] = anchor_filter_setter(value)
            elif "selectedValues" in value:
                selected_filters[key] = option_filter_setter(value)
            elif "lowerBound" in value or "upperBound" in value:
                selected_filters[key] = range_filter_setter(value)
            else:
                raise ValueError(f"Unknown filter type for key: {key} with value: {value}")

        return selected_filters

    for search_id, filter_obj, name in searches:
        if filter_obj and "value" not in filter_obj:
            try:
                new_filter_object = {}
                old_filter_object = filter_obj.copy()
                if "__type" in old_filter_object:
                    new_filter_object["__type"] = old_filter_object["__type"]
                    old_filter_object.pop("__type")
                else:
                    new_filter_object["__type"] = "STANDARD"
                
                if "__combineMode" in old_filter_object:
                    new_filter_object["__combineMode"] = old_filter_object["__combineMode"]
                    old_filter_object.pop("__combineMode")
                else:
                    new_filter_object["__combineMode"] = "AND"
            
                new_filter_object["value"] = proccess_filter_object(old_filter_object)
            
            except Exception as e:
                print(f"Error processing search {name}: {e}")
                continue
        
            updates.append((search_id, new_filter_object, filter_obj))
    
    for search_id, new_filter, filter_obj in updates:
        logger.info(f"Updating search {search_id} with new filter object: {new_filter} from old filter object: {filter_obj}")
        session.query(Search).filter(Search.id == search_id).update(
            {"filter_object": new_filter}
        )
            




    session.commit()
        
            
def downgrade() -> None:
    pass

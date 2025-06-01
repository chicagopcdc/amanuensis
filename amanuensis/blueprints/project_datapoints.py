"""
Blueprints for accessing the datapoints table.
"""



from flask import request, Blueprint, current_app, jsonify
from cdislogging import get_logger

from amanuensis.errors import UserError, AuthError
from amanuensis.resources.userdatamodel.project_datapoints import get_project_datapoints, update_project_datapoints, create_project_datapoints

from amanuensis.schema import (
    ProjectDataPointsSchema
)

logger = get_logger(__name__)

blueprint = Blueprint("project-datapoints",__name__)

#TODO: implement debug log function

@blueprint.route("/delete-datapoints", methods = ["DELETE"])
def delete_datapoints():
    """
    deletes a datapoints

    returns a json object
    """

    id = request.get_json().get("id",None)
    
    if not id:
        raise UserError("A, id is required for this endpoint")
    
    with current_app.db.session as session:

        project_datapoints_schema = ProjectDataPointsSchema()
        
        project_datapoints = update_project_datapoints(session, id, delete=True)

        session.commit()

        return jsonify(project_datapoints_schema.dump(project_datapoints))

@blueprint.route("/modify-datapoints", methods = ["POST"])
def modify_datapoints():
    id = request.get_json().get("id",None)
    term = request.get_json().get("term",None)
    value_list = request.get_json().get("value_list",None)
    type = request.get_json().get("type",None)
    project_id = request.get_json().get("project_id",None)

    project_datapoints_schema = ProjectDataPointsSchema()

    with current_app.db.session as session:
        if not id:
            raise UserError("must provide project_datapoints id")

        project_datapoints = update_project_datapoints(session,id,term,value_list,project_id,type,delete=False)

        session.commit()

        return jsonify(project_datapoints_schema.dump(project_datapoints))

@blueprint.route("/add-datapoints", methods = ["POST"])
def add_datapoints():
    """
    creates a new datapoints for the project_datapoints table

    returns a json object
    """
    
    term = request.get_json().get("term",None)
    value_list = request.get_json().get("value_list",None)
    type = request.get_json().get("type",None)
    project_id = request.get_json().get("project_id",None)

    project_datapoints_schema = ProjectDataPointsSchema()

    with current_app.db.session as session:
        project_datapoints = create_project_datapoints(session,term,value_list,type,project_id)

        session.commit()

        return jsonify(project_datapoints_schema.dump(project_datapoints))

@blueprint.route("/get-datapoints-with-id",methods = ["GET"])
def get_datapoints_with_id():
    id = request.get_json().get("id",None)
    term = request.get_json().get("term",None)
    type = request.get_json().get("type",None)
    project_id = request.get_json().get("project_id",None)

    if id is None:
        raise UserError("get_datapoints_with_id function requires datapoints table id")

    with current_app.db.session as session:

        project_datapoints_schema = ProjectDataPointsSchema()

        project_datapoints = get_project_datapoints(session,term,id,project_id,type)

        return jsonify(project_datapoints_schema.dump(project_datapoints))

@blueprint.route("/get-datapoints-with-term",methods = ["GET"])
def get_datapoints_with_term():
    id = request.get_json().get("id",None)
    term = request.get_json().get("term",None)
    type = request.get_json().get("type",None)
    project_id = request.get_json().get("project_id",None)

    if term is None:
        raise UserError("get_datapoints_with_id function requires datapoints table term")

    with current_app.db.session as session:

        project_datapoints_schema = ProjectDataPointsSchema()

        project_datapoints = get_project_datapoints(session,term,id,project_id,type,many=True)

        return jsonify(project_datapoints_schema.dump(project_datapoints,many=True))


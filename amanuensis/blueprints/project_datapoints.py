"""
Blueprints for accessing the datapoints table.
"""
from psycopg2.errors import ForeignKeyViolation
from sqlalchemy.exc import IntegrityError
from flask import request, Blueprint, current_app, jsonify
from cdislogging import get_logger

from amanuensis.errors import UserError, AuthError
from amanuensis.resources.userdatamodel.project_datapoints import get_project_datapoints, update_project_datapoints, create_project_datapoints, reactivate_datapoint
from amanuensis.auth.auth import check_arborist_auth

from amanuensis.schema import (
    ProjectDataPointsSchema
)

logger = get_logger(__name__)

blueprint = Blueprint("project-datapoints",__name__)

#TODO: implement debug log function

@check_arborist_auth(resource="/services/amanuensis", method="*")
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

@check_arborist_auth(resource="/services/amanuensis", method="*")
@blueprint.route("/modify-datapoints", methods = ["POST"])
def modify_datapoints():
    """
    modifies an existing datapoint

    returns a json object
    """
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

@check_arborist_auth(resource="/services/amanuensis", method="*")
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

    if not isinstance(value_list, list):
        raise UserError(f"Expected a list for value_list value")
    if not isinstance(type, str):
        raise UserError(f"Expected a string for type value")
    if not isinstance(term, str):
        raise UserError(f"Expected a string for term value")
    if not isinstance(project_id, int):
        raise UserError(f"Expected an integer for project_id")


    project_datapoints_schema = ProjectDataPointsSchema()

    with current_app.db.session as session:
        try:
            project_datapoints = create_project_datapoints(session, term, value_list, type, project_id)
            session.commit()
            return jsonify(project_datapoints_schema.dump(project_datapoints))

        except IntegrityError as e:
            session.rollback()
            if isinstance(e.orig, ForeignKeyViolation):
                raise UserError("Invalid project_id: project does not exist")  # will be returned as 400
            raise
 
@check_arborist_auth(resource="/services/amanuensis", method="*")
@blueprint.route("/get-datapoints",methods = ["GET"])
def get_datapoints():
    id = request.get_json().get("id",None)
    term = request.get_json().get("term",None)
    type = request.get_json().get("type",None)
    project_id = request.get_json().get("project_id",None)
    many = request.get_json().get("many",None)

    with current_app.db.session as session:

        project_datapoints_schema = None

        project_datapoints = get_project_datapoints(session,term,id,project_id,type,many = many)

        if isinstance(project_datapoints, list):
            project_datapoints_schema = ProjectDataPointsSchema(many=True)
        elif project_datapoints is None:
            return jsonify([])  # or 404, or custom message
        else:
            project_datapoints_schema = ProjectDataPointsSchema()


        return jsonify(project_datapoints_schema.dump(project_datapoints))

@check_arborist_auth(resource="/services/amanuensis", method="*")
@blueprint.route("/reactivate-datapoints",methods = ["POST"])
def reactivate_datapoints():
    """
    used with an input of a project_datapoint id

    reactivates a datapoint that has previously been deleted

    returns a json object
    """

    id = request.get_json().get("id",None)

    project_datapoints_schema = ProjectDataPointsSchema()

    with current_app.db.session as session:
        project_datapoints = reactivate_datapoint(session,id)

        session.commit()

        return jsonify(project_datapoints_schema.dump(project_datapoints))


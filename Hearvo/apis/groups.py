import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt
import hashlib
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, User, UserGETSchema, UserInfo, UserInfoGETSchema,Group,UserInfoGroup, GroupSchema
from Hearvo.middlewares.detect_language import get_lang_id
from .logger_api import logger_api

def create_link(user_info_id, group_name, created_at):
  input_txt = group_name + str(user_info_id) + created_at
  hash_object = hashlib.sha256(input_txt.encode("utf-8"))
  hex_dig = hash_object.hexdigest()
  return hex_dig

#########################################
# Schema
#########################################
# group_schema = UserInfoGETSchema()
groups_info_schema = GroupSchema(many=True)

#########################################
# Routes to handle API
#########################################
class GroupResource(Resource):
  @jwt_required
  def get(self):
    """
    get groups that the user has joined
    """
    user_info_id = get_jwt_identity()

    try:
        data = UserInfoGroup.query.filter_by(user_info_id=user_info_id).all()
        all_group_id = [x.group_id for x in data]
        fetched_groups = Group.query.filter(Group.id.in_(all_group_id)).all()
        status_code = 200
        return groups_info_schema.dump(fetched_groups), status_code
    except:
        status_code = 400
        db.session.rollback()
        return {}, status_code


  @jwt_required
  def post(self):
    """
    add a new group
    """
    title = request.json["title"]
    user_info_id = get_jwt_identity()
    current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

    try:
        link = create_link(user_info_id, title, current_datetime)
        new_group = Group(
          user_info_id=user_info_id,
          title=title,
          link=link,
          created_at=current_datetime,
          num_of_users=1
        )
        db.session.add(new_group)
        db.session.flush()
        group_id = new_group.id

        new_user_info_group = UserInfoGroup(
          user_info_id=user_info_id,
          group_id=group_id,
          created_at=current_datetime
        )
        db.session.add(new_user_info_group)
        db.session.commit()
        status_code = 200
        return {"message": "Successfully created a new group.", "link": link}, status_code
    except:
        status_code = 400
        db.session.rollback()
        return {"message": "Failed to create a new group."}, status_code

  


class GroupUserInfoResource(Resource):
  @jwt_required
  def post(self):
    """
    add a new user to the group.
    """
    link = request.json["link"]
    user_info_id = get_jwt_identity()
    current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

    # Check if the group exists
    group_obj = Group.query.filter_by(link=link).first()
    if group_obj is None:
      status_code = 400
      return {"message": "Failed to add a user."}, status_code

    # Check if the user has already joined the group
    is_duplicated = UserInfoGroup.query.filter_by(user_info_id=user_info_id).first()
    if is_duplicated:
      status_code = 400
      return {"message": "This user already exists."}, status_code

    try:
        group_id = group_obj.id
        user_info_group = UserInfoGroup(user_info_id=user_info_id, group_id=group_id)
        db.session.add(user_info_group)
        db.session.commit()
        status_code = 200
        return {"message": "Successfully add a user to the group."}, status_code
    except:
        status_code = 400
        db.session.rollback()
        return {"message": "Failed to add a user."}, status_code

  @jwt_required
  def delete(self):
    """
    delete the user from the group.
    """
    link = request.json["link"]
    user_info_id = get_jwt_identity()
    current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

    # Check if the group exists
    group_obj = Group.query.filter_by(link=link).first()
    if group_obj is None:
      status_code = 400
      return {"message": "Failed to delete the user."}, status_code

    try:
        group_id = group_obj.id

        # delete data
        UserInfoGroup.query.filter_by(user_info_id=user_info_id).delete()

        # decrease num of users
        group_obj.num_of_users = group_obj.num_of_users - 1
        db.session.add(group_obj)
        db.session.commit()
        status_code = 200
        return {"message": "Successfully delete the user from the group."}, status_code
    except:
        status_code = 400
        db.session.rollback()
        return {"message": "Failed to delete the user."}, status_code

  

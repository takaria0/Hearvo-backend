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
from Hearvo.middlewares.detect_language import get_country_id
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
group_info_schema = GroupSchema()
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
    country_id = get_country_id(request)
    link = request.args["link"] if "link" in request.args.keys() else None
    id = request.args["id"] if "id" in request.args.keys() else None
    order_by = request.args["order_by"] if "order_by" in request.args.keys() else None

    # one group
    if id:
      try:
        data = Group.query.filter_by(id=id).first()
        already_joined = UserInfoGroup.query.filter_by(user_info_id=user_info_id, group_id=data.id, country_id=country_id).first()
        result = group_info_schema.dump(data)
        result["already_joined"] = True if already_joined else False
        return result, 200
      except:
        return {}, 400

    # one group
    if link:
      try:
        data = Group.query.filter_by(link=link, country_id=country_id).first()
        already_joined = UserInfoGroup.query.filter_by(user_info_id=user_info_id, group_id=data.id).first()
        result = group_info_schema.dump(data)
        result["already_joined"] = True if already_joined else False
        return result, 200
      except:
        return {}, 400

    # multiple groups
    try:
        data = UserInfoGroup.query.filter_by(user_info_id=user_info_id).all()
        all_group_id = [x.group_id for x in data]
        fetched_groups = Group.query.filter(Group.id.in_(all_group_id), Group.country_id == country_id).order_by(Group.created_at.desc()).all()
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
    country_id = get_country_id(request)
    current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

    # max group number is 50
    all_groups = UserInfoGroup.query.filter_by(user_info_id=user_info_id).all()
    if len(all_groups) > 49:
      return {"message": "Group max number exceeded."}, 400

    try:
        link = create_link(user_info_id, title, current_datetime)
        new_group = Group(
          user_info_id=user_info_id,
          title=title,
          link=link,
          created_at=current_datetime,
          num_of_users=1,
          country_id=country_id
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
    country_id = get_country_id(request)

    # Check if the group exists
    group_obj = Group.query.filter_by(link=link, country_id=country_id).first()

    if group_obj is None:
      status_code = 400
      return {"message": "Failed to add a user."}, status_code

    # Check if the user has already joined the group
    is_duplicated = UserInfoGroup.query.filter_by(user_info_id=user_info_id, group_id=group_obj.id).first()
    if is_duplicated:
      status_code = 400
      return {"message": "This user already exists."}, status_code

    # max group number is 50
    all_groups = UserInfoGroup.query.filter_by(user_info_id=user_info_id).all()
    if len(all_groups) > 49:
      return {"message": "Group max number exceeded."}, 400

    try:
      group_id = group_obj.id
      user_info_group = UserInfoGroup(user_info_id=user_info_id, group_id=group_id, created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
      group_obj.num_of_users = group_obj.num_of_users + 1
      db.session.add(user_info_group)
      db.session.add(group_obj)
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
    country_id = get_country_id(request)
    current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

    # Check if the group exists
    group_obj = Group.query.filter_by(link=link, country_id=country_id).first()
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

  

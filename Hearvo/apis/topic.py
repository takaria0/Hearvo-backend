import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, Topic, TopicSchema
from .logger_api import logger_api


#########################################
# Schema
#########################################
topic_schema = TopicSchema()
topics_schema = TopicSchema(many=True)

#########################################
# Routes to handle API
#########################################
class TopicResource(Resource):

  def get(self):
    # try:
    #   verify_jwt_in_request_optional()
    #   user_info_id = get_jwt_identity()
    # except :
    #   user_info_id = None

    # filter by lang_id and popularity (num of contents)?
    topics = Topic.query.all()
    status_code = 200
    return topics_schema.dump(topics), status_code


    
  # @jwt_required
  # def post(self):
  #   logger_api("request.json", str(request.json))
  #   user_info_id = get_jwt_identity()
  #   post_id = request.json["post_id"]
  #   parent_id = request.json["parent_id"]

  #   if (parent_id == 0) or (parent_id == "0"):
  #     parent_id = None

  #   content = request.json["content"]

  #   new_comment = Topic(
  #     user_info_id=user_info_id,
  #     post_id=post_id,
  #     parent_id=parent_id,
  #     content=content,
  #     created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
  #   )

  #   logger_api("new_comment", str(new_comment))
  #   try:
  #     db.session.add(new_comment)
  #     db.session.commit()
  #     status_code = 200
  #   except:
  #     db.session.rollback()
  #     status_code = 400
  #   finally:
  #     pass
  #     # db.session.close()

  #   return comment_schema.dump(new_comment)





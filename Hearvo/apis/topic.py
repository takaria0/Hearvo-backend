import os

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, Topic, TopicSchema, UserInfoTopic
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
  @jwt_required
  def get(self):
    # try:
    #   verify_jwt_in_request_optional()
    #   user_info_id = get_jwt_identity()
    # except :
    #   user_info_id = None

    # filter by lang_id and popularity (num of contents)?
    topics = Topic.query.order_by(Topic.num_of_posts.desc()).all()
    result = topics_schema.dump(topics)
    # for each in result:
      # each["post_topic_length"] =len(each["post_topic"])
    status_code = 200
    return result, status_code


    
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




class UserInfoTopicResource(Resource):
  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    logger_api("user_info_id", str(user_info_id))
    topic_id_list = request.json["topic_id_list"]

    
    try:
      topic_obj_list = Topic.query.filter(Topic.id.in_(topic_id_list)).all()

      # update topic num of users
      for topic_obj in topic_obj_list:
        topic_obj.num_of_users = topic_obj.num_of_users + 1
      
      new_topic_user_info = [UserInfoTopic(user_info_id=user_info_id,topic_id=topic_id) for topic_id in topic_id_list]

      # bulk insert
      db.session.bulk_save_objects(topic_obj)
      db.session.bulk_save_objects(new_topic_user_info)
      db.session.commit()
      status_code = 200
      return {"message":"Successfully added topics to the user."}, status_code
    except:
      db.session.rollback()
      status_code = 400
      return {"message":"Failed to add topics to the user."}, status_code

  @jwt_required
  def delete(self):
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    logger_api("user_info_id", str(user_info_id))
    topic_id_list = request.json["topic_id_list"]

    
    try:

      topic_obj_list = Topic.query.filter(Topic.id.in_(topic_id_list)).all()
      logger_api("topic_obj_list", topic_obj_list)
      # update topic num of users
      for topic_obj in topic_obj_list:
        topic_obj.num_of_users = topic_obj.num_of_users - 1
      
      # bulk update and delete
      db.session.bulk_save_objects(topic_obj)
      UserInfoTopic.query.filter(UserInfoTopic.topic_id.in_(topic_id_list), UserInfoTopic.user_info_id==user_info_id).delete()
      db.session.commit()
      status_code = 200
      return {"message":"Successfully deleted relation between topics and the user."}, status_code

    except:
      db.session.rollback()
      status_code = 400
      return {"message":"Failed to delete."}, status_code


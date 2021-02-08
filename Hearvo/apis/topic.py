import os
import json

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, Topic, TopicSchema, UserInfoTopic
from .logger_api import logger_api
from Hearvo.middlewares.detect_language import get_lang_id


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
    """
    /topics:
    get topics by the user_info_id

    /topics?startswith=XXX:
    get topics that starts with XXX order by popularity
    """
    user_info_id = get_jwt_identity()
    lang_id = get_lang_id(request.base_url)

    """
    return initial topics. save topics beforehand
    """
    if "initial_topics" in request.args.keys():
      try:
        initial_topics = json.loads(request.args["initial_topics"])

        for topic in initial_topics:
          check_topic = Topic.query.filter_by(topic=topic).first()
          if check_topic:
            pass
          else:
            db.session.add(Topic(topic=topic, lang_id=lang_id))
        
        db.session.commit()
        topics = Topic.query.filter(Topic.topic.in_(initial_topics)).all()
        result = topics_schema.dump(topics)
        return result, 200

      except:
        db.session.rollback()
        return {}, 400

    """
    I think this query is really slow when the data becomes huge. Need to update in the future. 
    It's just LIKE operator that matches XXX%
    """
    if "startswith" in request.args.keys():
      startswith_word = request.args["startswith"]

      if len(startswith_word) == 0:
        return [], 200

      topics = Topic.query.filter(Topic.topic.startswith(startswith_word)).order_by(Topic.num_of_posts.desc()).all()
      result = topics_schema.dump(topics)
      return result, 200

    # filter by lang_id and popularity (num of contents)?
    topics = Topic.query.order_by(Topic.num_of_posts.desc()).all()
    result = topics_schema.dump(topics)
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
    """
    create assosiation between a user and a topic
    """
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    logger_api("user_info_id", str(user_info_id))
    topic_id_list = request.json["topic_id_list"]

    
    try:
      new_topic_user_info_list = []
      topic_obj_list = Topic.query.filter(Topic.id.in_(topic_id_list)).all()
      # update topic num of users
      for topic_obj in topic_obj_list:
        # check if the user already followed the topic
        check_already = UserInfoTopic.query.filter_by(id=topic_obj).first()
        if check_already is None:
          topic_obj.num_of_users = topic_obj.num_of_users + 1
          new_topic_user_info_list.append(UserInfoTopic(user_info_id=user_info_id,topic_id=topic_id))

      # bulk insert
      db.session.bulk_save_objects(topic_obj_list)
      db.session.bulk_save_objects(new_topic_user_info_list)
      db.session.commit()
      status_code = 200
      return {"message":"Successfully added topics to the user."}, status_code
    except:
      db.session.rollback()
      status_code = 400
      return {"message":"Failed to add topics to the user."}, status_code

  @jwt_required
  def delete(self):
    """
    delete assosiation between a user and a topic
    """
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
      db.session.bulk_save_objects(topic_obj_list)
      UserInfoTopic.query.filter(UserInfoTopic.topic_id.in_(topic_id_list), UserInfoTopic.user_info_id==user_info_id).delete()
      db.session.commit()
      status_code = 200
      return {"message":"Successfully deleted relation between topics and the user."}, status_code

    except:
      db.session.rollback()
      status_code = 400
      return {"message":"Failed to delete."}, status_code


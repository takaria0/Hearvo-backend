import os
import json

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

import Hearvo.config as config
from ..app import logger
from ..models import db, Topic, TopicSchema, UserInfoTopic, PostTopic
from .logger_api import logger_api
from Hearvo.middlewares.detect_language import get_country_id


#########################################
# Schema
#########################################
topic_schema = TopicSchema()
topics_schema = TopicSchema(many=True)

#########################################
# Routes to handle API
#########################################
class TopicResource(Resource):
  # @jwt_required
  def get(self):
    """
    /topics:
    get topics by the user_info_id

    /topics?startswith=XXX:
    get topics that starts with XXX order by popularity
    """
    # user_info_id = get_jwt_identity()
    country_id = get_country_id(request)


    """
    for side bar topic rankings
    do not include group's topic
    """
    if "sidebar" in request.args.keys():
      try:
        """
        get popular topics in the last 24 hours
        """
        yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(hours=24)).isoformat()
        q = db.session.query(Topic.topic, func.count(PostTopic.topic_id)) \
        .join(PostTopic, PostTopic.topic_id == Topic.id, isouter=True) \
        .order_by(func.count(PostTopic.topic_id).desc()) \
        .group_by(Topic.id, PostTopic.topic_id) \
        .filter(PostTopic.created_at > yesterday_datetime, Topic.country_id == country_id) \
        .limit(10) \
        .all() 

        result = topics_schema.dump(q)
        return result, 200
      except:
        return [], 400

    """
    return initial topics. save topics beforehand
    """
    if "initial_topics" in request.args.keys():
      try:
        initial_topics = json.loads(request.args["initial_topics"])

        for topic in initial_topics:
          check_topic = Topic.query.filter_by(topic=topic, country_id=country_id).first()
          if check_topic:
            pass
          else:
            db.session.add(Topic(topic=topic, country_id=country_id))
        
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

      topics = Topic.query.filter(Topic.topic.startswith(startswith_word), Topic.country_id==country_id).order_by(Topic.num_of_posts.desc()).limit(20).all()
      result = topics_schema.dump(topics)
      return result, 200

    # filter by country_id and popularity (num of contents)?
    # topics = Topic.query.order_by(Topic.num_of_posts.desc()).limit(20).all()
    # result = topics_schema.dump(topics)
    # status_code = 200
    return {}, 200


    
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
  def get(self):
    """
    get user's topic
    """
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    country_id = get_country_id(request)
    logger_api("user_info_id", str(user_info_id))


    """
    check the user has already followed the topic
    """
    if "topic_word" in request.args.keys():
      try:
        """
        get popular topics in the last 24 hours
        """
        topic_word = request.args["topic_word"]
        topic_obj = Topic.query.filter_by(topic=topic_word, country_id=country_id).first()
        has_followed = UserInfoTopic.query.filter_by(user_info_id=user_info_id).join(Topic,Topic.id == UserInfoTopic.topic_id).filter_by(topic=topic_word).first()

        
        if has_followed:
          result = {"following": True, "topic_id": topic_obj.id, "num_of_posts": topic_obj.num_of_posts, "num_of_users": topic_obj.num_of_users}
        else:
          result = {"following": False, "topic_id": topic_obj.id, "num_of_posts": topic_obj.num_of_posts, "num_of_users": topic_obj.num_of_users}
        return result, 200

      except:
        return {"following": False, "topic_id": None}, 400

    try:
      topic_list = Topic.query.join(UserInfoTopic, Topic.id == UserInfoTopic.topic_id).filter(UserInfoTopic.user_info_id == user_info_id, Topic.country_id==country_id).limit(100).all()
      result = topics_schema.dump(topic_list)
      status_code = 200
      return result, status_code
    except:
      db.session.rollback()
      status_code = 400
      return {}, status_code




  @jwt_required
  def post(self):
    """
    create assosiation between a user and a topic
    """
    logger_api("request.json", str(request.json))
    user_info_id = get_jwt_identity()
    country_id = get_country_id(request)
    logger_api("user_info_id", str(user_info_id))
    topic_id_list = request.json["topic_id_list"]

    
    try:
      new_topic_user_info_list = []
      topic_obj_list = Topic.query.filter(Topic.id.in_(topic_id_list), Topic.country_id==country_id).all()
      # update topic num of users
      for topic_obj in topic_obj_list:
        # check if the user already followed the topic
        check_already = UserInfoTopic.query.filter_by(user_info_id=user_info_id, topic_id=topic_obj.id).first()
        if check_already is None:
          topic_obj.num_of_users = topic_obj.num_of_users + 1
          new_topic_user_info_list.append(UserInfoTopic(user_info_id=user_info_id,topic_id=topic_obj.id,created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()))

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
    country_id = get_country_id(request)
    logger_api("user_info_id", str(user_info_id))
    topic_id_list = request.json["topic_id_list"]

    
    try:

      topic_obj_list = Topic.query.filter(Topic.id.in_(topic_id_list), Topic.country_id==country_id).all()
      logger_api("topic_obj_list", topic_obj_list)
      # update topic num of users
      for topic_obj in topic_obj_list:
        topic_obj.num_of_users = topic_obj.num_of_users - 1
      
      # bulk update and delete
      db.session.bulk_save_objects(topic_obj_list)
      delete_obj = UserInfoTopic.query.filter(UserInfoTopic.topic_id.in_(topic_id_list), UserInfoTopic.user_info_id==user_info_id).delete(synchronize_session=False)
      db.session.commit()
      status_code = 200
      return {"message":"Successfully deleted relation between topics and the user."}, status_code

    except:
      db.session.rollback()
      status_code = 400
      return {"message":"Failed to delete."}, status_code


import os
from datetime import datetime, timedelta, timezone

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
import bcrypt

import Hearvo.config as config
from ..utils import concat_realname
from ..app import logger
from ..models import db, User, UserGETSchema, UserInfo, UserInfoGETSchema, UserInfoPostVoted, UserInfoTopic, UserInfoFollowing, UserInfoFollowingSchema
from Hearvo.middlewares.detect_language import get_country_id
from .logger_api import logger_api

DELETED_USER_NAME = "<削除済み>" 
DELETED_USER_NAME_MAP = {
  1: "<削除済み>",
  2: "<Deleted>"
}

#########################################
# Schema
#########################################
user_info_schema = UserInfoGETSchema()
users_info_schema = UserInfoGETSchema(many=True)

user_info_followings_schema = UserInfoFollowingSchema(many=True)

#########################################
# Routes to handle API
#########################################
class UserResource(Resource):
  @jwt_optional
  def get(self):
    user_info_id = get_jwt_identity()

    """
    get user list who voted a poll
    """
    if "post_detail_id" in request.args.keys():
      post_detail_id = request.args["post_detail_id"]
      user_info_list = UserInfo.query.join(UserInfoPostVoted).filter_by(post_detail_id=post_detail_id).limit(30).all()

      result = []
      for user_info in user_info_list:
        """
        check hide real name setting
        """
        if user_info.hide_realname == False:
          profile_name = concat_realname(user_info.first_name, user_info.middle_name, user_info.last_name)
          name = user_info.name
          has_followed = True if UserInfoFollowing.query.filter_by(user_info_id=user_info_id, following_user_info_id=user_info.id).first() else False
          is_real_name = True
        else:
          profile_name = user_info.profile_name
          name = user_info.name
          has_followed = True if UserInfoFollowing.query.filter_by(user_info_id=user_info_id, following_user_info_id=user_info.id).first() else False
          is_real_name = False

        result.append({"user_info_id": user_info.id, "profile_name": profile_name, "name": name, "is_real_name": is_real_name, "description": user_info.description if user_info.description else "", "has_followed": has_followed })

      return result, 200
  
    """
    get specific user's profile infomation
    """
    if "name" in request.args.keys():
      name = request.args["name"]
      country_id = get_country_id(request)
      user_info = UserInfo.query.filter_by(name=name, country_id=country_id).first()
      
      if user_info == None:
        return {}, 400


      """
      if the user is me, always show the real name
      """
      num_of_following_topics = UserInfoTopic.query.filter_by(user_info_id=user_info.id).count()
      num_of_votes = UserInfoPostVoted.query.filter_by(user_info_id=user_info.id).count()
      num_of_following_users = UserInfoFollowing.query.filter_by(user_info_id=user_info.id).count()
      num_of_followers = UserInfoFollowing.query.filter_by(following_user_info_id=user_info.id).count()

      if str(user_info_id) == str(user_info.id):
        result = { "user_info_id": user_info.id, "name": user_info.name, "profile_name": user_info.profile_name, "first_name": user_info.first_name, "middle_name": user_info.middle_name, "last_name": user_info.last_name, "created_at": user_info.created_at.isoformat(), "description": user_info.description, "profile_img_url": user_info.profile_img_url }
        
        result = { **result, "num_of_following_topics": num_of_following_topics, "num_of_votes": num_of_votes, "num_of_following_users": num_of_following_users, "num_of_followers": num_of_followers, "myprofile": True }
      else:
        """
        if the user is not me, 
        check hide real name setting and hide it if so.
        """
        has_followed = True if UserInfoFollowing.query.filter_by(user_info_id=user_info_id, following_user_info_id=user_info.id).first() else False

        if user_info.hide_realname == False:
          result = { "user_info_id": user_info.id, "name": user_info.name, "profile_name": user_info.profile_name, "first_name": user_info.first_name, "middle_name": user_info.middle_name, "last_name": user_info.last_name, "created_at": user_info.created_at.isoformat(), "description": user_info.description, "profile_img_url": user_info.profile_img_url, "has_followed": has_followed }
        else:
          result = { "user_info_id": user_info.id, "name": user_info.name, "profile_name": user_info.profile_name, "first_name": None, "middle_name": None, "last_name": None, "created_at": user_info.created_at.isoformat(), "description": user_info.description, "profile_img_url": user_info.profile_img_url, "has_followed": has_followed }

        result = { **result, "num_of_following_topics": num_of_following_topics, "num_of_votes": num_of_votes,
        "num_of_following_users": num_of_following_users, "num_of_followers": num_of_followers, "myprofile": False }


      return result, 200
    

    if "profile_detail" in request.args.keys():
      num_of_following_topics = UserInfoTopic.query.filter_by(user_info_id=user_info_id).count()
      num_of_votes = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id).count()
      user = UserInfo.query.filter_by(id=user_info_id).first()
      user = user_info_schema.dump(user)
      return { **user, "num_of_following_topics":num_of_following_topics, "num_of_votes": num_of_votes }, 200

    if user_info_id is None:
      return {}, 400

    user = UserInfo.query.filter_by(id=user_info_id).first()
    return user_info_schema.dump(user), 200

  @jwt_required
  def put(self):
    user_info_id = get_jwt_identity()

    user_info_obj = UserInfo.query.get(user_info_id)

    if "login_count" in request.args.keys():
      login_count = request.args["login_count"]
      try:
        user_info_obj.login_count = int(login_count)
        db.session.add(user_info_obj)
        db.session.commit()
        return {}, 200
      except:
        db.session.rollback()
        return {}, 400

    elif "initial_setting" in request.args.keys():
      gender = request.json["gender"]
      birth_year = request.json["birth_year"]
      gender_detail = request.json["gender_detail"]
      first_name = request.json["first_name"]
      middle_name = request.json["middle_name"]
      last_name = request.json["last_name"]


      """ can't update anymore because: """
      if (user_info_obj.gender != None) or (user_info_obj.birth_year != None):
        return {}, 409
      
      if (len(first_name) < 1) or (len(first_name) > 100):
        return {}, 400

      if (len(last_name) < 1) or (len(last_name) > 100):
        return {}, 400

      # UPDATE USER 
      user_info_obj.gender = gender
      user_info_obj.birth_year = birth_year
      user_info_obj.gender_detail = gender_detail
      user_info_obj.first_name = first_name
      user_info_obj.middle_name = middle_name
      user_info_obj.last_name = last_name

      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
        
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code

    elif "edit_profile_img" in request.args.keys():
      profile_img_url = request.json["profile_img_url"]
      user_info_obj.profile_img_url = profile_img_url

      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
        
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code
      return {}, 200

    elif "edit_profile" in request.args.keys():
      profile_name = request.json["profile_name"]
      description = request.json["description"]

      # UPDATE USER
      user_info_obj.profile_name = profile_name
      user_info_obj.description = description

      """
      check name duplication
      """
      country_id = get_country_id(request)
      check_dup = UserInfo.query.filter(UserInfo.profile_name==profile_name, UserInfo.id != user_info_id, UserInfo.country_id==country_id).first()
      if check_dup:
        return {}, 400

      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
        
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code
      return {}, 200

    elif "edit_settings" in request.args.keys():
      hide_realname = request.json["hideName"]

      # UPDATE USER_INFO
      user_info_obj.hide_realname = hide_realname

      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
        
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code

      return

    else:
      gender = request.json["gender"]
      birth_year = request.json["birth_year"]

      user_info_obj.gender = gender
      user_info_obj.birth_year = birth_year
      
      try:
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return user_info_schema.dump(user_info_obj), status_code
      except:
        db.session.rollback()
        status_code = 400
        return {}, status_code


  @jwt_required
  def delete(self):
    user_info_id = get_jwt_identity()
    country_id = get_country_id(request)
    confirm_password = request.headers['confirmPassword']
    logger_api('confirm_password',confirm_password)

    try:
      user_info = UserInfo.query.filter_by(id=user_info_id).first()
      logger_api('user_info',user_info)
      logger_api('user_info.user_id',user_info.user_id)
      user = User.query.filter_by(id=user_info.user_id).first()
      hashed_password = user.hashed_password
      logger_api('user.hashed_password',user.hashed_password)
      if (bcrypt.checkpw(confirm_password.encode("utf-8"), hashed_password.encode("utf-8"))):
        
        # UPDATE EMAIL TO NULL, NAME TO <deleted>
        user.deleted_email = user.email
        user.email = None
        user_info.name = DELETED_USER_NAME_MAP[country_id] if country_id in DELETED_USER_NAME_MAP.keys() else "<Deleted>"

        db.session.add(user)
        db.session.add(user_info)
        db.session.commit()
        
        return {"message": "Successfully deleted the account"}, 200

      else:
        logger_api('password doesnt mathced', [])
        return {"message": "Account deletion failed"}, 400

    except:
      import traceback
      traceback.print_exc()
      db.session.rollback()
      
      return {"message": "Account deletion failed"}, 400
    




class UserPasswordResource(Resource):

  @jwt_required
  def put(self):
    user_info_id = get_jwt_identity()
    user_info_obj = UserInfo.query.get(user_info_id)

    old_password = request.json["old_password"]
    new_password = request.json["new_password"]

    # validate old password
    old_hashed_password = user_info_obj.hashed_password

    # password matching
    try:
      if (bcrypt.checkpw(old_password.encode("utf-8"), old_hashed_password.encode("utf-8"))):
        # matched
        # create new hashed password from new_password
        salt = bcrypt.gensalt(rounds=15, prefix=b'2a') # generate salt, 2^15 = 32768
        new_hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode("utf-8") # hashed password

        user_info_obj.hashed_password = new_hashed_password        
        db.session.add(user_info_obj)
        db.session.commit()
        status_code = 200
        return {"message": "Password has changed"}, status_code
      else:
        status_code = 400
        return {}, status_code

    except:
      db.session.rollback()
      status_code = 400
      return {}, status_code



class UserInfoFollowingResource(Resource):

  @jwt_required
  def get(self):
    user_info_id = request.args["id"]

    try:
      followings = UserInfoFollowing.query.filter_by(user_info_id=user_info_id).limit(100).all()
      followers = UserInfoFollowing.query.filter_by(following_user_info_id=user_info_id).limit(100).all()
      return {"followings": user_info_followings_schema.dump(followings), "followers": user_info_followings_schema.dump(followers)}
    except:
      return {}, 400

  @jwt_required
  def post(self):
    my_user_info_id = get_jwt_identity()
    target_user_info_id = request.json["user_info_id"]

    if int(target_user_info_id) == int(my_user_info_id):
      return {"message": "Failed to follow."}, 400

    already_followed = UserInfoFollowing.query.filter_by(user_info_id=my_user_info_id, following_user_info_id=target_user_info_id).first()

    if already_followed:
      return {"message": "Failed to follow."}, 400

    try:
      create_obj = UserInfoFollowing(
        user_info_id=my_user_info_id,
        following_user_info_id=target_user_info_id,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
        updated_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
        )
      db.session.add(create_obj)
      db.session.commit()

      return {"message": "Followed."}, 200
    except:
      db.session.rollback()
      return {"message": "Failed to follow."}, 400


  @jwt_required
  def delete(self):
    my_user_info_id = get_jwt_identity()
    my_user_info_obj = UserInfo.query.get(my_user_info_id)
    target_user_info_id = request.json["user_info_id"]

    try:
      UserInfoFollowing.query \
      .filter_by(user_info_id=my_user_info_id, following_user_info_id=target_user_info_id) \
      .delete()
      db.session.commit()

      return {"message": "Unfollow."}, 200
    except:
      db.session.rollback()
      return {"message": "Failed to unfollow."}, 400

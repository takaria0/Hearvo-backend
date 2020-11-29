import os
from collections import Counter
from datetime import datetime, timedelta, timezone
import json

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from sqlalchemy import or_

import Hearvo.config as config
from ..app import logger, cache
from ..models import db, Post, PostSchema, VoteSelect, VoteSelectUser, UserInfoPostVoted, UserInfo, VoteMj, MjOption, VoteMjUser

from .logger_api import logger_api
from Hearvo.middlewares.detect_language import get_lang_id

#########################################
# Schema
#########################################
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

#########################################
# Routes to handle API
#########################################
class PostResource(Resource):

  def _string_check(self, content):
    if (len(content.replace(" ", "")) == 0):
      return False
    else:
      return True

  def _options_validate(self, options):

    if "gender" in options.keys():
      gender = options["gender"] if self._string_check(options["gender"]) else None
    else:
      gender = None

    if "min_age" in options.keys():
      min_age = int(options["min_age"]) if self._string_check(options["min_age"]) else 0
    else:
      min_age = 0

    if "max_age" in options.keys():
      max_age = int(options["max_age"]) if self._string_check(options["max_age"]) else 130
    else:
      max_age = 130

    if "occupation" in options.keys():
      occupation = options["occupation"] if self._string_check(options["occupation"]) else None
    else:
      occupation = None

    
    return {"gender": gender, "min_age": min_age, "max_age": max_age, "occupation": occupation}

  def _filter_vote_selects_options(self, options, user_info_id, vote_select_ids):
    gender = options["gender"]
    min_age = options["min_age"]
    max_age = options["max_age"]
    occupation = options["occupation"]

    if gender == None:
      vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).join(UserInfo, UserInfo.id==VoteSelectUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.age >= min_age, UserInfo.age <= max_age, ).all()

    elif occupation == None:
      vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).join(UserInfo, UserInfo.id==VoteSelectUser.user_info_id).filter(UserInfo.gender==gender, UserInfo.age >= min_age, UserInfo.age <= max_age, ).all()

    else:
      vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).join(UserInfo, UserInfo.id==VoteSelectUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.gender==gender, UserInfo.age >= min_age, UserInfo.age <= max_age, ).all()

    return vote_select_user_obj

  def _filter_vote_mjs_options(self, options, user_info_id, post_id):
    gender = options["gender"]
    min_age = options["min_age"]
    max_age = options["max_age"]
    occupation = options["occupation"]

    if gender == None:
      vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(UserInfo, UserInfo.id==VoteMjUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.age >= min_age, UserInfo.age <= max_age, ).all()

    elif occupation == None:
      vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(UserInfo, UserInfo.id==VoteMjUser.user_info_id).filter(UserInfo.gender==gender, UserInfo.age >= min_age, UserInfo.age <= max_age, ).all()

    else:
      vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(UserInfo, UserInfo.id==VoteMjUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.gender==gender, UserInfo.age >= min_age, UserInfo.age <= max_age, ).all()

    return vote_mj_user_obj

  def _count_vote(self, posts, user_info_id):

    if type(posts) == dict:
      posts = [posts]

    for idx, post in enumerate(posts):
      post_id = post["id"]
      vote_type_id = post["vote_type"]["id"]

      if vote_type_id == 1:
        post_obj = Post.query.filter_by(id=post_id).first()
        vote_selects_obj = post_obj.vote_selects

        vote_select_ids = [obj.id for obj in vote_selects_obj]
        vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).all()
        count_obj = {obj.user_info_id: obj.vote_select_id for obj in vote_select_user_obj}
        id_content_table = {obj.id: obj.content for obj in vote_selects_obj}

        vote_selects_count = Counter(count_obj.values())
        total_vote = sum(vote_selects_count.values())
        data = dict(Counter(count_obj.values()))
        vote_selects_count = [{"vote_select_id": id, "count": data[id], "content": id_content_table[id]} if id in data.keys() else {"vote_select_id": id, "count": 0, "content": id_content_table[id]} for id in vote_select_ids ]

        already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

        current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
        end_datetime = datetime.fromisoformat(post["end_at"])
        end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

        vote_period_end = True if current_datetime > end_datetime else False
        
        posts[idx]["vote_select_ids"] = vote_select_ids
        posts[idx]["vote_selects_count"] = vote_selects_count
        posts[idx]["already_voted"] = already_voted
        posts[idx]["total_vote"] = total_vote
        posts[idx]["vote_period_end"] = vote_period_end
      
      elif vote_type_id == 2:
        raw_mj_options = MjOption.query.filter_by(post_id=post_id).all()
        mj_options = {obj.id: obj.content for obj in raw_mj_options}
        # ADD USER FILTERING LATER
        vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(VoteMj, VoteMj.id==VoteMjUser.vote_mj_id).all() 
        vote_mj_ids = list({obj.vote_mj_id for obj in vote_mj_user_obj})

        vote_mj_obj = [{"vote_mj_id": obj.id, "content": obj.content} for obj in VoteMj.query.filter(VoteMj.id.in_(vote_mj_ids)).all()]
        count_obj = [  {"vote_mj_id": mj_id, "mj_option_ids":[ obj.mj_option_id for obj in vote_mj_user_obj if mj_id==obj.vote_mj_id]} for mj_id in vote_mj_ids ]
        total_vote = len(count_obj[0]["mj_option_ids"]) if len(count_obj) != 0 else 0
        vote_mj_count = [{"count": [{"mj_option_id":key, "content":mj_options[key], "count": val} for key, val in dict(Counter(obj["mj_option_ids"])).items()], "vote_mj_id": obj["vote_mj_id"]}  for obj in count_obj]

        already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

        current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
        end_datetime = datetime.fromisoformat(post["end_at"])
        end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

        vote_period_end = True if current_datetime > end_datetime else False
        
        posts[idx]["vote_mj_ids"] = vote_mj_ids
        posts[idx]["vote_mj_count"] = vote_mj_count
        posts[idx]["vote_mj_obj"] = vote_mj_obj
        posts[idx]["already_voted"] = already_voted
        posts[idx]["total_vote"] = total_vote
        posts[idx]["vote_period_end"] = vote_period_end

    return posts


  def _count_vote_option(self, posts, user_info_id, options):
    if type(posts) == dict:
      posts = [posts]

    options = self._options_validate(options)
    for idx, post in enumerate(posts):
      post_id = post["id"]
      vote_type_id = post["vote_type"]["id"]

      if vote_type_id == 1:
        
        post_obj = Post.query.filter_by(id=post_id).first()
        vote_selects_obj = post_obj.vote_selects

        vote_select_ids = [obj.id for obj in vote_selects_obj]
        vote_select_user_obj = self._filter_vote_selects_options(options, user_info_id, vote_select_ids)
        
        count_obj = {obj.user_info_id: obj.vote_select_id for obj in vote_select_user_obj}
        id_content_table = {obj.id: obj.content for obj in vote_selects_obj}

        vote_selects_count = Counter(count_obj.values())
        total_vote = sum(vote_selects_count.values())
        data = dict(Counter(count_obj.values()))
        vote_selects_count = [{"vote_select_id": id, "count": data[id], "content": id_content_table[id]} if id in data.keys() else {"vote_select_id": id, "count": 0, "content": id_content_table[id]} for id in vote_select_ids ]

        already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

        current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
        end_datetime = datetime.fromisoformat(post["end_at"])
        end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

        vote_period_end = True if current_datetime > end_datetime else False
        
        posts[idx]["vote_select_ids"] = vote_select_ids
        posts[idx]["vote_selects_count"] = vote_selects_count
        posts[idx]["already_voted"] = already_voted
        posts[idx]["total_vote"] = total_vote
        posts[idx]["vote_period_end"] = vote_period_end

      elif vote_type_id == 2:
        raw_mj_options = MjOption.query.filter_by(post_id=post_id).all()
        mj_options = {obj.id: obj.content for obj in raw_mj_options}

        vote_mj_user_obj = self._filter_vote_mjs_options(options, user_info_id, post_id)
        vote_mj_ids = list({obj.vote_mj_id for obj in vote_mj_user_obj})

        vote_mj_obj = [{"vote_mj_id": obj.id, "content": obj.content} for obj in VoteMj.query.filter(VoteMj.id.in_(vote_mj_ids)).all()]
        count_obj = [  {"vote_mj_id": mj_id, "mj_option_ids":[ obj.mj_option_id for obj in vote_mj_user_obj if mj_id==obj.vote_mj_id]} for mj_id in vote_mj_ids ]
        total_vote = len(count_obj[0]["mj_option_ids"]) if len(count_obj) != 0 else 0
        vote_mj_count = [{"count": [{"mj_option_id":key, "content":mj_options[key], "count": val} for key, val in dict(Counter(obj["mj_option_ids"])).items()], "vote_mj_id": obj["vote_mj_id"]}  for obj in count_obj]

        already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

        current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
        end_datetime = datetime.fromisoformat(post["end_at"])
        end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

        vote_period_end = True if current_datetime > end_datetime else False
        
        posts[idx]["vote_mj_ids"] = vote_mj_ids
        posts[idx]["vote_mj_count"] = vote_mj_count
        posts[idx]["vote_mj_obj"] = vote_mj_obj
        posts[idx]["already_voted"] = already_voted
        posts[idx]["total_vote"] = total_vote
        posts[idx]["vote_period_end"] = vote_period_end

    return posts



  def get(self):
    logger_api("request.base_url", request.base_url)
    
    if "page" in request.args.keys():
      page = int(request.args["page"])
      if page > 20:
        return {}, 200

    lang_id = get_lang_id(request.base_url)
    try:
      verify_jwt_in_request_optional()
      user_info_id = get_jwt_identity()
    except :
      user_info_id = None

    logger_api("user_info_id", user_info_id)
    if "id" in request.args.keys():
      do_filter = request.args["do_filter"] if "do_filter" in request.args.keys() else "no"

      if do_filter == "yes":
        logger_api("do_filter", request.args)
        options = request.args
        id = request.args["id"]
        post = Post.query.filter_by(id=id).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).first()
        status_code = 200
        post_obj = post_schema.dump(post)
        count_vote_obj = self._count_vote_option(post_obj, user_info_id, options)[0]
        return count_vote_obj, status_code
      else:
        id = request.args["id"]
        post = Post.query.filter_by(id=id).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).first()
        status_code = 200
        post_obj = post_schema.dump(post)
        count_vote_obj = self._count_vote(post_obj, user_info_id)[0]
        return count_vote_obj, status_code


    elif "keyword" in request.args.keys() and "page" in request.args.keys():
      keyword = request.args["keyword"]
      page = int(request.args["page"])
      logger_api("request.args['keyword']", request.args["keyword"])
      
      if keyword == "popular":
        time = request.args["time"] if ("time" in request.args.keys()) and (request.args["time"] != "") else None
        count_vote_obj = cache.get('popular_posts_page_{}_time_{}'.format(page, time))
        status_code = 200
        logger_api("popular cache hit or not", (count_vote_obj is not None))
        if count_vote_obj is None:
          if time == "today":
            yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(hours=24)).isoformat()
          elif time == "now":
            yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(hours=1)).isoformat()
          elif time == "week":
            yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=7)).isoformat()
          elif time == "month":
            yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=30)).isoformat()
          else:
            yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(hours=24)).isoformat()

          
          posts = Post.query.filter(Post.lang_id == lang_id, Post.created_at > yesterday_datetime).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.num_vote.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
          
          post_obj = posts_schema.dump(posts)
          count_vote_obj = self._count_vote(post_obj, user_info_id)
          cache.set('popular_posts_page_{}_time_{}'.format(page, time), count_vote_obj)
        return count_vote_obj, status_code

      elif keyword == "latest":
        count_vote_obj = cache.get('latest_posts_page_{}'.format(page))
        status_code = 200
        logger_api("latest cache hit or not", (count_vote_obj is not None))
        if count_vote_obj is None:
          posts = Post.query.filter_by(lang_id=lang_id).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
          
          post_obj = posts_schema.dump(posts)
          count_vote_obj = self._count_vote(post_obj, user_info_id)
          cache.set('latest_posts_page_{}'.format(page), count_vote_obj)

        return count_vote_obj, status_code

      elif keyword == "myposts":
        posts = Post.query.distinct().filter_by(lang_id=lang_id, user_info_id=user_info_id).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items
        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = self._count_vote(post_obj, user_info_id)
        return count_vote_obj, status_code

      elif keyword == "voted":
        voted_post_list = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id).all()
        voted_post_id_list = [obj.post_id for obj in voted_post_list]

        posts = Post.query.distinct().filter(Post.lang_id==lang_id, Post.id.in_(voted_post_id_list)).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items
        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = self._count_vote(post_obj, user_info_id)
        return count_vote_obj, status_code

      
      else:
        return {}, 200

    elif "search" in request.args.keys() and "page" in request.args.keys():
      search = request.args["search"]

      if "type" in request.args.keys():
        if request.args["type"] == "hash_tag":
          search = "#" + search

      page = int(request.args["page"])
      posts = Post.query.filter(Post.lang_id==lang_id, or_(Post.content.contains(search), Post.title.contains(search))).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
      status_code = 200
      post_obj = posts_schema.dump(posts)
      count_vote_obj = self._count_vote(post_obj, user_info_id)
      return count_vote_obj, status_code

    else:
      posts = Post.query.filter_by(lang_id=lang_id).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
      status_code = 200
      post_obj = posts_schema.dump(posts)
      count_vote_obj = self._count_vote(post_obj, user_info_id)
      return count_vote_obj, status_code



  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    data = request.get_json(force=True)
    logger_api("data", str(data))
    lang_id = get_lang_id(request.base_url)
    user_info_id = get_jwt_identity()

    title = data['title']
    content = data['content']
    end_at = data['end_at']
    vote_obj = data["vote_obj"]
    vote_type_id = data["vote_type_id"]
    

    if vote_type_id == "1":
      vote_obj_list = [VoteSelect(content=obj["content"]) for obj in vote_obj]
      logger_api("vote_obj_list", vote_obj_list)
      new_post = Post(
        user_info_id=user_info_id,
        title=title,
        lang_id=lang_id,
        content=content,
        end_at=end_at,
        vote_selects=vote_obj_list,
        vote_type_id=1,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      )

      # try:
      db.session.add(new_post)
      db.session.commit()
      cache.delete_many(*['latest_posts_page_{}'.format(page) for page in range(1,21)])
      status_code = 200
      return post_schema.dump(new_post), status_code
      # except:
      #   db.session.rollback()
      #   status_code = 400
      #   return {}, status_code
      # finally:
      #   pass
        # db.session.close()

    elif vote_type_id == "2":
      # try:
      vote_obj_list = [VoteMj(content=obj["content"]) for obj in vote_obj]
      logger_api("vote_obj_list", vote_obj_list)
      new_post = Post(
        user_info_id=user_info_id,
        title=title,
        lang_id=lang_id,
        content=content,
        end_at=end_at,
        vote_mjs=vote_obj_list,
        vote_type_id=2,
      )
      
      db.session.add(new_post)
      db.session.flush()

      post_id = new_post.id
      mj_option_list = ["良い", "やや良い", "普通", "やや悪い", "悪い"]
      new_mj_option = [MjOption(post_id=post_id, lang_id=lang_id, content=cont) for cont in mj_option_list]
      logger_api("new_mj_option", new_mj_option)
      db.session.bulk_save_objects(new_mj_option)
      db.session.commit()

      cache.delete_many(*['latest_posts_page_{}'.format(page) for page in range(1,21)])

      status_code = 200
      return post_schema.dump(new_post), status_code
      # except:
        # db.session.rollback()
        # status_code = 400
        # return {}, status_code
      # finally:
        # pass
        # db.session.close()

        
    else:
      return {}, 400

    





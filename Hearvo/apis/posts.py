import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import Hearvo.config as config
from ..app import logger
from ..models import db, Post, PostSchema, VoteSelect, VoteSelectUser, UserInfoPostVoted
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


  def _count_vote(self, posts, user_info_id):

    if type(posts) == dict:
      posts = [posts]

    for idx, post in enumerate(posts):
      post_id = post["id"]
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

    return posts

  @jwt_required
  def get(self):
    logger_api("request.base_url", request.base_url)
    lang_id = get_lang_id(request.base_url)
    user_info_id = get_jwt_identity()

    if "id" in request.args.keys():
      id = request.args["id"]
      post = Post.query.filter_by(id=id).join(Post.vote_selects).first()
      status_code = 200
      post_obj = post_schema.dump(post)
      count_vote_obj = self._count_vote(post_obj, user_info_id)[0]
      return count_vote_obj, status_code

    elif "keyword" in request.args.keys() and "page" in request.args.keys():
      keyword = request.args["keyword"]
      page = int(request.args["page"])
      logger_api("request.args['keyword']", request.args["keyword"])

      if keyword == "popular":
        """
        GET TODAY'S POPULAR POSTS BASED ON NUM_VOTES
        """
        yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=1)).isoformat()
        posts = Post.query.distinct().filter(Post.lang_id == lang_id, Post.created_at > yesterday_datetime).join(Post.vote_selects).order_by(Post.num_vote.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items
        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = self._count_vote(post_obj, user_info_id)
        return count_vote_obj, status_code

      elif keyword == "latest":
        posts = Post.query.distinct().filter_by(lang_id=lang_id).join(Post.vote_selects).order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items
        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = self._count_vote(post_obj, user_info_id)
        return count_vote_obj, status_code

      else:
        return {}, 200

    else:
      posts = Post.query.distinct().filter_by(lang_id=lang_id).join(Post.vote_selects).order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items
      status_code = 200
      post_obj = posts_schema.dump(posts)
      count_vote_obj = self._count_vote(post_obj, user_info_id)
      return count_vote_obj, status_code



  @jwt_required
  def post(self):
    logger_api("request.json", str(request.json))
    lang_id = get_lang_id(request.base_url)
    user_info_id = get_jwt_identity()

    title = request.json['title']
    content = request.json['content']
    end_at = request.json['end_at']
    vote_selects = request.json["vote_selects"]
    vote_selects_list = [VoteSelect(content=obj["content"]) for obj in vote_selects]

    new_post = Post(
      user_info_id=user_info_id,
      title=title,
      lang_id=lang_id,
      content=content,
      end_at=end_at,
      vote_selects=vote_selects_list,
      vote_type_id=1,
    )
    try:
      db.session.add(new_post)
      db.session.commit()
      status_code = 200
      return post_schema.dump(new_post), status_code
    except:
      db.session.rollback()
      status_code = 400
      return {}, status_code
    finally:
      pass
      # db.session.close()

    





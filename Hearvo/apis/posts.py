import os
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import traceback
      

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from sqlalchemy import or_, and_
from sqlalchemy.orm import lazyload, selectinload, with_loader_criteria

import Hearvo.config as config
from ..app import logger, cache, limiter
from ..models import db, Post, PostDetail, PostSchema, VoteSelect, VoteSelectUser, UserInfoPostVoted, UserInfo, VoteMj, MjOption, VoteMjUser, Topic, PostTopic, PostGroup, Group, UserInfoPostVotedSchema, UserInfoGroup, UserInfoTopic, TopicSchema, VoteSelectSchema, PostDetailSchema, UserInfoFollowing

from .logger_api import logger_api
from Hearvo.middlewares.detect_language import get_country_id
from Hearvo.utils import cache_delete_latest_posts, cache_delete_all_posts

user_info_post_voted_schema = UserInfoPostVotedSchema(many=True)


#########################################
# Schema
#########################################
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

vote_select_schema = VoteSelectSchema(many=True)

#########################################
# Routes to handle API
#########################################
class PostResource(Resource):


  @limiter.limit(config.DEFAULT_LIMIT)
  def get(self):
    """
    get posts based on the query parameters below

    page: page of the feed
    id: post id
    keyword: query keyword e.g. "popular" "latest" "myposts" "voted" "recommend"
    time: get post by the time, "now" "today" "week" "month"
    group_id: id of the group posts belong to 

    DEPRECATED
    do_filter: do filtering or not. yes or no
    """
    logger_api("request.base_url", request.base_url)

    """ 
    maximum page length is currently 20, beyond that, no longer return the data 
    """
    if "page" in request.args.keys():
      page = int(request.args["page"])
      if page > 20:
        return {}, 200

    country_id = get_country_id(request)

    """ 
    basically users can see the timeline without login 
    """
    try:
      verify_jwt_in_request_optional()
      user_info_id = get_jwt_identity()
    except:
      user_info_id = None

    """
    get vote_type 3 children posts based on parent_id
    """
    if "parent_id" in request.args.keys():
      # try:
      parent_id = request.args["parent_id"]
      
      try:
        target_post_detail_id = int(request.args["post_detail_id"]) if "post_detail_id" in request.args.keys() else None
      except:
        target_post_detail_id = None

      if target_post_detail_id:
        """
        use target post detail id
        """        
        posts = Post.query.filter_by(parent_id=parent_id).all()
        post_detail_obj = PostDetail.query.get(target_post_detail_id)
        """
        insert children's target post_detail obj
        """
        for post in posts:
          child_post_detail = PostDetail.query.filter_by(end_at=post_detail_obj.end_at, post_id=post.id).first()
          post.target_post_detail_id = child_post_detail.id
          post.target_post_detail = child_post_detail

      else:
        """
        use current post detail id
        """
        posts = Post.query.filter_by(parent_id=parent_id).all()
        parent_post = Post.query.get(parent_id)
        parent_post_detail = PostDetail.query.filter_by(id=parent_post.current_post_detail_id).first()
        """
        insert children's target post_detail obj
        """
        for post in posts:
          child_post_detail = PostDetail.query.filter_by(end_at=parent_post_detail.end_at, post_id=post.id).first()
          post.target_post_detail_id = child_post_detail.id
          post.target_post_detail = child_post_detail

      post_obj_list = posts_schema.dump(posts)
      count_vote_obj = count_vote_ver2(post_obj_list, user_info_id, is_parent=True, target_post_detail_id=1000000000)
      return count_vote_obj, 200
      # except:
      #   return {}, 400

    """ 
    group id is None if the user has not joined the group, or, if the user has not created the account yet. 
    namely users can't see group's contents without joining Hearvo and the group.  
    """
    group_id = request.args["group_id"] if "group_id" in request.args.keys() else None
    if user_info_id is None:
      group_id = None

    if user_info_id and group_id:
      has_joined = UserInfoGroup.query.filter_by(user_info_id=user_info_id, group_id=group_id).first()
      if has_joined is None:
        group_id = None

    logger_api("user_info_id", user_info_id)


    """
    get single post based on the post_id and post_detail_id
    if post_detail_id is present, add 'target_post_detail' data
    """
    if "id" in request.args.keys():
      try:
        id = int(request.args["id"])
        target_post_detail_id = int(request.args["post_detail_id"]) if "post_detail_id" in request.args.keys() else None
      except:
        return {}, 400
      """
      check if the post_detail exists or not
      """
      if target_post_detail_id:
        check_post_detail = PostDetail.query.filter(Post.id==id, PostDetail.id==target_post_detail_id).first()
      else:
        check_post_detail = None

      """
      if exists, add target_post_detail data
      """
      if check_post_detail:
        post = Post.query.filter_by(id=id, parent_id=None) \
          .options(
            lazyload(Post.target_post_detail),
            with_loader_criteria(PostDetail, PostDetail.id == target_post_detail_id) # Add another filtering option to an existing relationship 
          ) \
          .first()
        post_details = PostDetail.query.filter_by(post_id=id).all()
        post.post_details = post_details
        post_obj = post_schema.dump(post)
        # post_obj["current_post_detail"] = post_obj["target_post_detail"] # What should I do?
        post_detail_id = target_post_detail_id
      else:
        post = Post.query.filter_by(id=id, parent_id=None) \
          .join(PostDetail, Post.id==PostDetail.post_id, isouter=True) \
          .first()
        post_obj = post_schema.dump(post)
        post_detail_id = post_obj["current_post_detail"]["id"]
        post_obj["target_post_detail"] = None

      count_vote_obj = count_vote_ver2(post_obj, user_info_id, target_post_detail_id=target_post_detail_id)[0]
      count_vote_obj["gender_distribution"] = get_gender_distribution(post_detail_id)
      count_vote_obj["age_distribution"] = get_age_distribution(post_detail_id)
      count_vote_obj["my_vote"] = get_my_vote(post_detail_id, user_info_id)
      return count_vote_obj, 200

      # if do_filter == "yes":
      #   logger_api("do_filter", request.args)
      #   options = request.args
      #   id = request.args["id"]
      #   post = Post.query.filter_by(id=id, parent_id=None).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).first()
      #   status_code = 200
      #   post_obj = post_schema.dump(post)
      #   count_vote_obj = count_vote_option(post_obj, user_info_id, options)[0]
      #   count_vote_obj["gender_distribution"] = get_gender_distribution(id)
      #   count_vote_obj["age_distribution"] = get_age_distribution(id)
      #   count_vote_obj["my_vote"] = get_my_vote(id, user_info_id)
      #   return count_vote_obj, status_code


    """
    return posts based on the keyword (rubbish code.)

    keyword: 
    popular: return popular feed
    latest: return latest feed
    myposts: return user's own feed
    voted: return user's voted feed
    recommend: return user's individual feed (show only following topics)
    """
    if "keyword" in request.args.keys() and "page" in request.args.keys():
      keyword = request.args["keyword"]
      page = int(request.args["page"])
      logger_api("request.args['keyword']", request.args["keyword"])
      
      if keyword == "popular":
        time = request.args["time"] if ("time" in request.args.keys()) and (request.args["time"] != "") else None
        status_code = 200

        if time == "today":
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(hours=24)).isoformat()
        elif time == "now":
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(hours=1)).isoformat()
        elif time == "week":
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=7)).isoformat()
        elif time == "month":
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=30)).isoformat()
        else:
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=7)).isoformat()
        
        posts = Post.query \
          .filter(Post.country_id == country_id, Post.group_id==group_id, Post.parent_id==None) \
          .join(Post.current_post_detail) \
          .filter(PostDetail.created_at > yesterday_datetime) \
          .order_by(PostDetail.num_vote.desc()).distinct() \
          .paginate(page, per_page=config.POSTS_PER_PAGE).items
        
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        
        return count_vote_obj, status_code


      if keyword == "recommend":
        """
        get all posts that has topics the user has followed 
        """
        if user_info_id is None:
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=7)).isoformat()
          posts = Post.query \
          .filter(Post.country_id == country_id, Post.group_id==group_id, Post.parent_id==None) \
          .join(Post.current_post_detail) \
          .filter(PostDetail.created_at > yesterday_datetime) \
          .order_by(PostDetail.num_vote.desc()).distinct() \
          .paginate(page, per_page=config.POSTS_PER_PAGE).items
          
        else:
          posts = Post.query.filter_by(country_id=country_id, parent_id=None) \
          .join(Post.current_post_detail) \
          .join(PostTopic, PostTopic.post_id == Post.id, isouter=True) \
          .join(UserInfoTopic, UserInfoTopic.topic_id == PostTopic.topic_id, isouter=True) \
          .filter(UserInfoTopic.user_info_id == user_info_id) \
          .order_by(PostDetail.id.desc()).distinct() \
          .paginate(page, per_page=config.POSTS_PER_PAGE).items
          
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, 200

      if keyword == "latest":
        status_code = 200
        posts = Post.query \
          .filter_by(country_id=country_id, group_id=group_id, parent_id=None) \
          .join(Post.current_post_detail) \
          .order_by(PostDetail.id.desc()).distinct() \
          .paginate(page, per_page=config.POSTS_PER_PAGE).items
        
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, status_code

      if keyword == "myposts":
        posts = Post.query.distinct() \
        .filter_by(country_id=country_id, group_id=group_id, user_info_id=user_info_id, parent_id=None) \
        .order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items

        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, status_code

      if keyword == "voted":
        voted_post_list = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id).all()
        voted_post_id_list = [obj.post_id for obj in voted_post_list]

        posts = Post.query.distinct() \
        .filter(Post.country_id==country_id, Post.group_id==group_id, Post.id.in_(voted_post_id_list), Post.parent_id==None) \
        .order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items

        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, status_code
      
      if keyword == "following":
        
        try:
          body = handle_following_feed(user_info_id, country_id)
          return body, 200
        except:
          body = { "success": False }
          traceback.print_exc()
          return body, 400



      """
      others
      """
      return {}, 200


    """
    return searched results based on search word.

    e.g. search = "Apex"
    """
    if "search" in request.args.keys() and "page" in request.args.keys():
      search = request.args["search"]

      if "type" in request.args.keys():
        if request.args["type"] == "hash_tag":
          search = "#" + search

      page = int(request.args["page"])
      posts = Post.query \
        .filter(Post.country_id==country_id, Post.group_id==group_id, or_(Post.content.contains(search), Post.title.contains(search)), Post.parent_id==None) \
        .order_by(Post.id.desc()).distinct() \
        .paginate(page, per_page=config.POSTS_PER_PAGE).items
      status_code = 200
      post_obj = posts_schema.dump(posts)
      count_vote_obj = count_vote_ver2(post_obj, user_info_id)
      return count_vote_obj, status_code

    """
    return related posts of post_id = XX

    e.g. related_post_id = 10
    """
    if "related_post_id" in request.args.keys():
      related_post_id = request.args["related_post_id"]

      related_topic_list = Topic.query.join(PostTopic).filter_by(post_id=related_post_id).all()
      topic_id_list = [topic_obj.id for topic_obj in related_topic_list]
      related_topic_names = [topic_obj.topic for topic_obj in related_topic_list]

      posts = Post.query \
      .filter(Post.id != related_post_id, Post.country_id==country_id, Post.group_id==group_id, Post.parent_id==None) \
      .join(PostTopic) \
      .join(Topic) \
      .filter(Topic.id.in_(topic_id_list)) \
      .order_by(Post.id.desc()) \
      .distinct() \
      .limit(8) \
      .all()

      # .join(Post.vote_selects, isouter=True) \
      # .join(Post.vote_mjs, isouter=True) \
      # .join(Post.mj_options, isouter=True) \

      post_obj = posts_schema.dump(posts)
      count_vote_obj = count_vote_ver2(post_obj, user_info_id)
      return {"posts":count_vote_obj, "related_topics": related_topic_names}, 200



    """
    return topic feed

    e.g. topic = "Wraith"
    """
    if "topic" in request.args.keys() and "page" in request.args.keys():
      topic = request.args["topic"]
      page = int(request.args["page"])
      order_by = request.args["order_by"] if "order_by" in request.args.keys() else ""

      topic_obj = Topic.query.filter_by(topic=topic, country_id=country_id).first()
      topic_schema = TopicSchema()
      # order by
      if order_by == "popular":
        """ This month """
        yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=30)).isoformat() 
        target_topics = Post.query \
        .filter(Post.group_id==group_id, Post.parent_id==None, Post.country_id==country_id, Post.created_at > yesterday_datetime) \
        .join(PostTopic) \
        .join(Topic) \
        .filter_by(topic=topic) \
        .order_by(Post.num_vote.desc()).distinct()  \
        .paginate(page, per_page=config.POSTS_PER_PAGE).items
      else:
        target_topics = Post.query \
        .filter_by(group_id=group_id, parent_id=None, country_id=country_id) \
        .join(PostTopic) \
        .join(Topic) \
        .filter_by(topic=topic) \
        .order_by(Post.id.desc()).distinct()  \
        .paginate(page, per_page=config.POSTS_PER_PAGE).items

      status_code = 200
      post_obj = posts_schema.dump(target_topics)
      count_vote_obj = count_vote_ver2(post_obj, user_info_id)
      return { "posts": count_vote_obj, "topic": topic_schema.dump(topic_obj) }, status_code

    """
    return default feed.
    """
    posts = Post.query.filter_by(country_id=country_id, group_id=group_id, parent_id=None).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
    status_code = 200
    post_obj = posts_schema.dump(posts)
    count_vote_obj = count_vote_ver2(post_obj, user_info_id)
    return count_vote_obj, status_code



  @jwt_required
  @limiter.limit(config.DEFAULT_LIMIT)
  def post(self):
    """
    create a new post || recreate an exsiting poll

    title
    content
    end_at
    vote_obj
    vote_type_id
    topic
    group_id
    """
    logger_api("POST_posts_route", '')
    logger_api("request.json", str(request.json))
    data = request.get_json(force=True)
    logger_api("data", str(data))
    country_id = get_country_id(request)
    user_info_id = get_jwt_identity()

    if "id" in data.keys() and data["id"]:
      """
      if id, recreate a poll
      """
      try:
        handle_recreate(data, user_info_id, country_id)
        db.session.commit()
        return {"message": "successfully recreated a post"}, 200
      except NameError:
        db.session.rollback()
        return {"message": "wait 30 days to recreate"}, 400
      except:
        db.session.rollback()
        return {"message": "failed to recreate a post"}, 400

    else:
      """
      create a new poll
      """
      try:
        vote_type_id = data["vote_type_id"]
        group_id = data["group_id"] if ("group_id" in data.keys() and data["group_id"]) else None
        handle_create(data, user_info_id, country_id, vote_type_id, group_id)
        db.session.commit()
        return {"message": "successfully created a post"}, 200
      except:
        traceback.print_exc()
        db.session.rollback()
        return {"message": "failed to create a post"}, 400



    
    
    
    
"""
Util functions
"""




def order_filter_posts(feed): 
  
  """drop duplicates TODO: make it faster"""
  set_of_jsons = {json.dumps(d, sort_keys=True) for d in feed}
  dropped_feed = [json.loads(t) for t in set_of_jsons]
  
  """reorder feed by created_at""" 
  
  
  return dropped_feed

def handle_following_feed(user_info_id, country_id):
  """
  return following posts
  
  they contain:
  following_feed_type: 1. posts that following users has posted 
  following_feed_type: 2. posts that following users has voted
  following_feed_type: 3. posts that has topics the user is following
  
  thus not logged in users can't see this feed.
  """
  
  if not user_info_id:
    return {}, 200
  
  """following_feed_type: 1"""
  """posts that following users have posted"""
  following_posts_posted = Post.query \
    .filter_by(country_id=country_id, parent_id=None) \
    .join(UserInfoFollowing, Post.user_info_id == UserInfoFollowing.following_user_info_id) \
    .filter(UserInfoFollowing.following_user_info_id == user_info_id) \
    .limit(20).all()
    
  """attach who posted"""
  following_posts_posted = posts_schema.dump(following_posts_posted)
  new_following_posts_posted = []
  for each in following_posts_posted:
    each["following_feed_type"] = 1
    new_following_posts_posted.append(each)

  """following_feed_type: 2"""
  """posts that following users have voted"""
  following_posts_voted = Post.query \
    .filter_by(country_id=country_id, parent_id=None) \
    .join(UserInfoPostVoted) \
    .filter_by(user_info_id=user_info_id) \
    .limit(20).all()
    
  """attach who voted"""
  following_posts_voted = posts_schema.dump(following_posts_voted)
  new_following_posts_voted = []
  for each in following_posts_voted:
    each["following_feed_type"] = 2
    new_following_posts_voted.append(each)
    
  """following_feed_type: 3"""
  """posts that has following topics"""
  following_posts_topic = Post.query.filter_by(country_id=country_id, parent_id=None) \
    .join(Post.current_post_detail) \
    .join(PostTopic, PostTopic.post_id == Post.id, isouter=True) \
    .join(UserInfoTopic, UserInfoTopic.topic_id == PostTopic.topic_id, isouter=True) \
    .filter(UserInfoTopic.user_info_id == user_info_id) \
    .order_by(PostDetail.id.desc()).distinct().limit(20).all() \
    # .paginate(page, per_page=config.POSTS_PER_PAGE).items

  """attach what topic"""
  following_posts_topic = posts_schema.dump(following_posts_topic)
  new_following_posts_topic = []
  for each in following_posts_topic:
    each["following_feed_type"] = 3
    new_following_posts_topic.append(each)

  feed = [*following_posts_posted, *following_posts_voted, *following_posts_topic]
  
  """ordering posts or filtering posts"""
  post_obj = order_filter_posts(feed)
  count_vote_obj = count_vote_ver2(post_obj, user_info_id)
  return count_vote_obj





def handle_create(data, user_info_id, country_id, vote_type_id, group_id):
  """
  create a new poll
  """

  """
  vote_type_id = 3
  this is multiple posts. handle here to avoid code complexity
  """
  if vote_type_id == "3":
    handle_vote_type_3(data, country_id, user_info_id, group_id)
    return


  title = data['title']
  content = data['content']
  end_at = data['end_at']
  vote_obj = data["vote_obj"]
  topic_list = data["topic"]

  if not title:
    return {}, 400

  if validate_vote_obj(vote_obj):
    return {}, 400

  """
  vote_type_id = 1 meaning this is a simple vote post.
  """
  if vote_type_id == "1":
    vote_obj_list = [VoteSelect(content=obj["content"]) for obj in vote_obj]
    logger_api("vote_obj_list", vote_obj_list)
    new_post = Post(
      user_info_id=user_info_id,
      title=title,
      country_id=country_id,
      content=content,
      end_at=end_at,
      vote_selects=vote_obj_list,
      vote_type_id=1,
      group_id=group_id,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
    )

    db.session.add(new_post)
    db.session.flush()

    post_id = new_post.id

    new_post_detail = PostDetail(
      user_info_id=user_info_id,
      post_id=post_id,
      start_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
      end_at=end_at,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
      vote_selects=vote_obj_list,
    )

    """
    update current post detail id
    """
    db.session.add(new_post_detail)
    db.session.flush()
    current_post_detail_id = new_post_detail.id
    new_post.current_post_detail_id = current_post_detail_id

    """ 
    if this was posted in a group, update a relation between the post and the group
    """
    update_num_of_posts(group_id, post_id)

    """
    save topics of the posts
    """
    topic_ids = save_unique_topic(topic_list, country_id, post_id, group_id)

    db.session.add(new_post)
    return
    # return post_schema.dump(new_post), status_code


  """
  vote_type_id = 2. this post is majority judgement
  """
  # DO NOT DELETE
  # if vote_type_id == "2":
  #   try:
  #     vote_obj_list = [VoteMj(content=obj["content"]) for obj in vote_obj]
  #     logger_api("vote_obj_list", vote_obj_list)
  #     new_post = Post(
  #       user_info_id=user_info_id,
  #       title=title,
  #       country_id=country_id,
  #       content=content,
  #       end_at=end_at,
  #       vote_mjs=vote_obj_list,
  #       group_id=group_id,
  #       vote_type_id=2,
  #       created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
  #     )
      
  #     db.session.add(new_post)
  #     db.session.flush()

  #     post_id = new_post.id

  #     """ 
  #     if this was posted in a group, update a relation between the post and the group
  #     """
  #     update_num_of_posts(group_id, post_id)

  #     mj_option_list = request.json["mj_option_list"] #["良い", "やや良い", "普通", "やや悪い", "悪い"]
  #     new_mj_option = [MjOption(post_id=post_id, country_id=country_id, content=cont) for cont in mj_option_list]
  #     db.session.bulk_save_objects(new_mj_option)

  #     """
  #     save topics of the posts
  #     """
  #     topic_ids = save_unique_topic(topic_list, country_id, post_id, group_id)
  #     db.session.commit()
      
  #     status_code = 200
  #     return post_schema.dump(new_post), status_code

  #   except:
  #     db.session.rollback()
  #     return {}, 400
  return

def check_recreate_condition(data):
  last_post_detail = PostDetail.query.filter_by(post_id=data["id"]).order_by(PostDetail.id.desc()).first()
  last_end_at = datetime.fromisoformat(str(last_post_detail.end_at))
  last_end_at = last_end_at.replace(tzinfo=timezone(timedelta(days=0), 'UTC')) # as timezone UTC
  plus_30_days = timedelta(days=int(config.RECREATE_POLL_LIMIT_DAYS))
  last_end_at = last_end_at + plus_30_days
  current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC')) # as timezone UTC
  can_recreate = True if current_datetime > last_end_at else False
  if not can_recreate:
    raise NameError("can not recreate a poll until 30 days have passed from the last poll")
  return


def handle_recreate(data, user_info_id, country_id):
  """
  recreate a poll
  add another post detail
  add another vote options
  update post's current_post_detail_id
  """

  """
  check if latest end_at was more than 30 days ago
  """
  post_obj = Post.query.get(data["id"])
  vote_type_id = str(post_obj.vote_type_id)
  check_recreate_condition(data)

  """
  simple vote
  """
  if vote_type_id == "1":
    end_at = data["end_at"]
    post_id = data["id"]

    """
    update topic update_at
    """
    topic_list_obj = PostTopic.query.filter_by(post_id=post_id).all()
    updated_topic_list_obj = []
    for topic_obj in topic_list_obj:
      topic_obj.updated_at = datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      updated_topic_list_obj.append(topic_obj)

    new_post_detail = PostDetail(
      user_info_id=user_info_id,
      post_id=post_id,
      start_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
      end_at=end_at,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
    )

    db.session.add(new_post_detail)
    db.session.flush()
    current_post_detail_id = new_post_detail.id

    """
    update current post detail id
    """
    post_obj.current_post_detail_id = current_post_detail_id

    """
    add another vote option
    """
    vote_selects = post_obj.vote_selects
    vote_selects = vote_select_schema.dump(vote_selects)
    new_vote_selects = [ 
      VoteSelect(post_id=post_id, content=obj["content"], post_detail_id=current_post_detail_id) 
      for obj in vote_selects]

    db.session.add(post_obj)
    db.session.add_all(updated_topic_list_obj)
    db.session.add_all(new_vote_selects)
    db.session.commit()
    return

  """
  multiple vote
  """
  if vote_type_id == "3":
    end_at = data["end_at"]
    parent_id = data["id"]

    """
    update topic update_at
    """
    topic_list_obj = PostTopic.query.filter_by(post_id=parent_id).all()
    updated_topic_list_obj = []
    for topic_obj in topic_list_obj:
      topic_obj.updated_at = datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      updated_topic_list_obj.append(topic_obj)

    """
    parent
    """    
    new_parent_detail = PostDetail(
      user_info_id=user_info_id,
      post_id=parent_id,
      start_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
      end_at=end_at,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
    )

    db.session.add(new_parent_detail)
    db.session.flush()
    current_parent_detail_id = new_parent_detail.id
    """
    update current parent detail id
    """
    post_obj.current_post_detail_id = current_parent_detail_id
    db.session.add(post_obj)
    """
    children
    """
    children_post_list = Post.query.filter_by(parent_id=parent_id).all()
    for child in children_post_list:
      child_id = child.id
      new_child_detail = PostDetail(
        user_info_id=user_info_id,
        post_id=child_id,
        start_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
        end_at=end_at,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      )
      db.session.add(new_child_detail)
      db.session.flush()
      current_child_detail_id = new_child_detail.id
      """
      update current child detail id
      """
      child.current_post_detail_id = current_child_detail_id
      """
      add another vote option
      """
      vote_selects = child.vote_selects
      vote_selects = vote_select_schema.dump(vote_selects)
      new_vote_selects = [ 
        VoteSelect(post_id=child_id, content=obj["content"], post_detail_id=current_child_detail_id) 
        for obj in vote_selects]
      db.session.add(child)
      db.session.add_all(new_vote_selects)

    db.session.add_all(db.session.add_all(updated_topic_list_obj))
    return

  return



def validate_vote_obj(vote_obj):
  count = 0
  for obj in vote_obj:
    if len(obj["content"]) == 0:
      count += 1

  return False if count == 0 else True

def distribute_year(age_list):
  result =   {
    "0_9": 0,
    "10_19": 0,
    "20_29": 0,
    "30_39": 0,
    "40_49": 0,
    "50_59": 0,
    "60_69": 0,
    "70_79": 0,
    "80_89": 0,
    "90_99": 0,
    "100_109": 0,
    "110_119": 0,
  }

  for age in age_list:
    if 0 <= age <= 9:
      result["0_9"] = result["0_9"] + 1
    if 10 <= age <= 19:
      result["10_19"] = result["10_19"] + 1
    if 20 <= age <= 29:
      result["20_29"] = result["20_29"] + 1
    if 30 <= age <= 39:
      result["30_39"] = result["30_39"] + 1
    if 40 <= age <= 49:
      result["40_49"] = result["40_49"] + 1
    if 50 <= age <= 59:
      result["50_59"] = result["50_59"] + 1
    if 60 <= age <= 69:
      result["60_69"] = result["60_69"] + 1
    if 70 <= age <= 79:
      result["70_79"] = result["70_79"] + 1
    if 80 <= age <= 89:
      result["80_89"] = result["80_89"] + 1
    if 90 <= age <= 99:
      result["90_99"] = result["90_99"] + 1
    if 100 <= age <= 109:
      result["100_109"] = result["100_109"] + 1
    if 110 <= age <= 119:
      result["110_119"] = result["110_119"] + 1

  return result

def handle_vote_type_3(data, country_id, user_info_id, group_id):
  """
  save multiple posts
  currently, the post has only vote_type 1 children 

  data = {
    title: "",
    content: "",
    topic: [],
    children: [
      {
        title: "",
        content: "",
        vote_obj: [],
        vote_type_id: 1
      },
      { 
        ... 
      },
    ]
  }
  """

  if not data["title"]:
    raise ValueError("no title")

  topic_list = data["topic"]
  end_at = data["end_at"]
  start_at = datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

  parent_data = Post(
        parent_id=None,
        user_info_id=user_info_id,
        title=data["title"],
        country_id=country_id,
        content=data["content"],
        end_at=end_at,
        vote_type_id=3,
        group_id=group_id,
        created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      )
  
  db.session.add(parent_data)
  db.session.flush()
  parent_id = parent_data.id

  """
  create parent's post detail
  """
  new_parent_post_detail = PostDetail(
    user_info_id=user_info_id,
    post_id=parent_id,
    start_at=start_at,
    end_at=end_at,
    created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
  )
  """
  update parent post's current_post_detail_id
  """
  db.session.add(new_parent_post_detail)
  db.session.flush()
  current_post_detail_id = new_parent_post_detail.id
  parent_data.current_post_detail_id = current_post_detail_id
  db.session.add(parent_data)

  """
  if this was posted in a group, update a relation between the post and the group
  """
  update_num_of_posts(group_id, parent_id)

  """ 
  save topics of the posts
  """
  topic_ids = save_unique_topic(topic_list, country_id, parent_id, group_id)

  """
  save the children
  """
  for each in data["children"]:
    
    if validate_vote_obj(each["vote_obj"]):
      raise ValueError("Contains zero length vote obj")

    vote_obj_list = [VoteSelect(content=ea["content"]) for ea in each["vote_obj"]]
    children_post = Post(
          parent_id=parent_id,
          user_info_id=user_info_id,
          country_id=country_id,
          end_at=end_at,
          group_id=group_id,
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
          vote_type_id=1,
          title=each["title"],
          content=each["content"],
          vote_selects=vote_obj_list,
        )
    
    db.session.add(children_post)
    db.session.flush()

    children_id = children_post.id
    """
    create child's post detail
    """
    new_child_post_detail = PostDetail(
      user_info_id=user_info_id,
      post_id=children_id,
      start_at=start_at,
      end_at=end_at,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
      vote_selects=vote_obj_list,
    )
    """
    update current child post's post detail id
    """
    db.session.add(new_child_post_detail)
    db.session.flush()
    current_post_detail_id = new_child_post_detail.id
    children_post.current_post_detail_id = current_post_detail_id
    db.session.add(children_post)


  return



def get_gender_distribution(post_detail_id):
  """
  compute the number of male, female and others who posted the poll

  post_detail_id: id

  {
    male: 10, female: 30, others: 4
  }
  """
  # male 0, female 1, others 2
  base_data = UserInfo.query.join(UserInfoPostVoted, UserInfoPostVoted.user_info_id==UserInfo.id).filter_by(post_detail_id=post_detail_id).all()
  gender_data = [x.gender for x in base_data] # [0,0,0,1,1,0,2,1,1,1]
  # logger_api("gender_data", gender_data)
  male = gender_data.count(0)
  female = gender_data.count(1)
  others = gender_data.count(2)
  return {"male": male, "female": female, "others": others}


def get_age_distribution(post_detail_id):
  """
  get age distribution of the post

  {
    "0_9": 3,
    "10_19": 4,
    "20_29": 10,
    "30_39": 10,
    "40_49": 10,
    "50_59": 10,
    "60_69": 10,
    "70_79": 10,
    "80_89": 10,
    "90_99": 10,
    "100_109": 10,
    "110_119": 0
  }
  """

  def year_to_age(birth_year):
    if type(birth_year) == int:
      current_year = datetime.now(timezone(timedelta(hours=0), 'UTC')).year
      return current_year - birth_year

    else:
      return 0



  ## WORKING ON IT
  base_data = UserInfo.query.join(UserInfoPostVoted, UserInfoPostVoted.user_info_id==UserInfo.id).filter_by(post_detail_id=post_detail_id).all()
  birth_year_list = [x.birth_year for x in base_data] # [1999, 1980, 2000, 1976, 1989, ...]
  age_list = [ year_to_age(birth_year) for birth_year in birth_year_list]
  result = distribute_year(age_list)
  return result



def get_my_vote(post_detail_id, user_info_id):
  """
  return user's vote for the post
  currently only available for vote select (unavailable for vote mj)

  TODO: add vote mjs

  {
    "vote_select_id": 4
  }
  """

  result = VoteSelectUser.query.filter_by(user_info_id=user_info_id, post_detail_id=post_detail_id).first()
  if result is None:
    myvote = { "vote_select_id": None, "vote_mj_id": []}
  else:
    myvote = {"vote_select_id": result.vote_select_id, "vote_mj_id": []}
  return myvote

def update_num_of_posts(group_id, post_id):
  """
  if the post was posted in a group feed, update a relation between the post and the group
  """
  if group_id:
    group_obj = Group.query.filter_by(id=group_id).first()
    group_obj.num_of_posts = group_obj.num_of_posts + 1
    db.session.add(group_obj)
    return

  else:
    return

def get_posts_from_db():
  return


def save_unique_topic(topic_list, country_id, post_id, group_id):
  """
  check Topic Table and insert new topics to DB
  update num of posts of existential topics
  insert new topics
  return topic ids
  """
  topic_ids = []
  fetched_data = Topic.query.filter(Topic.topic.in_(topic_list), Topic.country_id == country_id).all()

  """
  doesn't add num of post if the post was posted in a closed group
  """
  add_num = 1
  if group_id:
    add_num = 0

  # update topic num of posts
  for topic in fetched_data:
    topic.num_of_posts = topic.num_of_posts + add_num

  # update num of posts
  db.session.bulk_save_objects(fetched_data)

  # rubbish code to distinguish new and existed topics
  topic_in_db = [data.topic for data in fetched_data]
  save_data = []
  for topic in topic_list:
    if topic in topic_in_db:
      pass
    else:
      save_data.append(Topic(topic=topic, country_id=country_id, num_of_posts=add_num))

  # save new topics
  for data in save_data:
    db.session.add(data)
  db.session.flush()

  # return all of topic ids
  existed_ids = [data.id for data in fetched_data]
  created_ids = [data.id for data in save_data]

  topic_ids = existed_ids + created_ids

  """
  save topics
  """
  if topic_ids and len(topic_ids) > 0:
    post_topic_data = [PostTopic(
      post_id=post_id,
      topic_id=tp_id,
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(),
      updated_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      ) for tp_id in topic_ids]
    db.session.bulk_save_objects(post_topic_data)

  return topic_ids


def count_vote_ver2(posts, user_info_id, is_parent=False, target_post_detail_id=None):
  """
  rewriting count_vote to optimize performance 
  count votes of the post
  rubbish code.

  three conditions:
  vote type 1
  vote type 2
  vote type 3
  """
  if type(posts) == dict:
    posts = [posts]

  for idx, post in enumerate(posts):
    post_id = post["id"]
    post_detail_id = post["current_post_detail_id"]
    vote_type_id = post["vote_type"]["id"]

    if vote_type_id == 1:
      """
      DB access
      """
      if is_parent and target_post_detail_id:
        vote_selects_obj = post["target_post_detail"]["vote_selects"] if post["target_post_detail"] else []
        end_at = post["target_post_detail"]["end_at"]
        post_detail_id = post["target_post_detail"]["id"]
      elif target_post_detail_id:
        vote_selects_obj = post["target_post_detail"]["vote_selects"] if post["target_post_detail"] else []
        end_at = post["target_post_detail"]["end_at"]
        post_detail_id = post["target_post_detail"]["id"]
      else:
        vote_selects_obj = post["current_post_detail"]["vote_selects"] if post["current_post_detail"] else []
        end_at = post["current_post_detail"]["end_at"]
        post["target_post_detail"] = None
      
      vote_select_ids = [obj["id"] for obj in vote_selects_obj]
      vote_selects_count = [{"vote_select_id": obj["id"], "count": obj["count"],
                             "content": obj["content"]} for obj in vote_selects_obj]
      total_vote = sum([obj["count"] for obj in vote_selects_obj])

      """
      DB access
      """
      already_voted = True if UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_detail_id=post_detail_id).count() > 0 else False

      current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
      end_datetime = datetime.fromisoformat(end_at)
      end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

      vote_period_end = True if current_datetime > end_datetime else False
      
      posts[idx]["vote_select_ids"] = vote_select_ids
      posts[idx]["vote_selects_count"] = vote_selects_count
      posts[idx]["already_voted"] = already_voted
      posts[idx]["total_vote"] = total_vote
      posts[idx]["vote_period_end"] = vote_period_end
      posts[idx]["my_vote"] = get_my_vote(post_detail_id, user_info_id)

      """
      add age and gender dist iff is_parent True
      to improve performance
      """
      if is_parent:
        posts[idx]["gender_distribution"] = get_gender_distribution(post_detail_id)
        posts[idx]["age_distribution"] = get_age_distribution(post_detail_id)
      
    
    elif vote_type_id == 2:
      # """
      # DB access
      # """
      # raw_mj_options = MjOption.query.filter_by(post_id=post_id).all()
      # mj_options = {obj.id: obj.content for obj in raw_mj_options}
      # # ADD USER FILTERING LATER

      # """
      # DB access
      # """
      # vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(VoteMj, VoteMj.id==VoteMjUser.vote_mj_id).all() 
      # vote_mj_ids = list({obj.vote_mj_id for obj in vote_mj_user_obj})

      # """
      # DB access
      # """
      # vote_mj_obj = [{"vote_mj_id": obj.id, "content": obj.content} for obj in VoteMj.query.filter(VoteMj.id.in_(vote_mj_ids)).all()]
      # count_obj = [  {"vote_mj_id": mj_id, "mj_option_ids":[ obj.mj_option_id for obj in vote_mj_user_obj if mj_id==obj.vote_mj_id]} for mj_id in vote_mj_ids ]
      # total_vote = len(count_obj[0]["mj_option_ids"]) if len(count_obj) != 0 else 0
      # vote_mj_count = [{"count": [{"mj_option_id":key, "content":mj_options[key], "count": val} for key, val in dict(Counter(obj["mj_option_ids"])).items()], "vote_mj_id": obj["vote_mj_id"]}  for obj in count_obj]

      # """
      # DB access
      # """
      # already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

      # current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
      # end_datetime = datetime.fromisoformat(post["end_at"])
      # end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

      # vote_period_end = True if current_datetime > end_datetime else False
      
      # posts[idx]["vote_mj_ids"] = vote_mj_ids
      # posts[idx]["vote_mj_count"] = vote_mj_count
      # posts[idx]["vote_mj_obj"] = vote_mj_obj
      # posts[idx]["already_voted"] = already_voted
      # posts[idx]["total_vote"] = total_vote
      # posts[idx]["vote_period_end"] = vote_period_end
      # posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)
      pass

    elif vote_type_id == 3:
      post_detail_id = target_post_detail_id if target_post_detail_id else post["current_post_detail_id"]
      end_datetime = post["target_post_detail"]["end_at"] if target_post_detail_id else post["current_post_detail"]["end_at"]
      """
      DB access
      """
      total_vote = UserInfoPostVoted.query.filter_by(post_detail_id=post_detail_id).count()

      """
      DB access
      """
      num_of_user_info_post_voted = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_detail_id=post_detail_id).count()
      already_voted = True if num_of_user_info_post_voted > 0 else False
      current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
      end_datetime = datetime.fromisoformat(end_datetime)
      end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))
      vote_period_end = True if current_datetime > end_datetime else False

      """
      DB access
      """
      num_of_children = Post.query.filter_by(parent_id=post_id).count()

      posts[idx]["already_voted"] = already_voted
      posts[idx]["total_vote"] = total_vote
      posts[idx]["vote_period_end"] = vote_period_end
      posts[idx]["num_of_children"] = num_of_children

  return posts





# def filter_vote_selects_options(options, user_info_id, vote_select_ids):
#   gender = options["gender"]
#   min_birth_year = options["min_birth_year"]
#   max_birth_year = options["max_birth_year"]
#   occupation = options["occupation"]

#   logger_api(options, 'options')

#   if gender == None:
#     vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).join(UserInfo, UserInfo.id==VoteSelectUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.birth_year >= min_birth_year, UserInfo.birth_year <= max_birth_year, ).all()

#   elif occupation == None:
#     vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).join(UserInfo, UserInfo.id==VoteSelectUser.user_info_id).filter(UserInfo.gender==gender, UserInfo.birth_year >= min_birth_year, UserInfo.birth_year <= max_birth_year, ).all()

#   else:
#     vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).join(UserInfo, UserInfo.id==VoteSelectUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.gender==gender, UserInfo.birth_year >= min_birth_year, UserInfo.birth_year <= max_birth_year, ).all()

#   return vote_select_user_obj

# def filter_vote_mjs_options(options, user_info_id, post_id):
#   gender = options["gender"]
#   min_birth_year = options["min_birth_year"]
#   max_birth_year = options["max_birth_year"]
#   occupation = options["occupation"]
  
#   if gender == None:
#     vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(UserInfo, UserInfo.id==VoteMjUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.age >= min_birth_year, UserInfo.birth_year <= max_birth_year, ).all()

#   elif occupation == None:
#     vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(UserInfo, UserInfo.id==VoteMjUser.user_info_id).filter(UserInfo.gender==gender, UserInfo.birth_year >= min_birth_year, UserInfo.birth_year <= max_birth_year, ).all()

#   else:
#     vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(UserInfo, UserInfo.id==VoteMjUser.user_info_id).filter(UserInfo.occupation==occupation, UserInfo.gender==gender, UserInfo.birth_year >= min_birth_year, UserInfo.birth_year <= max_birth_year, ).all()

#   return vote_mj_user_obj

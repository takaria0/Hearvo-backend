import os
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import traceback
      

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from sqlalchemy import or_

import Hearvo.config as config
from ..app import logger, cache, limiter
from ..models import db, Post, PostSchema, VoteSelect, VoteSelectUser, UserInfoPostVoted, UserInfo, VoteMj, MjOption, VoteMjUser, Topic, PostTopic, PostGroup, Group, UserInfoPostVotedSchema, UserInfoGroup, UserInfoTopic, TopicSchema

from .logger_api import logger_api
from Hearvo.middlewares.detect_language import get_country_id
from Hearvo.utils import cache_delete_latest_posts, cache_delete_all_posts

user_info_post_voted_schema = UserInfoPostVotedSchema(many=True)


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

  end_at = data["end_at"]
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

  topic_list = data["topic"]

  db.session.add(parent_data)
  db.session.flush()

  parent_id = parent_data.id
  """  if this was posted in a group, update a relation between the post and the group """
  update_num_of_posts(group_id, parent_id)

  """ save topics of the posts """
  topic_ids = save_unique_topic(topic_list, country_id, parent_id, group_id)

  """ save the children """
  children_data_all = []
  for each in data["children"]:
    vote_obj_list = [VoteSelect(content=ea["content"]) for ea in each["vote_obj"]]
     # not working. have to add after children insert
    children_data = Post(
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
    children_data_all.append(children_data)

  db.session.add_all(children_data_all)

  return



def get_gender_distribution(post_id):
  """
  compute the number of male, female and others who posted the poll

  post_id: id

  {
    male: 10, female: 30, others: 4
  }
  """
  # male 0, female 1, others 2
  base_data = UserInfo.query.join(UserInfoPostVoted, UserInfoPostVoted.user_info_id==UserInfo.id).filter_by(post_id=post_id).all()
  gender_data = [x.gender for x in base_data] # [0,0,0,1,1,0,2,1,1,1]
  # logger_api("gender_data", gender_data)
  male = gender_data.count(0)
  female = gender_data.count(1)
  others = gender_data.count(2)
  return {"male": male, "female": female, "others": others}


def get_age_distribution(post_id):
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
  base_data = UserInfo.query.join(UserInfoPostVoted, UserInfoPostVoted.user_info_id==UserInfo.id).filter_by(post_id=post_id).all()
  birth_year_list = [x.birth_year for x in base_data] # [1999, 1980, 2000, 1976, 1989, ...]
  age_list = [ year_to_age(birth_year) for birth_year in birth_year_list]
  result = distribute_year(age_list)
  return result



def get_my_vote(post_id, user_info_id):
  """
  return user's vote for the post
  currently only available for vote select (unavailable for vote mj)

  TODO: add vote mjs

  {
    "vote_select_id": 4
  }
  """

  result = VoteSelectUser.query.filter_by(user_info_id=user_info_id, post_id=post_id).first()
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
      created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
      ) for tp_id in topic_ids]
    db.session.bulk_save_objects(post_topic_data)

  return topic_ids


def count_vote_ver2(posts, user_info_id, is_parent=False):
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
    vote_type_id = post["vote_type"]["id"]

    if vote_type_id == 1:
      vote_selects_obj = post["vote_selects"]
      vote_select_ids = [obj["id"] for obj in vote_selects_obj]

      """
      DB access
      """
      vote_select_user_obj = VoteSelectUser.query.filter(VoteSelectUser.vote_select_id.in_(vote_select_ids)).all()

      count_obj = {obj.user_info_id: obj.vote_select_id for obj in vote_select_user_obj}
      id_content_table = {obj["id"]: obj["content"] for obj in vote_selects_obj}

      vote_selects_count = Counter(count_obj.values())
      total_vote = sum(vote_selects_count.values())
      data = dict(Counter(count_obj.values()))
      vote_selects_count = [{"vote_select_id": id, "count": data[id], "content": id_content_table[id]} if id in data.keys() else {"vote_select_id": id, "count": 0, "content": id_content_table[id]} for id in vote_select_ids ]

      """
      DB access
      """
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
      posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)

      """
      add age and gender dist iff is_parent True
      to improve performance
      """
      if is_parent:
        posts[idx]["gender_distribution"] = get_gender_distribution(post_id)
        posts[idx]["age_distribution"] = get_age_distribution(post_id)
      
    
    elif vote_type_id == 2:
      """
      DB access
      """
      raw_mj_options = MjOption.query.filter_by(post_id=post_id).all()
      mj_options = {obj.id: obj.content for obj in raw_mj_options}
      # ADD USER FILTERING LATER

      """
      DB access
      """
      vote_mj_user_obj = VoteMjUser.query.filter_by(post_id=post_id).join(VoteMj, VoteMj.id==VoteMjUser.vote_mj_id).all() 
      vote_mj_ids = list({obj.vote_mj_id for obj in vote_mj_user_obj})

      """
      DB access
      """
      vote_mj_obj = [{"vote_mj_id": obj.id, "content": obj.content} for obj in VoteMj.query.filter(VoteMj.id.in_(vote_mj_ids)).all()]
      count_obj = [  {"vote_mj_id": mj_id, "mj_option_ids":[ obj.mj_option_id for obj in vote_mj_user_obj if mj_id==obj.vote_mj_id]} for mj_id in vote_mj_ids ]
      total_vote = len(count_obj[0]["mj_option_ids"]) if len(count_obj) != 0 else 0
      vote_mj_count = [{"count": [{"mj_option_id":key, "content":mj_options[key], "count": val} for key, val in dict(Counter(obj["mj_option_ids"])).items()], "vote_mj_id": obj["vote_mj_id"]}  for obj in count_obj]

      """
      DB access
      """
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
      posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)

    elif vote_type_id == 3:

      """
      DB access
      """
      total_vote = len(UserInfoPostVoted.query.filter_by(post_id=post_id).all())

      """
      DB access
      """
      user_info_post_voted_obj = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()
      already_voted = True if len(user_info_post_voted_obj) > 0 else False

      current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
      end_datetime = datetime.fromisoformat(post["end_at"])
      end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))
      vote_period_end = True if current_datetime > end_datetime else False
      children_posts = Post.query.filter_by(parent_id=post_id).all()

      posts[idx]["already_voted"] = already_voted
      posts[idx]["total_vote"] = total_vote
      posts[idx]["vote_period_end"] = vote_period_end
      posts[idx]["num_of_children"] = len(children_posts)

  return posts









def count_vote(posts, user_info_id):
  """
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
      posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)
      posts[idx]["gender_distribution"] = get_gender_distribution(post_id)
      posts[idx]["age_distribution"] = get_age_distribution(post_id)
      
    
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
      posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)

    elif vote_type_id == 3:
      total_vote = len(UserInfoPostVoted.query.filter_by(post_id=post_id).all())
      user_info_post_voted_obj = UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()
      already_voted = True if len(user_info_post_voted_obj) > 0 else False

      current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
      end_datetime = datetime.fromisoformat(post["end_at"])
      end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))
      vote_period_end = True if current_datetime > end_datetime else False
      children_posts = Post.query.filter_by(parent_id=post_id).all()

      posts[idx]["already_voted"] = already_voted
      posts[idx]["total_vote"] = total_vote
      posts[idx]["vote_period_end"] = vote_period_end
      posts[idx]["num_of_children"] = len(children_posts)

  return posts


# def count_vote_option(posts, user_info_id, options):
#   if type(posts) == dict:
#     posts = [posts]

#   options = options_validate(options)
#   for idx, post in enumerate(posts):
#     post_id = post["id"]
#     vote_type_id = post["vote_type"]["id"]

#     if vote_type_id == 1:
      
#       post_obj = Post.query.filter_by(id=post_id).first()
#       vote_selects_obj = post_obj.vote_selects

#       vote_select_ids = [obj.id for obj in vote_selects_obj]
#       vote_select_user_obj = filter_vote_selects_options(options, user_info_id, vote_select_ids)
      
#       count_obj = {obj.user_info_id: obj.vote_select_id for obj in vote_select_user_obj}
#       id_content_table = {obj.id: obj.content for obj in vote_selects_obj}

#       vote_selects_count = Counter(count_obj.values())
#       total_vote = sum(vote_selects_count.values())
#       data = dict(Counter(count_obj.values()))
#       vote_selects_count = [{"vote_select_id": id, "count": data[id], "content": id_content_table[id]} if id in data.keys() else {"vote_select_id": id, "count": 0, "content": id_content_table[id]} for id in vote_select_ids ]

#       already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

#       current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
#       end_datetime = datetime.fromisoformat(post["end_at"])
#       end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

#       vote_period_end = True if current_datetime > end_datetime else False
      
#       posts[idx]["vote_select_ids"] = vote_select_ids
#       posts[idx]["vote_selects_count"] = vote_selects_count
#       posts[idx]["already_voted"] = already_voted
#       posts[idx]["total_vote"] = total_vote
#       posts[idx]["vote_period_end"] = vote_period_end
#       posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)

#     elif vote_type_id == 2:
#       raw_mj_options = MjOption.query.filter_by(post_id=post_id).all()
#       mj_options = {obj.id: obj.content for obj in raw_mj_options}

#       vote_mj_user_obj = filter_vote_mjs_options(options, user_info_id, post_id)
#       vote_mj_ids = list({obj.vote_mj_id for obj in vote_mj_user_obj})

#       vote_mj_obj = [{"vote_mj_id": obj.id, "content": obj.content} for obj in VoteMj.query.filter(VoteMj.id.in_(vote_mj_ids)).all()]
#       count_obj = [  {"vote_mj_id": mj_id, "mj_option_ids":[ obj.mj_option_id for obj in vote_mj_user_obj if mj_id==obj.vote_mj_id]} for mj_id in vote_mj_ids ]
#       total_vote = len(count_obj[0]["mj_option_ids"]) if len(count_obj) != 0 else 0
#       vote_mj_count = [{"count": [{"mj_option_id":key, "content":mj_options[key], "count": val} for key, val in dict(Counter(obj["mj_option_ids"])).items()], "vote_mj_id": obj["vote_mj_id"]}  for obj in count_obj]

#       already_voted = True if len(UserInfoPostVoted.query.filter_by(user_info_id=user_info_id, post_id=post_id).all()) > 0 else False

#       current_datetime = datetime.now(timezone(timedelta(hours=0), 'UTC'))
#       end_datetime = datetime.fromisoformat(post["end_at"])
#       end_datetime = end_datetime.replace(tzinfo=timezone(timedelta(hours=0), 'UTC'))

#       vote_period_end = True if current_datetime > end_datetime else False
      
#       posts[idx]["vote_mj_ids"] = vote_mj_ids
#       posts[idx]["vote_mj_count"] = vote_mj_count
#       posts[idx]["vote_mj_obj"] = vote_mj_obj
#       posts[idx]["already_voted"] = already_voted
#       posts[idx]["total_vote"] = total_vote
#       posts[idx]["vote_period_end"] = vote_period_end
#       posts[idx]["my_vote"] = get_my_vote(post_id, user_info_id)

#   return posts


# def string_check(content):
#   if (len(content.replace(" ", "")) == 0):
#     return False
#   else:
#     return True


# def options_validate(options):
  
#   def age_to_year(age):
#     current_year = datetime.now(timezone(timedelta(hours=0), 'UTC')).year
#     return current_year - age

#   if "gender" in options.keys():
#     gender = options["gender"] if string_check(options["gender"]) else None
#   else:
#     gender = None

#   if "min_age" in options.keys():
#     max_birth_year = age_to_year(int(options["min_age"])) if string_check(options["min_age"]) else 0
#   else:
#     max_birth_year = 0

#   if "max_age" in options.keys():
#     min_birth_year = age_to_year(int(options["max_age"])) if string_check(options["max_age"]) else 3000
#   else:
#     min_birth_year = 3000

#   if "occupation" in options.keys():
#     occupation = options["occupation"] if string_check(options["occupation"]) else None
#   else:
#     occupation = None

  
#   return {"gender": gender, "min_birth_year": min_birth_year, "max_birth_year": max_birth_year, "occupation": occupation}



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


#########################################
# Schema
#########################################
post_schema = PostSchema()
posts_schema = PostSchema(many=True)

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
      try:
        parent_id = request.args["parent_id"]
        posts = Post.query.filter_by(parent_id=parent_id).all()
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id, is_parent=True)
        return count_vote_obj, 200
      except:
        return {}, 400

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
     get single post based on the post_id
     rubbish code. need to update
    """
    if "id" in request.args.keys():
      # do_filter = request.args["do_filter"] if "do_filter" in request.args.keys() else "no"

      id = request.args["id"]
      post = Post.query.filter_by(id=id, parent_id=None).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).first()
      status_code = 200
      post_obj = post_schema.dump(post)
      count_vote_obj = count_vote_ver2(post_obj, user_info_id)[0]
      count_vote_obj["gender_distribution"] = get_gender_distribution(id)
      count_vote_obj["age_distribution"] = get_age_distribution(id)
      count_vote_obj["my_vote"] = get_my_vote(id, user_info_id)
      return count_vote_obj, status_code

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
        .filter(Post.country_id == country_id, Post.created_at > yesterday_datetime, Post.group_id==group_id, Post.parent_id==None) \
        .join(Post.vote_selects, isouter=True) \
        .join(Post.vote_mjs, isouter=True) \
        .join(Post.mj_options, isouter=True) \
        .order_by(Post.num_vote.desc()).distinct() \
        .paginate(page, per_page=config.POSTS_PER_PAGE).items
        
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        
        return count_vote_obj, status_code


      if keyword == "recommend":
        """
        get all posts that has topics which the user has followed 
        """
        if user_info_id is None:
          yesterday_datetime = (datetime.now(timezone(timedelta(hours=0), 'UTC')) - timedelta(days=7)).isoformat()
          posts = Post.query \
          .filter(Post.country_id == country_id, Post.created_at > yesterday_datetime, Post.group_id==group_id, Post.parent_id==None) \
          .join(Post.vote_selects, isouter=True) \
          .join(Post.vote_mjs, isouter=True) \
          .join(Post.mj_options, isouter=True) \
          .order_by(Post.num_vote.desc()).distinct() \
          .paginate(page, per_page=config.POSTS_PER_PAGE).items
          
        else:
          posts = Post.query.filter_by(country_id=country_id, parent_id=None) \
          .join(Post.vote_selects, isouter=True) \
          .join(Post.vote_mjs, isouter=True) \
          .join(Post.mj_options, isouter=True) \
          .join(PostTopic, PostTopic.id == Post.id, isouter=True) \
          .join(UserInfoTopic, UserInfoTopic.topic_id == PostTopic.topic_id, isouter=True) \
          .filter(UserInfoTopic.user_info_id == user_info_id) \
          .order_by(Post.id.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
          
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, 200

      if keyword == "latest":
        status_code = 200
        posts = Post.query \
        .filter_by(country_id=country_id, group_id=group_id, parent_id=None) \
        .join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True) \
        .join(Post.mj_options, isouter=True) \
        .order_by(Post.id.desc()).distinct() \
        .paginate(page, per_page=config.POSTS_PER_PAGE).items
        
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, status_code

      if keyword == "myposts":
        posts = Post.query.distinct() \
        .filter_by(country_id=country_id, group_id=group_id, user_info_id=user_info_id, parent_id=None) \
        .join(Post.vote_selects, isouter=True) \
        .join(Post.vote_mjs, isouter=True) \
        .join(Post.mj_options, isouter=True) \
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
        .join(Post.vote_selects, isouter=True) \
        .join(Post.vote_mjs, isouter=True) \
        .join(Post.mj_options, isouter=True) \
        .order_by(Post.id.desc()).paginate(page, per_page=config.POSTS_PER_PAGE).items

        status_code = 200
        post_obj = posts_schema.dump(posts)
        count_vote_obj = count_vote_ver2(post_obj, user_info_id)
        return count_vote_obj, status_code

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
      posts = Post.query.filter(Post.country_id==country_id, Post.group_id==group_id, or_(Post.content.contains(search), Post.title.contains(search)), Post.parent_id==None).join(Post.vote_selects, isouter=True).join(Post.vote_mjs, isouter=True).join(Post.mj_options, isouter=True).order_by(Post.id.desc()).distinct().paginate(page, per_page=config.POSTS_PER_PAGE).items
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
    create a new post

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
    vote_type_id = data["vote_type_id"]
    group_id = data["group_id"] if ("group_id" in data.keys() and data["group_id"]) else None

    """
    vote_type_id = 3
    this is multiple posts. handle here to avoid code complexity
    """
    if vote_type_id == "3":
      try:
        handle_vote_type_3(data, country_id, user_info_id, group_id)
        db.session.commit()
        return {"message": "successfully created a post"}, 200
      except:
        db.session.rollback()
        return {}, 400


    title = data['title']

    if not title:
      raise ValueError("no title")

    content = data['content']
    end_at = data['end_at']
    vote_obj = data["vote_obj"]
    topic_list = data["topic"]
    


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

      # try:
      db.session.add(new_post)
      db.session.flush()

      post_id = new_post.id

      """ 
      if this was posted in a group, update a relation between the post and the group
      """
      update_num_of_posts(group_id, post_id)

      """
      save topics of the posts
      """
      topic_ids = save_unique_topic(topic_list, country_id, post_id, group_id)

      db.session.commit()
      status_code = 200
      return post_schema.dump(new_post), status_code

      # except:
      #   db.session.rollback()
      #   return {}, 400

    """
    vote_type_id = 2. this post is majority judgement
    """
    if vote_type_id == "2":
      try:
        vote_obj_list = [VoteMj(content=obj["content"]) for obj in vote_obj]
        logger_api("vote_obj_list", vote_obj_list)
        new_post = Post(
          user_info_id=user_info_id,
          title=title,
          country_id=country_id,
          content=content,
          end_at=end_at,
          vote_mjs=vote_obj_list,
          group_id=group_id,
          vote_type_id=2,
          created_at=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()
        )
        
        db.session.add(new_post)
        db.session.flush()

        post_id = new_post.id

        """ 
        if this was posted in a group, update a relation between the post and the group
        """
        update_num_of_posts(group_id, post_id)

        mj_option_list = request.json["mj_option_list"] #["良い", "やや良い", "普通", "やや悪い", "悪い"]
        new_mj_option = [MjOption(post_id=post_id, country_id=country_id, content=cont) for cont in mj_option_list]
        db.session.bulk_save_objects(new_mj_option)

        """
        save topics of the posts
        """
        topic_ids = save_unique_topic(topic_list, country_id, post_id, group_id)
        db.session.commit()
        
        status_code = 200
        return post_schema.dump(new_post), status_code

      except:
        db.session.rollback()
        return {}, 400

    """
    other input.
    might add vote_type_id=3, 4 ,5 ... add it here then
    """
    return {}, 400

    





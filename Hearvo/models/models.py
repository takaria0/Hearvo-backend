from datetime import datetime, timedelta, timezone
from typing import List
from flask_sqlalchemy import SQLAlchemy


from ..app import db #, ma



#########################################
# Model (DB) and Schema (Serialization)
#########################################


#########################################
# Post
#########################################
class Post(db.Model):
  __tablename__ = "post"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  parent_id = db.Column(db.BigInteger, primary_key=False, nullable=True, default=None)
  title = db.Column(db.String(200), nullable=False)
  content = db.Column(db.String(5000), nullable=True)
  num_comment = db.Column(db.BigInteger, default=0)
  num_vote = db.Column(db.BigInteger, default=0)
  start_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  end_at = db.Column(db.DateTime, default=None)
  is_deleted = db.Column(db.Boolean, default=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  country_id = db.Column(db.BigInteger, db.ForeignKey('country.id'), nullable=True)
  vote_type_id = db.Column(db.BigInteger, db.ForeignKey('vote_type.id'), nullable=False)
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)
  group_id = db.Column(db.BigInteger, db.ForeignKey('group.id'), nullable=True)
  current_post_detail_id = db.Column(db.BigInteger, db.ForeignKey('post_detail.id'), nullable=True)

  # One to Many
  # primary_join argument replace the default join condition, which is basically Post.id==PostDetail.post_id .
  post_details = db.relationship("PostDetail", primaryjoin="Post.id==PostDetail.post_id", foreign_keys=id, uselist=True, order_by="PostDetail.id")
  target_post_detail = db.relationship("PostDetail", primaryjoin="Post.id==PostDetail.post_id", foreign_keys=id, uselist=False, lazy='subquery',)
  # post_details = db.relationship("PostDetail", backref="post_details")
  current_post_detail = db.relationship("PostDetail", backref="post", primaryjoin="and_(Post.id==PostDetail.post_id, Post.current_post_detail_id==PostDetail.id)", foreign_keys="[Post.id, Post.current_post_detail_id]")
  vote_selects = db.relationship("VoteSelect", order_by="VoteSelect.id", backref="post") # DELETE IN THE FUTURE
  vote_mjs = db.relationship("VoteMj", backref="post")  # DELETE IN THE FUTURE
  mj_options = db.relationship("MjOption", backref="post")  # DELETE IN THE FUTURE
  comments = db.relationship("Comment", backref="post")
  topics = db.relationship("PostTopic", backref="post")

  def __repr__(self):
      return '<Post %s>' % self.title

#########################################
# PostDetail
#########################################
class PostDetail(db.Model):
  __tablename__ = "post_detail"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  num_vote = db.Column(db.BigInteger, default=0)
  start_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  end_at = db.Column(db.DateTime, default=None)
  is_deleted = db.Column(db.Boolean, default=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(
  ), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)

  # One to Many
  vote_selects = db.relationship("VoteSelect", order_by="VoteSelect.id", backref="post_detail")
  vote_mjs = db.relationship("VoteMj", backref="post_detail")
  mj_options = db.relationship("MjOption", backref="post_detail")

  def __repr__(self):
      return '<PostDetail %s>' % self.id



#########################################
# User
#########################################
class User(db.Model):
  __tablename__ = "user"
  
  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  google_id = db.Column(db.String(32), unique=True, nullable=True)
  name = db.Column(db.String(100), unique=True)
  email = db.Column(db.String(350), unique=True)
  deleted_email = db.Column(db.String(350), unique=False)
  hashed_password = db.Column(db.String(150), nullable=True)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  def __repr__(self):
      return '<User %s>' % self.name


#########################################
# UserInfo
#########################################
class UserInfo(db.Model):
  __tablename__ = "user_info"
  
  
  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  string_id = db.Column(db.String(20), unique=True)
  name = db.Column(db.String(100))
  profile_name = db.Column(db.String(100))
  first_name = db.Column(db.String(100))
  middle_name = db.Column(db.String(100))
  last_name = db.Column(db.String(100))
  description = db.Column(db.String(300))
  occupation = db.Column(db.String(100))
  gender = db.Column(db.BigInteger, primary_key=False) # 0 male, 1 female, 2 others
  gender_detail = db.Column(db.String(20))
  age = db.Column(db.BigInteger)
  birthday = db.Column(db.DateTime)
  birth_year = db.Column(db.BigInteger)
  login_count = db.Column(db.BigInteger, default=0)
  hide_realname = db.Column(db.Boolean, default=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
  country_id = db.Column(db.BigInteger, db.ForeignKey('country.id'), nullable=True)

  # One to Many
  posts = db.relationship("Post", backref="user_info")
  comments = db.relationship("Comment", backref="user_info")

  # Many to Many
  vote_selects = db.relationship("VoteSelect", secondary="vote_select_user")

  def __repr__(self):
      return '<User %s>' % self.name




#########################################
# VoteSelect
#########################################
class VoteSelect(db.Model):
  __tablename__ = "vote_select"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  # post_id = db.Column(db.String(20))
  content = db.Column(db.String(100))
  count = db.Column(db.BigInteger, default=0)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=True) # DELETE IN THE FUTURE?
  post_detail_id = db.Column(db.BigInteger, db.ForeignKey('post_detail.id'), nullable=False)

  # Many to Many
  users = db.relationship("UserInfo", secondary="vote_select_user")

  def __repr__(self):
      return '<VoteSelect %s>' % self.post_id




#########################################
# VoteSelectUser (Associate Many to Many for User and VoteSelect)
#########################################
class VoteSelectUser(db.Model):
  __tablename__ = "vote_select_user"

  # id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  vote_select_id = db.Column(db.BigInteger, db.ForeignKey('vote_select.id'), primary_key=True) # is this pk ok?
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), primary_key=True) # is this pk ok?
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), primary_key=True) # is this pk ok?
  post_detail_id = db.Column(db.BigInteger, db.ForeignKey('post_detail.id'), nullable=False)

  # one to one
  user_info = db.relationship('UserInfo', backref='vote_select_user', lazy=True, uselist=False)


  def __repr__(self):
      return '<VoteSelectUser %s>' % self.vote_select_id



#########################################
# VoteMj
#########################################
class VoteMj(db.Model):
  __tablename__ = "vote_mj"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)

  content = db.Column(db.String(500))
  mj_type = db.Column(db.BigInteger)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'))
  post_detail_id = db.Column(db.BigInteger, db.ForeignKey('post_detail.id'), nullable=False)

  def __repr__(self):
      return '<VoteMj %s>' % self.post_id


#########################################
# MjOption
#########################################
class MjOption(db.Model):
  __tablename__ = "mj_option"
  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  content = db.Column(db.String(300))

  # Foreign Key
  country_id = db.Column(db.BigInteger, db.ForeignKey('country.id'), nullable=True)
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)
  post_detail_id = db.Column(db.BigInteger, db.ForeignKey('post_detail.id'), nullable=False)

  def __repr__(self):
      return '<MjOption %s>' % self.post_id





#########################################
# VoteMjUser
#########################################
class VoteMjUser(db.Model):
  __tablename__ = "vote_mj_user"

  # id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  vote_mj_id = db.Column(db.BigInteger, db.ForeignKey('vote_mj.id'), primary_key=True)
  mj_option_id = db.Column(db.BigInteger, db.ForeignKey('mj_option.id'), primary_key=True)
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), primary_key=True)
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), primary_key=True)



#########################################
# Comment
#########################################
class Comment(db.Model):
  __tablename__ = "comment"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  parent_id = db.Column(db.BigInteger, nullable=True)

  content = db.Column(db.String(5000), nullable=True)
  num_of_good = db.Column(db.BigInteger, primary_key=False, default=0)
  num_of_bad = db.Column(db.BigInteger, primary_key=False, default=0)

  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)

  # one to many
  comment_favs = db.relationship("CommentFav", backref="comment")

  def __repr__(self):
      return '<Comment %s>' % self.content

#########################################
# CommentFav
#########################################
class CommentFav(db.Model):
  __tablename__ = "comment_fav"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  good_or_bad = db.Column(db.BigInteger, primary_key=False, default=0) # 1 is good, 0 is bad

  # Foreign Key
  comment_id = db.Column(db.BigInteger, db.ForeignKey('comment.id'), nullable=False)
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)



# #########################################
# # Lang
# #########################################
# class Lang(db.Model):
#   __tablename__ = "lang"

#   id = db.Column(db.BigInteger, primary_key=True, nullable=False)
#   language = db.Column(db.String(100), nullable=False)

#   def __repr__(self):
#       return ' Lang %s>' % self.language

#########################################
# Country
#########################################
class Country(db.Model):
  __tablename__ = "country"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  country = db.Column(db.String(100), nullable=False)

  def __repr__(self):
      return ' Country <%s>' % self.country


#########################################
# UserInfoPostVoted
#########################################
class UserInfoPostVoted(db.Model):
  __tablename__ = "user_info_post_voted"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)
  vote_type_id = db.Column(db.BigInteger, db.ForeignKey('vote_type.id'), nullable=False)
  post_detail_id = db.Column(db.BigInteger, db.ForeignKey('post_detail.id'), nullable=False)

  def __repr__(self):
      return '<UserInfoPostVoted %s>' % self.content


#########################################
# VoteType
#########################################
class VoteType(db.Model):
  __tablename__ = "vote_type"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  vote_type = db.Column(db.String(50))

  # one to many
  posts = db.relationship("Post", backref="vote_type")

  def __repr__(self):
      return '<VoteType %s>' % self.content





#########################################
# Topic
#########################################
class Topic(db.Model):
  __tablename__ = "topic"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  topic = db.Column(db.String(200), nullable=True)
  num_of_posts = db.Column(db.BigInteger, default=0)
  num_of_users = db.Column(db.BigInteger, default=0)

  # Foreign Key
  country_id = db.Column(db.BigInteger, db.ForeignKey('country.id'), nullable=True)

#########################################
# UserInfoTopic
#########################################
class UserInfoTopic(db.Model):
  __tablename__ = "user_info_topic"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)
  topic_id = db.Column(db.BigInteger, db.ForeignKey('topic.id'), nullable=False)


#########################################
# PostTopic
#########################################
class PostTopic(db.Model):
  __tablename__ = "post_topic"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)
  topic_id = db.Column(db.BigInteger, db.ForeignKey('topic.id'), nullable=False)

  topic = db.relationship("Topic", backref="post_topic")


#########################################
# Group
#########################################
class Group(db.Model):
  __tablename__ = "group"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  title = db.Column(db.String(200), nullable=False)
  link = db.Column(db.String(100), nullable=False)
  num_of_users = db.Column(db.BigInteger, primary_key=False, default=0)
  num_of_posts = db.Column(db.BigInteger, primary_key=False, default=0)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  country_id = db.Column(db.BigInteger, db.ForeignKey('country.id'), nullable=True)
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)

#########################################
# PostGroup
#########################################
class PostGroup(db.Model):
  __tablename__ = "post_group"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=False)
  group_id = db.Column(db.BigInteger, db.ForeignKey('group.id'), nullable=False)

  
#########################################
# UserInfoGroup
#########################################
class UserInfoGroup(db.Model):
  __tablename__ = "user_info_group"

  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)
  group_id = db.Column(db.BigInteger, db.ForeignKey('group.id'), nullable=False)

#########################################
# Report
#########################################
class Report(db.Model):
  __tablename__ = "report"
  
  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.BigInteger, db.ForeignKey('user_info.id'), nullable=False)
  post_id = db.Column(db.BigInteger, db.ForeignKey('post.id'), nullable=True)
  comment_id = db.Column(db.BigInteger, db.ForeignKey('comment.id'), nullable=True)
  # One to Many
  

  # Many to Many
  


#########################################
# ReportReason
#########################################
class ReportReason(db.Model):
  __tablename__ = "report_reason"
  
  id = db.Column(db.BigInteger, primary_key=True, nullable=False)
  report_id = db.Column(db.BigInteger,db.ForeignKey('report.id'))
  reason = db.Column(db.Integer)
  reason_detail = db.Column(db.String(300),nullable=True)



  

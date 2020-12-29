from datetime import datetime, timedelta, timezone

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

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  title = db.Column(db.String(200), nullable=False)
  content = db.Column(db.String(5000), nullable=True)
  num_comment = db.Column(db.Integer, default=0)
  num_vote = db.Column(db.Integer, default=0)
  start_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  end_at = db.Column(db.DateTime, default=None)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  lang_id = db.Column(db.Integer, db.ForeignKey('lang.id'), nullable=False)
  vote_type_id = db.Column(db.Integer, db.ForeignKey('vote_type.id'), nullable=False)
  user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), nullable=False)

  # One to Many
  vote_selects = db.relationship("VoteSelect", backref="post")
  vote_mjs = db.relationship("VoteMj", backref="post")
  mj_options = db.relationship("MjOption", backref="post")
  comments = db.relationship("Comment", backref="post")

  def __repr__(self):
      return '<Post %s>' % self.title



#########################################
# User
#########################################
class User(db.Model):
  __tablename__ = "user"
  
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  # string_id = db.Column(db.String(20), unique=True)
  # name = db.Column(db.String(100))
  # email = db.Column(db.String(350), unique=True)
  # description = db.Column(db.String(300))
  # occupation = db.Column(db.String(100))
  # gender = db.Column(db.String(100))
  # age = db.Column(db.Integer)
  # birthday = db.Column(db.DateTime)
  email = db.Column(db.String(350), unique=True)
  hashed_password = db.Column(db.String(150), nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # One to Many
  # posts = db.relationship("Post", backref="user")
  # comments = db.relationship("Comment", backref="user")

  # Many to Many
  # vote_selects = db.relationship("VoteSelect", secondary="vote_select_user")

  def __repr__(self):
      return '<User %s>' % self.name


#########################################
# UserInfo
#########################################
class UserInfo(db.Model):
  __tablename__ = "user_info"
  
  
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  string_id = db.Column(db.String(20), unique=True)
  name = db.Column(db.String(100))
  description = db.Column(db.String(300))
  occupation = db.Column(db.String(100))
  gender = db.Column(db.String(100))
  age = db.Column(db.Integer)
  birthday = db.Column(db.DateTime)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  lang_id = db.Column(db.Integer, db.ForeignKey('lang.id'), nullable=False)

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

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  # post_id = db.Column(db.String(20))
  content = db.Column(db.String(100))
  count = db.Column(db.Integer)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

  # Many to Many
  users = db.relationship("UserInfo", secondary="vote_select_user")

  def __repr__(self):
      return '<VoteSelect %s>' % self.post_id




#########################################
# VoteSelectUser (Associate Many to Many for User and VoteSelect)
#########################################
class VoteSelectUser(db.Model):
  __tablename__ = "vote_select_user"

  # id = db.Column(db.Integer, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  vote_select_id = db.Column(db.Integer, db.ForeignKey('vote_select.id'), primary_key=True)
  user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), primary_key=True)
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)

  def __repr__(self):
      return '<VoteSelectUser %s>' % self.vote_select_id



#########################################
# VoteMj
#########################################
class VoteMj(db.Model):
  __tablename__ = "vote_mj"

  id = db.Column(db.Integer, primary_key=True, nullable=False)

  content = db.Column(db.String(500))
  mj_type = db.Column(db.Integer)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

  def __repr__(self):
      return '<VoteMj %s>' % self.post_id


#########################################
# MjOption
#########################################
class MjOption(db.Model):
  __tablename__ = "mj_option"
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  content = db.Column(db.String(300))

  # Foreign Key
  lang_id = db.Column(db.Integer, db.ForeignKey('lang.id'), nullable=False)
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
  # vote_mj_id = db.Column(db.Integer, db.ForeignKey('vote_mj.id'), nullable=False)

  def __repr__(self):
      return '<MjOption %s>' % self.post_id





#########################################
# VoteMjUser
#########################################
class VoteMjUser(db.Model):
  __tablename__ = "vote_mj_user"

  # id = db.Column(db.Integer, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  vote_mj_id = db.Column(db.Integer, db.ForeignKey('vote_mj.id'), primary_key=True)
  mj_option_id = db.Column(db.Integer, db.ForeignKey('mj_option.id'), primary_key=True)
  user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), primary_key=True)
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)



#########################################
# Comment
#########################################
class Comment(db.Model):
  __tablename__ = "comment"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  parent_id = db.Column(db.Integer, nullable=True)

  content = db.Column(db.String(5000), nullable=True)

  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), nullable=False)
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)


  def __repr__(self):
      return '<Comment %s>' % self.content


#########################################
# Lang
#########################################
class Lang(db.Model):
  __tablename__ = "lang"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  language = db.Column(db.String(500), nullable=False)

  def __repr__(self):
      return ' Lang %s>' % self.language


#########################################
# UserInfoPostVoted
#########################################
class UserInfoPostVoted(db.Model):
  __tablename__ = "user_info_post_voted"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), nullable=False)
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
  vote_type_id = db.Column(db.Integer, db.ForeignKey('vote_type.id'), nullable=False)

  def __repr__(self):
      return '<UserInfoPostVoted %s>' % self.content


#########################################
# VoteType
#########################################
class VoteType(db.Model):
  __tablename__ = "vote_type"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
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

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  topic = db.Column(db.String(200), nullable=True)
  num_of_contents = db.Column(db.Integer, default=0)

  # Foreign Key
  lang_id = db.Column(db.Integer, db.ForeignKey('lang.id'), nullable=False)

#########################################
# UserInfoTopic
#########################################
class UserInfoTopic(db.Model):
  __tablename__ = "user_info_topic"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  user_info_id = db.Column(db.Integer, db.ForeignKey('user_info.id'), nullable=False)
  topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)


#########################################
# PostTopic
#########################################
class PostTopic(db.Model):
  __tablename__ = "post_topic"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())
  updated_at = db.Column(db.DateTime, default=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat(), onupdate=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat())

  # Foreign Key
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
  topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)




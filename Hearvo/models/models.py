from datetime import datetime

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
  title = db.Column(db.String(100), nullable=False)
  content = db.Column(db.String(300), nullable=True)
  start_at = db.Column(db.DateTime, default=datetime.utcnow())
  end_at = db.Column(db.DateTime, default=None)
  created_at = db.Column(db.DateTime, default=datetime.utcnow())
  updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

  # Foreign Key
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  # One to Many
  vote_selects = db.relationship("VoteSelect", backref="post")

  def __repr__(self):
      return '<Post %s>' % self.title



#########################################
# User
#########################################
class User(db.Model):
  __tablename__ = "user"
  
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  string_id = db.Column(db.String(20))
  name = db.Column(db.String(100))
  email = db.Column(db.String(350))
  description = db.Column(db.String(300))
  occupation = db.Column(db.String(100))
  gender = db.Column(db.String(100))
  age = db.Column(db.Integer)
  birthday = db.Column(db.DateTime)
  hashed_password = db.Column(db.String(150), nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.utcnow())
  updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

  # One to Many
  posts = db.relationship("Post", backref="user")

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
  post_id = db.Column(db.String(20))
  content = db.Column(db.String(100))
  count = db.Column(db.Integer)
  created_at = db.Column(db.DateTime, default=datetime.utcnow())
  updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

  # Foreign Key
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

  # Many to Many
  users = db.relationship("User", secondary="vote_select_user")

  def __repr__(self):
      return '<VoteSelect %s>' % self.post_id




#########################################
# VoteSelectUser (Associate Many to Many for User and VoteSelect)
#########################################
class VoteSelectUser(db.Model):
  __tablename__ = "vote_select_user"

  # id = db.Column(db.Integer, primary_key=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.utcnow())
  updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

  # Foreign Key
  vote_select_id = db.Column(db.Integer, db.ForeignKey('vote_select.id'), primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

  def __repr__(self):
      return '<VoteSelectUser %s>' % self.vote_select_id



#########################################
# VoteMj
#########################################
class VoteMj(db.Model):
  __tablename__ = "vote_mj"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  post_id = db.Column(db.String(20))
  content = db.Column(db.String(100))
  count = db.Column(db.Integer)
  created_at = db.Column(db.DateTime, default=datetime.utcnow())
  updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

  # Foreign Key
  post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

  def __repr__(self):
      return '<VoteMj %s>' % self.title



#########################################
# MjOption
#########################################
class MjOption(db.Model):
  __tablename__ = "mj_option"
  id = db.Column(db.Integer, primary_key=True, nullable=False)
  rank = db.Column(db.String(20))
  option = db.Column(db.String(100))


  def __repr__(self):
      return '<MjOption %s>' % self.title




#########################################
# VoteMjUser
#########################################
class VoteMjUser(db.Model):
  __tablename__ = "vote_mj_user"

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  post_id = db.Column(db.String(20))
  content = db.Column(db.String(100))
  count = db.Column(db.Integer)

  created_at = db.Column(db.DateTime, default=datetime.utcnow())
  updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

  def __repr__(self):
      return '<VoteMjUser %s>' % self.title



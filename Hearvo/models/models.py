from datetime import datetime
from ..app import db, ma
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow



class Test(db.Model):
  __tablename__ = "test"
  id = db.Column(db.Integer, primary_key=True)
  content = db.Column(db.String(100))

#########################################
# Model (DB) and Schema (Serialization)
#########################################

#########################################
# Person
#########################################

class Person(db.Model):
    __tablename__ = 'person'
    person_id = db.Column(db.Integer,
                          primary_key=True)
    lname = db.Column(db.String)
    fname = db.Column(db.String)
    timestamp = db.Column(db.DateTime,
                          default=datetime.utcnow(),
                          onupdate=datetime.utcnow())

class PersonSchema(ma.Schema):
    class Meta:
        model = Person
        sqla_session = db.session


#########################################
# Product
#########################################

class Product(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    price = db.Column(db.Float)
    qty = db.Column(db.Integer)

    def __init__(self, name, description, price, qty):
        self.name = name
        self.description = description
        self.price = price
        self.qty = qty


class ProductSchema(ma.Schema):
    class Meta:
        fields = ('_id', 'name', 'description', 'price', 'qty')


#########################################
# Post
#########################################

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.String(300))


    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

    def __repr__(self):
        return '<Post %s>' % self.title


class PostSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "content")

#########################################
# User
#########################################
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    string_id = db.Column(db.String(20))
    name = db.Column(db.String(100))
    description = db.Column(db.String(300))

    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

    def __repr__(self):
        return '<User %s>' % self.title


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "string_id", "name", "description")

#########################################
# VoteSelect
#########################################
class VoteSelect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(20))
    content = db.Column(db.String(100))
    count = db.Column(db.Integer(11))

    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

    def __repr__(self):
        return '<VoteSelect %s>' % self.title


class VoteSelectSchema(ma.Schema):
    class Meta:
        fields = ("id", "string_id", "name", "description")

#########################################
# VoteMJ
#########################################
class VoteMJ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(20))
    content = db.Column(db.String(100))
    count = db.Column(db.Integer(11))

    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

    def __repr__(self):
        return '<VoteMJ %s>' % self.title


class VoteMJSchema(ma.Schema):
    class Meta:
        fields = ("id", "string_id", "name", "description")


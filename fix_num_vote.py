"""
DO NOT RUN THIS SCRIPT
"""

from Hearvo.models import db, PostDetail, Post, VoteSelect, UserInfoPostVoted, VoteSelectUser

try:
  posts = Post.query.all()

  for post in posts:
    post_detail = PostDetail.query.filter_by(post_id=post.id).first()
    post_detail.num_vote = post.num_vote
    db.session.add(post_detail)


  db.session.commit()

except:
  db.session.rollback()
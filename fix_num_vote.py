"""
DO NOT RUN THIS SCRIPT
"""

from Hearvo.models import db, PostDetail, Post, VoteSelect, UserInfoPostVoted, VoteSelectUser

try:
  posts = Post.query.filter_by(parent_id=None).all()

  for parent_post in posts:
    children_posts = Post.query.filter_by(parent_id=parent_post.id).all()

    if len(children_posts) == 0:
      pass

    for child_post in children_posts:

      if child_post.num_vote == 0:
        child_post.num_vote = parent_post.num_vote
        db.session.add(child_post)
        post_detail = PostDetail.query.filter_by(post_id=child_post.id).first()
        post_detail.num_vote = child_post.num_vote
        db.session.add(post_detail)
        
      pass




  db.session.commit()

except:
  db.session.rollback()
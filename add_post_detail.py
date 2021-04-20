"""
DO NOT RUN THIS SCRIPT
"""


raise NameError("You have to delete this error to run this script.")



from Hearvo.models import db, PostDetail, Post, VoteSelect, UserInfoPostVoted, VoteSelectUser

try:
  posts = Post.query.filter_by(current_post_detail_id=None).all()

  for post in posts:
    new_vote_selects = VoteSelect.query.filter_by(post_id=post.id, post_detail_id=None).all()
    new_user_info_post_voted = UserInfoPostVoted.query.filter_by(post_id=post.id, post_detail_id=None).all()
    new_vote_select_user = VoteSelectUser.query.filter_by(post_id=post.id, post_detail_id=None).all()
    new_post_detail = PostDetail(
      post_id=post.id,
      user_info_id=post.user_info_id,
      created_at=post.created_at,
      updated_at=post.updated_at,
      start_at=post.start_at,
      end_at=post.end_at
      )

    db.session.add(new_post_detail)
    db.session.flush()
    new_post_detail_id = new_post_detail.id


    """
    vote_selects
    """
    for vote_select in new_vote_selects:
      vote_select.post_detail_id = new_post_detail_id
      db.session.add(vote_select)

    """
    user_info_post_voted
    """
    for user_info_post_voted in new_user_info_post_voted:
      user_info_post_voted.post_detail_id = new_post_detail_id
      db.session.add(user_info_post_voted)

    """
    vote_select_user
    """
    for vote_select_user in new_vote_select_user:
      vote_select_user.post_detail_id = new_post_detail_id
      db.session.add(vote_select_user)

    post.current_post_detail_id = new_post_detail_id
    db.session.add(post)

  db.session.commit()

except:
  db.session.rollback()
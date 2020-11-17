# Don't run this script

# heroku run python

# copy and paste below
from Hearvo.models import Lang, db, VoteType
db.create_all()

lang_1 = Lang(language="ja")
lang_2 = Lang(language="en")

db.session.add(lang_1)
db.session.add(lang_2)

vote_1 = VoteType(vote_type="vote_select")
vote_2 = VoteType(vote_type="vote_mj") 

db.session.add(vote_1)
db.session.add(vote_2)
db.session.commit()
# Don't run this script

# heroku run python

# copy and paste below
from Hearvo.models import Country, db, VoteType
db.create_all()

country_1 = Country(language="jp")
country_2 = Country(language="us")

db.session.add(country_1)
db.session.add(country_2)

vote_1 = VoteType(vote_type="vote_select")
vote_2 = VoteType(vote_type="vote_mj") 
vote_3 = VoteType(vote_type="multiple_vote") 

db.session.add(vote_1)
db.session.add(vote_2)
db.session.add(vote_3)

db.session.commit()
# Environment
for Mac

LANG: 
- Python 3.9 / Flask



# For Production

## How to deploy to Heroku

(for the first time)

1. heroku login
2. heroku create
3. git push heroku production:main


add postgres addon and initialize database

4. heroku run python
5. copy and paste db_init_for_heroku.py one by one
6. OK

useful commands
- heroku logs --tail

make sure to commit before pushing to heroku
git commit -am "ahahha"
git push heroku production:main

 
# migration (local)

when you add a new column or table, try below before deploy

```
docker container list # to look up XXX
docker exec -it XXX bash
flask db migrate
flask db upgrade
```

above command migrate db and update the migrations folder. 

# migration (on Heroku)

delete algembric_version table


```
heroku run flask db migrate
heroku run flask db upgrade
```

```
heroku run python3
from Hearvo.models import Lang, db, VoteType
db.create_all()
```

# Inititialize Database

INSERT these values as in db_init_for_heroku.py
```
from Hearvo.models import Country, db, VoteType
db.create_all()

country_1 = Country(country="jp")
country_2 = Country(country="us")

db.session.add(country_1)
db.session.add(country_2)

vote_1 = VoteType(vote_type="vote_select")
vote_2 = VoteType(vote_type="vote_mj") 
vote_3 = VoteType(vote_type="multiple_vote") 

db.session.add(vote_1)
db.session.add(vote_2)
db.session.add(vote_3)

db.session.commit()
```

# TODO since 2020-11-07

- introduce Swagger


- document the general idea and my intention for the future dev


- introduce testing (pytest)


- future versioning idea (right now just add v1.0 to URL)


- login / logout auth
add bcrypt authentication system. We might add google, facebook login soon.
AND ALSO, HOW TO MAKE ENDPOINTS LOGIN REQURED


- add validation for each endpoint
as soon as possible


- how to connect backend and frontend? search some ideas


- one-many relationship, many-many relationship


- might need to read SQLAlchemy doc throughly
espesially try, catch and performance issues
and DB types and options. like, required=True or something

- understand flask session

- Consider TIME ZONE

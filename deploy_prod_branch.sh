heroku login
git add -A
git commit -m "deploy"
git push heroku stable:main



# heroku run flask db upgrade
# heroku run flask db migrate

# heroku run python
# from Hearvo.models import Lang, db, VoteType
# db.create_all()

# heroku run python3 db_init_for_heroku.py


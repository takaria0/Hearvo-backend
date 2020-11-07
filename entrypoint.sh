#!/usr/bin/env bash
 
# echo flask db init
# flask db init

echo flask db migrate
flask db migrate

echo flask db upgrade
flask db upgrade

echo python3 run.py
python3 run.py
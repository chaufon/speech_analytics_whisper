#!/bin/bash
python manage.py reset_db --no-input
rm -rf apps/*/migrations/000*
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata dev/roles.json
python manage.py loaddata dev/campaigns.json
python manage.py loaddata dev/users.json
python manage.py loaddata dev/agents.json
python manage.py loaddata dev/wordlists.json
python manage.py loaddata dev/words.json
python manage.py loaddata dev/typifications.json
python manage.py loaddata dev/patterns.json
python manage.py loaddata dev/config.json
python manage.py search_index --rebuild -f

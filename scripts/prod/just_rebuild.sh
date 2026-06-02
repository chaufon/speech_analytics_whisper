#!/bin/bash
psql -d postgres -c "DROP DATABASE IF EXISTS speech;"
psql -d postgres -c "CREATE DATABASE speech OWNER your_db_user;"
redis-cli -s /var/run/redis/redis-server.sock -n 2 FLUSHDB
redis-cli -s /var/run/redis/redis-server.sock -n 0 FLUSHDB
python manage.py migrate
python manage.py loaddata prod/roles.json
python manage.py loaddata prod/campaigns.json
python manage.py loaddata prod/users.json
python manage.py loaddata prod/config.json
python manage.py search_index --rebuild -f

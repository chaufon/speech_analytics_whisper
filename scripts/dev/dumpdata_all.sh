#!/bin/bash
python manage.py dumpdata --all --indent 2 users.Role > apps/users/fixtures/dev/roles.json
python manage.py dumpdata --all --indent 2 users.Campaign > apps/users/fixtures/dev/campaigns.json
python manage.py dumpdata --all --indent 2 users.User > apps/users/fixtures/dev/users.json
python manage.py dumpdata --all --indent 2 analytics.Agent > apps/analytics/fixtures/dev/agents.json
python manage.py dumpdata --all --indent 2 analytics.WordList > apps/analytics/fixtures/dev/wordlists.json
python manage.py dumpdata --all --indent 2 analytics.Word > apps/analytics/fixtures/dev/words.json
python manage.py dumpdata --all --indent 2 analytics.Typification > apps/analytics/fixtures/dev/typifications.json
python manage.py dumpdata --all --indent 2 analytics.Pattern > apps/analytics/fixtures/dev/patterns.json
python manage.py dumpdata --all --indent 2 analytics.Process > apps/analytics/fixtures/dev/processes.json
python manage.py dumpdata --all --indent 2 analytics.Audio > apps/analytics/fixtures/dev/audios.json
python manage.py dumpdata --all --indent 2 analytics.AudioSegment > apps/analytics/fixtures/dev/audio_segments.json
python manage.py dumpdata --all --indent 2 common.Config > apps/common/fixtures/dev/config.json

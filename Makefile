all: test
	

clean:
	rm -rf build

env:
	@if [ ! -d "build" ]; then virtualenv build; fi


deps: env
	# For leaderboard
	@build/bin/pip install -Ue '.[dev]'
	# For IRC
	@build/bin/pip install -U google-api-python-client limnoria
	mkdir build/run
	mkdir build/run/logs
	mkdir build/run/data
	mkdir build/run/conf



leaderboard:
	@build/bin/python \
		scripts/start-chevah-leaderboard.py \
		build/trac.db build/irc-logs/ --nodaemon

report:
	@build/bin/python -m chevah.leaderboard.highscores \
		build/trac.db build/irc-logs/

bot:
	cp limnoria-plugins/robi-net.conf.seed build/robi-net.conf
	@build/bin/supybot --debug build/robi-net.conf

irc-bot-oauth:
	@build/bin/python limnoria-plugins/SupportNotifications/make_credentials.py \
		client_id.json \
		build/run/credentials.json


lint:
	@build/bin/pyflakes chevah/ scripts/ limnoria-plugins/
	@build/bin/pep8 chevah/ scripts/ limnoria-plugins/


test: lint
	@build/bin/python setup.py test

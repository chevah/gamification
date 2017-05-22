all: test
	

clean:
	rm -rf build

env:
	@if [ ! -d "build" ]; then virtualenv build; fi


deps: env
	# For leaderboard
	@build/bin/pip install -Ue '.[dev]'

run:
	@build/bin/python \
		scripts/start-chevah-leaderboard.py \
		build/trac.db build/irc-logs/ --nodaemon

report:
	@build/bin/python -m chevah.leaderboard.highscores \
		build/trac.db build/irc-logs/

lint:
	@build/bin/pyflakes chevah/ scripts/
	@build/bin/pep8 chevah/ scripts/


test: lint
	@build/bin/python setup.py test

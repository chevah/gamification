
# Default time for report.
TIME ?= `date -I`

all: test
	

clean:
	rm -rf build

env:
	@if [ ! -d "build" ]; then virtualenv build; fi


deps: env
	# For leaderboard
	@build/bin/pip install -Ue '.[dev]'

run:
	@build/bin/python scripts/start-chevah-leaderboard.py \
		build/leaderboard.toml \
		--port=tcp:8080:interface=127.0.0.1 --nodaemon

report:
	@echo "Reporting for $(TIME)"
	@build/bin/python -m chevah.leaderboard.highscores \
		build/leaderboard.toml $(TIME)

lint:
	@build/bin/pyflakes chevah/ scripts/
	@build/bin/pep8 chevah/ scripts/


test: lint
	@build/bin/python setup.py test

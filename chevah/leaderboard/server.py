"""
This is the entry point of the server.
"""
from __future__ import absolute_import, unicode_literals
import os
from datetime import datetime

from klein import resource, route
from twisted.web.static import File

from chevah.leaderboard import highscores

# Shut up the linter.
resource  # noqa

STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')


@route('/',  methods=['GET'])
def highscores_handler(request):
    request.setHeader(b'content-type', b'text/html; charset=utf-8')
    if 'time' in request.args:
        y, m, d = map(int, request.args['time'][0].split("-"))
        t = highscores.Time.fromDatetime(datetime(year=y, month=m, day=d))
    else:
        t = highscores.Time()

    highscores.renderPage(time=t, output=request.write)
    return b''


@route('/static', branch=True)
def static(request):
    """
    All files from static.
    """
    result = File(STATIC_PATH)
    result.contentTypes[b'.woff2'] = b'application/font-woff2'
    return result

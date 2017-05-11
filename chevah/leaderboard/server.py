"""
This is the entry point of the server.
"""
from __future__ import absolute_import, unicode_literals
import os

from klein import resource, route
from twisted.web.static import File
# Shut up the linter.
resource

from chevah.leaderboard import highscores

CONFIGURATION = {'trac-db': 'paht/to/trac-db-not-defined.yet'}

STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')


@route('/',  methods=['GET'])
def highscores_handler(request):
    highscores.CONFIGURATION['trac-db'] = (CONFIGURATION['trac-db'],)

    request.setHeader(b'content-type', b'text/html; charset=utf-8')
    if 'time' in request.args:
        t = highscores.parsetime(request.args['time'][0])
    else:
        t = highscores.Time()

    highscores.renderPage(time=t, output=request.write)
    return b''


@route('/static', branch=True)
def static(request):
    """
    All files from static.
    """
    return File(STATIC_PATH)

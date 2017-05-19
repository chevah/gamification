#!env python
"""
Entry point for the hooks server.

It setup up event handler and starts twistd.

It reads Trac credentials file and pass all other arguments to twistd web.
twistd arguments are only supported in `--option=X` format.
It also support some non-web twistd commands.

twistd web does not allow passing any extra arguments so we pass them via
the CONFIGURATION global.
"""
import sys

from twisted.scripts.twistd import run

from chevah.leaderboard.server import CONFIGURATION


if __name__ == '__main__':

    if len(sys.argv) < 3:
        raise AssertionError(
            'Launch script with at least the path to the Trac DB.')

    # Pass the trac credentials in a safer way.
    CONFIGURATION['trac-db'] = sys.argv[1]
    CONFIGURATION['irc-logs'] = sys.argv[2]

    base_arguments = []
    web_arguments = []
    for argument in sys.argv[3:]:
        if (
            argument.startswith('--pidfile') or
            argument.startswith('--nodaemon')
                ):
            base_arguments.append(argument)
        else:
            web_arguments.append(argument)

    sys.argv = ['twistd']
    sys.argv.extend(base_arguments)
    sys.argv.extend([
        'web',
        '--class', 'chevah.leaderboard.server.resource',
        ])
    sys.argv.extend(web_arguments)

    # Start twistd.
    sys.exit(run())

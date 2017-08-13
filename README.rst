gamification
============

Tools used to experiment with gamification.


leaderboard
-----------

Leaderboard will read the team's activity from Trac db and IRC logs.

It will use the leaderboard.toml config file, which might look like::

    [chevah.leaderboard]
    # Path to the Trac DB File
    trac_db = 'path/to/trac.db'
    # Path to the Lemnoria IRC Bot logs for the channel.
    irc_log = 'path/to/lemnoria/irc/logs/dir/'
    # You can define a list of usernames which are ignored. For example
    # for robots.
    ignore_authors = ['chevah-robot']

        # When the same team member has different usernames on various sources,
        # you can use this to aggregate under a single name.
        [chevah.leaderboard.aliases]
        mark = ['mark0', 'Mark Rubert', 'mark.rubert']

        # You can apply a factor to the total points in order to compensate
        # for team members working part time or more than the other team.
        [chevah.leaderboard.handicaps]
        john = 1.33
        mark = 0.66

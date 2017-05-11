# -*- coding: utf-8 -*-
#
#
#

import sqlite3
import os
from re import split
from itertools import chain, count, groupby
from operator import itemgetter
from datetime import timedelta, datetime


from twisted.web.template import Element, XMLFile, renderer, tags, flatten
from twisted.python.filepath import FilePath

from chevah.leaderboard.extime import Time

LINK_STYLE = "text-decoration: none; color: white;"

CONFIGURATION = {
    'trac-db': ('no/such/path/define-a-trac-db',),
    'irc-logs': 'no/such/path/logs/',
    }


UNKNOWN_OWNER = 'UNKNOWN'
IGNORED_AUTHORS = [
    'chevah-robot',
    UNKNOWN_OWNER,
    ]


AUTHOR_ALIASES = {
    'adi': ['adiroiban'],
    'hcs': ['hcs0'],
    'laura': ['laurici'],
    'dumol': ['Mișu Moldovan'],
    'alibotean': [],
    'bgola': [],
    }


class Factor(dict):
    """
    A score thing.
    """
    def __init__(self, *arg, **kw):
        super(Factor, self).__init__(*arg, **kw)
        self.__dict__ = kw


# All the point types for this leaderboard.
_factors = {}
_nextorder = count().next

def deffactor(score, description):
    """
    Define a new factor with an associated score and textual english
    description.

    Suck it, ubuntu.  Use software in ENGLISH.
    """
    key = (object(), repr(description))
    _factors[key] = Factor(
        order=_nextorder(),
        points=score,
        description=description,
        )
    return key

# You can enter tags (tags.br()) in the description as this is sent to HTML.
BUG_TICKET = deffactor(500, "creating a bug ticket")
DONE_REVIEW = deffactor(200, "complete a review")
NEEDS_REVIEW = deffactor(75, "submitting a ticket for review")
FIXED = deffactor(75, "solving a ticket")
WIKI_EDIT = deffactor(50, "wiki changes")
CREATE_TICKET = deffactor(50, "creating a ticket")
IRC_COMMENT = deffactor(50, "active on IRC in a day")
JUST_CLOSED = deffactor(25, "closing a ticket without solving it")
JUST_COMMENT = deffactor(10, "leaving a comment or updating the description")

# How many points to get for each action from that month.
ACTION_POINTS_RATIO = 0.1


here = FilePath(__file__)


class HiscoresPage(Element):
    loader = XMLFile(here.sibling('static').child('highscores.html').open())

    def __init__(self, dateWithinMonth, scores):
        self.dateWithinMonth = dateWithinMonth
        self.allScores = scores


    def linkTag(self, time, arrowDirection, hidden=False):
        style = LINK_STYLE
        if hidden:
            style += ' visibility: hidden;'
        return tags.a(
            style=style,
            href="?time=%s" % (time.asDatetime().strftime('%Y-%m-%d'),)
        )(
            tags.img(
                border="0",
                src="static/%s-arrow.png" % (arrowDirection,),
                )
        )


    @renderer
    def next(self, request, tag):
        start, end = monthRangeAround(self.dateWithinMonth + timedelta(days=45))
        hidden = False
        if start > Time():
            hidden = True
        return tag(self.linkTag(start, "right", hidden))


    @renderer
    def previous(self, request, tag):
        start, end = monthRangeAround(self.dateWithinMonth - timedelta(hours=1))
        return tag(self.linkTag(start, "left"))


    @renderer
    def scores(self, request, oneRowTag):
        for pos, (score, author) in enumerate(self.allScores):
            pos += 1
            if pos == 1:
                color = 'yellow'
            elif pos == 2:
                color = 'white'
            elif pos == 3:
                color = 'orange'
            else:
                if pos > 10:
                    color = '#555555'
                else:
                    color = '#888888'
            rank = str(pos)
            if (pos % 100) > 10 and (pos % 100) < 20:
                suffix = 'th'
            elif rank[-1] == '1':
                suffix = 'st'
            elif rank[-1] == '2':
                suffix = 'nd'
            elif rank[-1] == '3':
                suffix = 'rd'
            else:
                suffix = 'th'
            yield oneRowTag.clone().fillSlots(
                rank=str(pos) + suffix,
                color=color,
                bang="!" * max(0, 4-pos),
                total=str(score),
                author=author,
                )


    @renderer
    def action_points_ratio(self, request, tag):
        """
        The ration at which you get points for each other action in this
        period.
        """
        return tag(str(ACTION_POINTS_RATIO))

    @renderer
    def total_points(self, request, tag):
        """
        Total points for this period.
        """
        total = 0
        for score, _ in self.allScores:
            total += score
        return tag(str(total))

    @renderer
    def footer(self, request, tag):
        """
        Description of the actions which are scored.
        """
        for factor in sorted(_factors.values(), key=lambda f: f.order):
            tag(str(factor.points), " for ", factor.description, tags.br())
        return tag


def render(output, rangeStart, scores):
    """
    Write some score data to a callable of some kind.

    @param rangeStart: A L{Time} instance giving the beginning of the time range
        containing the given scores.

    @param scores: the scores data structure as returned by getscores.

    @param output: a callable that takes a C{str}; call it repeatedly to write
        the output.
    """
    page = HiscoresPage(rangeStart, scores)
    # Not requesting any asynchronous data, so we can just ignore the result of
    # this Deferred.
    flatten(None, page, output)


def getscores(actions):
    """
    Calculate each author's scores from the given month of actions.
    """
    tiebreaker = count()
    scores = {}
    for (action, author) in actions:
        scores[author] = (
            scores.get(author, 0) +
            _factors[action].points +
            tiebreaker.next() * ACTION_POINTS_RATIO
            )

    result = []
    for author, score in scores.items():
        # The scores are rounded by conversion to `int`.
        result.append((int(score), author))

    return sorted(result, reverse=True)


def parsetime(s):
    y, m, d = map(int, s.split("-"))
    return Time.fromDatetime(datetime(year=y, month=m, day=d))



HOW_LONG_IS_A_MONTH_I_DONT_KNOW = 27


def monthRangeAround(t):
    beginningdt = t.asDatetime().replace(day=1, hour=0, minute=0, second=0,
                                         microsecond=0)
    td = timedelta(days=HOW_LONG_IS_A_MONTH_I_DONT_KNOW)
    while (beginningdt + td).month == beginningdt.month:
        td += timedelta(days=1)
    beginning = Time.fromDatetime(beginningdt)
    end = Time.fromDatetime(beginningdt + td)
    return (beginning, end)


def getTicketChanges(start, end):
    """
    Return the changes made to the tickets.
    """
    con = sqlite3.connect(*CONFIGURATION['trac-db'])
    try:
        cur = con.cursor()
        cur.execute("""
            select ticket, (time / 1000000), author, field, oldvalue, newvalue
            from
                ticket_change
            where
                (time / 1000000) > %s and (time / 1000000) < %s
            order by
                time asc
            """ % (start.asPOSIXTimestamp(), end.asPOSIXTimestamp()))

        return cur.fetchall()
    finally:
        con.close()


def getNewTickets(start, end):
    """
    Return the new tickets.
    """
    con = sqlite3.connect(*CONFIGURATION['trac-db'])
    try:
        cur = con.cursor()
        cur.execute("""
            select type, reporter
            from
                ticket
            where
                (time / 1000000) > %s and (time / 1000000) < %s
            order by
                time asc
            """ % (start.asPOSIXTimestamp(), end.asPOSIXTimestamp()))

        return cur.fetchall()
    finally:
        con.close()


def getOwnser(id):
    """
    Return the current owner for ticket with `id`.
    """
    con = sqlite3.connect(*CONFIGURATION['trac-db'])
    try:
        cur = con.cursor()
        cur.execute('select owner from ticket where id = %s' % (id,))
        result = cur.fetchall()
        owner = result[0][0]
        if not owner:
            owner = UNKNOWN_OWNER
        return owner
    finally:
        con.close()


def _getTicketActions(start, end):
    """
    Compute the actions represented by the given sequence of ticket change.
    """
    changes = getTicketChanges(start, end)

    for time, localChanges in groupby(changes, itemgetter(1)):
        actions = []
        comment = None
        for ticket, time, author, field, oldvalue, newvalue in localChanges:

            author = author.lower()

            if field == 'resolution':
                # Ticket was closed.
                if newvalue == 'fixed':
                    if author == 'pqm':
                        # This is closed by PQM but we track this via the
                        # PQM comment.
                        continue
                    else:
                        # Mark to discover the actual author.
                        actions.append((FIXED, author))
                else:
                    actions.append((JUST_CLOSED, author))

            elif field == 'comment':
                # An action was done to the ticket.
                comment = newvalue

                if author == 'pqm':
                    if comment.startswith('Branch landed on master.'):
                        # The informative comment from PQM that the
                        # ticket was closed.
                        # We get the owner from the ticket owner.
                        author = getOwnser(ticket)
                    else:
                        # Action done in GitHub. Author is the first word.
                        author = comment.split(' ', 1)[0]

                if 'needs-review' in comment:
                    actions.append((NEEDS_REVIEW, author))
                elif 'needs-changes' in comment:
                    actions.append((DONE_REVIEW, author))
                elif 'changes-approved' in comment:
                    actions.append((DONE_REVIEW, author))
                elif 'Branch landed on master' in comment:
                    actions.append((FIXED, author))
                else:
                    actions.append((JUST_COMMENT, author))

            elif field == 'description':
                actions.append((JUST_COMMENT, author))

        for (action, author) in actions:

            if author in IGNORED_AUTHORS:
                continue

            yield (action, author)


    changes = getNewTickets(start, end)
    for ticket_type, reporter in changes:
        author = reporter.lower().strip()
        if ticket_type == 'bug':
            action = BUG_TICKET
        else:
            action = CREATE_TICKET
        yield (action, author)


def getWikiChanges(start, end):
    """
    Return the SQL for wiki changes.
    """
    con = sqlite3.connect(*CONFIGURATION['trac-db'])
    try:
        cur = con.cursor()
        cur.execute("""
            select author
            from
                wiki
            where
                (time / 1000000) > %s and (time / 1000000) < %s
            order by
                time asc
            """ % (start.asPOSIXTimestamp(), end.asPOSIXTimestamp()))

        return cur.fetchall()
    finally:
        con.close()


def _getWikiActions(start, end):
    """
    Compute the actions represented by the given sequence of ticket change.
    """
    changes = getWikiChanges(start, end)

    for change in changes:
        author = change[0]
        yield (WIKI_EDIT, author.strip().lower())


def _getIRCActions(start):
    """
    Compute the actions based on the IRC activity for a month.
    """
    target_month = start.asDatetime().strftime('%Y-%m-%B')
    month_path = os.path.join(CONFIGURATION['irc-logs'], target_month)
    for (root, dirnames, filenames) in os.walk(month_path):
        for day in filenames:
            for action in _getIRCActionsForDay(os.path.join(root,day)):
                yield action


def _getIRCActionsForDay(day_path):
    """

    2017-05-10T12:31:40  -GitHub54- salt-master/master 6a3c7d1 Mișu Moldovan: [#4050] Normalize links on pypi site.
    """
    day_comments = {}

    def update_day_comments(author):
        if not author:
            return
        previous = day_comments.get(author, 0)
        day_comments[author] = previous + 1

    with open(day_path) as day_file:
        for line in day_file:
            if '  *** ' in line:
                # Just a meta line.
                continue
            elif '  -GitHub' in line:
                # A GitHub hook
                action = _getIRCGitHubAction(line)
                if action:
                    yield action
            else:
                # Maybe is a comment from a team member.
                author = _getIRCCommentAuthor(line)
                update_day_comments(author)

    for author, count in day_comments.items():
        if count > 4:
            yield (IRC_COMMENT, author)

def _getIRCGitHubAction(line):
    """
    """
    return None


def _getIRCCommentAuthor(line):
    """
    Return the author for `line`.
    """
    try:
        author = line.split('>', 1)[0].split('<', 1)[1]
    except IndexError:
        return None

    return _resolveAuthor(author)


def _resolveAuthor(alias):
    """
    Return the well know author from the alias.
    """
    for global_author, aliases in AUTHOR_ALIASES.items():
        if alias in aliases:
            return global_author

    # No alias found.
    return alias


def computeActions(start, end):
    """
    Return all the actions for the time period.
    """
    return chain(
        _getTicketActions(start, end),
        _getWikiActions(start, end),
        _getIRCActions(start),
        )


def renderPage(time, output):
    """
    Called to render the page from start to end and send results to the
    `output` write function.

    This should be the only public method.
    """
    start, end = monthRangeAround(time)
    actions = computeActions(start, end)
    scores = getscores(actions)
    render(output, start, scores)


if __name__ == '__main__':
    """
    Show debugging info for current month.
    """
    import pprint, sys
    CONFIGURATION['trac-db'] = (sys.argv[1],)
    CONFIGURATION['irc-logs'] = sys.argv[2]
    start, end = monthRangeAround(Time())
    actions = list(computeActions(start, end))
    pprint.pprint(actions)
    pprint.pprint(getscores(actions))

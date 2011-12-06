import os
import re
import signal
from subprocess import Popen, PIPE

import sublime
import sublime_plugin

try:
    from local_settings import CHECKER, CHECKER_ARGS
except ImportError as e:
    print """
Please create file local_settings.py in the same directory with
jslint_checker.py. Add to jslint_settings.py list of your checkers.

Example:

CHECKER = 'java -jar /Users/gabonsky/Bin/jslint4java-2.0.0.jar'.split()
CHECKER_ARGS = '--browser --predef jQuery,$,Backbone,_'.split()

"""
    raise e


global view_messages
view_messages = {}


class JSLintCheckerCommand(sublime_plugin.EventListener):
    def on_activated(self, view):
        signal.signal(signal.SIGALRM, lambda s, f: check_and_mark(view))
        signal.alarm(1)

    def on_deactivated(self, view):
        signal.alarm(0)

    def on_post_save(self, view):
        check_and_mark(view)

    def on_selection_modified(self, view):
        global view_messages
        lineno = view.rowcol(view.sel()[0].end())[0]
        if view.id() in view_messages and lineno in view_messages[view.id()]:
            view.set_status('jslint_checker', view_messages[view.id()][lineno])
        else:
            view.erase_status('jslint_checker')


def check_and_mark(view):
    if not 'javascript' in view.settings().get('syntax').lower():
        return

    messages = []

    base_name = " > %s" % os.path.basename(view.file_name())

    # build args
    ARGS = []
    ARGS.extend(CHECKER)
    ARGS.extend(CHECKER_ARGS)
    ARGS.extend([view.file_name()])

    p = Popen(
        ARGS,
        stdout=PIPE,
        stderr=PIPE
    )
    stdout, stderr = p.communicate(None)
    title = "\n# JsLINT errors/warnings"

    if stdout:
        print title
        print stdout.replace(view.file_name(), base_name)

    if stderr:
        print title
        print stdout.replace(view.file_name(), base_name)

    messages += parse_messages(stdout)
    messages += parse_messages(stderr)

    outlines = [view.full_line(view.text_point(m['lineno'], 0)) \
                for m in messages]
    view.erase_regions('jslint_checker_outlines')
    view.add_regions('jslint_checker_outlines',
        outlines,
        'keyword',
        sublime.DRAW_EMPTY | sublime.DRAW_OUTLINED)

    underlines = []
    for m in messages:
        if m['col']:
            a = view.text_point(m['lineno'], m['col'])
            underlines.append(sublime.Region(a, a))

    view.erase_regions('jslint_checker_underlines')
    view.add_regions('jslint_checker_underlines',
        underlines,
        'keyword',
        sublime.DRAW_EMPTY_AS_OVERWRITE | sublime.DRAW_OUTLINED)

    line_messages = {}
    for m in (m for m in messages if m['text']):
        if m['lineno'] in line_messages:
            line_messages[m['lineno']] += ';' + m['text']
        else:
            line_messages[m['lineno']] = m['text']

    global view_messages
    view_messages[view.id()] = line_messages


def parse_messages(checker_output):
    """
    Parse messages from JsLint
    """
    lint = re.compile(r'.*:(\d+):(\d+):(.*)')

    messages = []
    for i, line in enumerate(checker_output.splitlines()):
        if lint.match(line):
            lineno, col, text = lint.match(line).groups()
        else:
            continue
        messages.append({'lineno': int(lineno) - 1,
                         'col': int(col) - 1,
                         'text': text})

    return messages

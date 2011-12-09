import os
import re
import signal
from subprocess import Popen, PIPE

import sublime
import sublime_plugin

import thread

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


class JslintCommand(sublime_plugin.EventListener):
    # global scope for messages for all of the views
    def __init__(self, *args, **kwargs):
        self.view_messages = {}
        self.line_messages = {}
        self.views = {}

        self.statuses = {}
        self.watching = False

        super(JslintCommand, self).__init__(*args, **kwargs)

    def on_activated(self, view):
        """
        Execute same handle as on saving of the file
        to display JsLint errors or warnings
        """
        self.on_post_save(view)

    def on_deactivated(self, view):
        signal.alarm(0)

    def on_post_save(self, view):
        """
        Starting execution of JS Lint check in background
        """

        if view.id() in self.statuses:
            return

        self.views[view.id()] = view

        if not 'javascript' in view.settings().get('syntax').lower():
            return

        self.statuses[view.id()] = True
        thread.start_new_thread(jslint_checker, (
                view.id(),
                view.file_name(),
                self
            )
        )

        view.set_status(
            'jslint_checker',
            "JsLint Checking started..."
        )

        if not self.watching:
            sublime.set_timeout(self.handle_thread, 500)

    def on_selection_modified(self, view):
        """
        Update status with JsLint message for current line
        if it's available
        """
        lineno = view.rowcol(view.sel()[0].end())[0]

        if view.id() in self.line_messages and \
            lineno in self.line_messages[view.id()]:
            view.set_status(
                'jslint_checker',
                "JsLint: %s" % self.line_messages[view.id()][lineno]
            )
        else:
            view.erase_status('jslint_checker')

    def handle_thread(self):
        """
        Handle executed threads and update status
        of the all executed checks
        """
        self.watching = True

        candidates = []
        for id, status in self.statuses.iteritems():
            if not status:
                self.render_lints(id)
                candidates.append(id)

        self.statuses = dict([(key, val) \
                                for key, val in self.statuses.iteritems() \
                                    if key not in candidates])

        if len(self.statuses) == 0:
            self.watching = False
            return

        sublime.set_timeout(self.handle_thread, 500)

    def render_lints(self, id):
        """
        Post-execution method to hilight lint messages
        and display 'finished' status of check in status bar
        """
        print "Rendering Regions..."

        view = self.views[id]
        outlines = [view.full_line(view.text_point(m['lineno'], 0)) \
                        for m in self.view_messages[id]]

        view.erase_regions('jslint_checker_outlines')
        view.add_regions('jslint_checker_outlines',
                     outlines,
                     'keyword',
                     sublime.DRAW_EMPTY | sublime.DRAW_OUTLINED)

        underlines = []
        for m in self.view_messages[id]:
            if m['col']:
                a = view.text_point(m['lineno'], m['col'])
                underlines.append(sublime.Region(a, a))

        view.erase_regions('jslint_checker_underlines')
        view.add_regions('jslint_checker_underlines',
                     underlines,
                     'keyword',
                     sublime.DRAW_EMPTY_AS_OVERWRITE | sublime.DRAW_OUTLINED)
        view.set_status(
            'jslint_checker',
            "JsLint Checking of '%s' finished..." % view.file_name()
        )


def jslint_checker(id, file_name, command):
    """
    Function to execute and parse JsLint messages
    via externally executed tool
    """

    messages = []
    base_name = " > %s" % os.path.basename(file_name)

    # build args
    ARGS = []
    ARGS.extend(CHECKER)
    ARGS.extend(CHECKER_ARGS)
    ARGS.extend([file_name])

    p = Popen(
        ARGS,
        stdout=PIPE,
        stderr=PIPE
    )

    stdout, stderr = p.communicate(None)
    title = "\n# JsLINT errors/warnings for %s" % file_name

    if stdout:
        print title
        print stdout.replace(file_name, base_name)

    if stderr:
        print title
        print stdout.replace(file_name, base_name)

    messages = parse_messages(stdout)
    messages.extend(parse_messages(stderr))

    line_messages = {}
    for m in (m for m in messages if m['text']):
        if m['lineno'] in line_messages:
            line_messages[m['lineno']] += ';' + m['text']
        else:
            line_messages[m['lineno']] = m['text']

    # update line messages
    command.view_messages[id] = messages
    command.line_messages[id] = line_messages
    command.statuses[id] = False


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

        messages.append({
            'lineno': int(lineno) - 1,
            'col': int(col) - 1,
            'text': text
        })

    return messages

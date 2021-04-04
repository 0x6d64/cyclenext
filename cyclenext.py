#!/usr/bin/env python3

import os
import time
import platform
from subprocess import call
import sys

config = dict()


def create_config_dict(config_to_modify):
    config_to_modify.update(
        {
            "taskdir": os.path.join(os.path.expanduser("~/.task")),
            "taskcommand": "/usr/bin/task",
            "default_limit": "page",
            "get_lazy_after_secs": 3 * 60,
            "force_redraw_secs_default": 10,
            "loop_delay_secs_default": 0.33,
            "platform_is_windows": platform.system() == "Windows",
            "debug": False
        }
    )


class TaskwarriorFiles(object):
    def __init__(self):
        self._relevant_paths = None
        self.backlog_file = os.path.join(config.get("taskdir"), "backlog.data")

    @property
    def relevant_paths(self):
        if not self._relevant_paths:
            self._relevant_paths = self._get_relevant_paths()
        return self._relevant_paths

    @property
    def unsynced_changes(self):
        backlog_count = None
        if os.path.isfile(self.backlog_file):
            with open(self.backlog_file, "r") as fp:
                content = fp.readlines()
            backlog_count = len(content) - 1
            assert backlog_count >= 0
        return backlog_count

    @staticmethod
    def _get_relevant_paths():
        filenames_to_watch = [  # these should be enough to get all operations including sync of remote tasks
            "undo.data",
            "backlog.data"
        ]
        taskdir = config.get("taskdir")
        relevant_paths_candidates = [os.path.join(taskdir, item) for item in filenames_to_watch]
        relevant_paths_existing = [item for item in relevant_paths_candidates if os.path.isfile(item)]
        return relevant_paths_existing

    @staticmethod
    def _get_file_age_secs(filename):
        """get file age for one file"""
        t_mod = os.path.getmtime(filename)
        seconds_since = time.time() - t_mod
        return seconds_since

    def get_minimal_age_secs(self):
        """get minimal age of list of files"""
        ages = [self._get_file_age_secs(filename) for filename in self.relevant_paths]
        return min(ages)


def redraw(task_filter=None, seconds_since_change=None, unsynced_count=None):
    """draw a new task list"""
    minutes_ago = seconds_since_change / 60

    filter_message = "filter: {}".format(" ".join(task_filter))
    if minutes_ago < 60:
        last_changed_message = " - last change %1.0f minutes ago" % minutes_ago
    elif minutes_ago < (24 * 60):
        last_changed_message = " - last change %1.1f hours ago" % (minutes_ago / 60)
    else:
        last_changed_message = " - last change %1.1f days ago" % (minutes_ago / (24 * 60))
    backlog_message = " - {} unsynced items".format(unsynced_count) if unsynced_count else ""

    # print the whole thing
    clear_terminal()
    print(filter_message + last_changed_message + backlog_message)
    call(_get_call_args(task_filter))


def _get_call_args(task_filter):
    call_args = [config.get("taskcommand")]
    call_args.extend(task_filter)
    call_args.append("rc.gc=off")
    call_args.append("rc.reserved.lines=2")
    if not config.get("debug"):
        call_args.append("rc.verbose=nothing")

    limit_requested_in_user_filter = any("limit:" in x for x in task_filter)
    if not limit_requested_in_user_filter:
        limitstring = "limit:{}".format(config.get("default_limit"))
        call_args.append(limitstring)

    return call_args


def clear_terminal():
    clear_command = 'cls' if config.get("platform_is_windows") else "clear"
    os.system(clear_command)


def run_main():
    create_config_dict(config)
    data_files = TaskwarriorFiles()

    time_since_redraw = 0.0
    terminal_size_old = (0, 0)
    filter_given = len(sys.argv) > 1
    if filter_given:
        taskw_filter = sys.argv[1:]
    else:
        taskw_filter = ["ready"]

    try:
        while True:
            terminal_size = os.popen('stty size', 'r').read().split()
            file_age_seconds = data_files.get_minimal_age_secs()
            lazy_factor = 5 if (file_age_seconds > config.get("get_lazy_after_secs")) else 1
            force_redraw_secs = config.get("force_redraw_secs_default") * lazy_factor
            loop_delay_seconds = config.get("loop_delay_secs_default") * lazy_factor

            terminal_size_did_change = (terminal_size != terminal_size_old)
            force_redraw = (time_since_redraw > force_redraw_secs)
            file_changed = (file_age_seconds < (loop_delay_seconds * 1.8))

            if terminal_size_did_change or force_redraw or file_changed:
                redraw(task_filter=taskw_filter, seconds_since_change=file_age_seconds,
                       unsynced_count=data_files.unsynced_changes)
                time_since_redraw = 0
                time.sleep(loop_delay_seconds)

            time.sleep(loop_delay_seconds)
            time_since_redraw += loop_delay_seconds
            terminal_size_old = terminal_size
    except KeyboardInterrupt:
        print("   bye!")
    pass


if __name__ == '__main__':
    run_main()

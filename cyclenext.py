#!/usr/bin/python

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
            "get_lazy_after_secs": 3 * 60,
            "force_redraw_secs_default": 10,
            "loop_delay_secs_default": 0.33,
            "platform_is_windows": platform.system() == "Windows",
            "debug": False
        }
    )


def redraw(limit, filter, seconds_since_change):
    """draw a new task list"""
    limitstring = "limit:{limit}".format(limit=limit)
    minutes_ago = seconds_since_change / 60
    unsynced_changes = get_sync_backlog_count()

    if minutes_ago < 60:
        last_changed_message = "last change %1.0f minutes ago" % minutes_ago
    elif minutes_ago < (24 * 60):
        last_changed_message = "last change %1.1f hours ago" % (minutes_ago / 60)
    else:
        last_changed_message = "last change %1.1f days ago" % (minutes_ago / (24 * 60))
    backlog_message = " - {} unsynced items".format(unsynced_changes) if unsynced_changes else ""

    # print the whole thing
    clear_terminal()
    print(last_changed_message + backlog_message)
    call(_get_call_args(filter, limitstring))


def _get_call_args(filter, limitstring):
    call_args = [config.get("taskcommand")]
    call_args.extend(filter)
    call_args.append("rc.gc=off")
    call_args.append("rc.reserved.lines=2")
    if not config.get("debug"):
        call_args.append("rc.verbose=nothing")

    custom_limit_in_user_filter = any("limit:" in x for x in filter)
    if not custom_limit_in_user_filter:
        call_args.append(limitstring)

    return call_args


def get_file_age_secs(filename):
    """get file age for one file"""
    t_mod = os.path.getmtime(filename)
    seconds_since = time.time() - t_mod
    return seconds_since


def get_minimal_age_secs(path_list):
    """get minimal age of list of files"""
    ages = [get_file_age_secs(filename) for filename in path_list]
    return min(ages)


def clear_terminal():
    clear_command = 'cls' if config.get("platform_is_windows") else "clear"
    os.system(clear_command)


def calc_terminal_size_limit(termsize):
    """
    calculates the number of lines to display based on available lines and columns in terminal
    a narrow terminal can support only a few lines due to the description being wrapped
    all values here are determined by experience

    :param termsize:
    :return:
    """
    terminal_lines = int(termsize[0])
    terminal_columns = int(termsize[1])
    if terminal_columns > 90:
        factor = 0.6
    elif terminal_columns > 65:
        factor = 0.4
    else:
        factor = 0.2
    limit = int(terminal_lines * factor)
    return limit if limit > 0 else 1


def get_relevant_paths():
    filenames_to_watch = [  # these should be enough to get all operations including sync of remote tasks
        "undo.data",
        "backlog.data"
    ]
    taskdir = config.get("taskdir")
    relevant_paths_candidates = [os.path.join(taskdir, item) for item in filenames_to_watch]
    relevant_paths_existing = [item for item in relevant_paths_candidates if os.path.isfile(item)]
    return relevant_paths_existing


def get_sync_backlog_count():
    backlog_file = os.path.join(config.get("taskdir"), "backlog.data")
    backlog_count = None
    if os.path.isfile(backlog_file):
        with open(backlog_file, "r") as fp:
            content = fp.readlines()
        backlog_count = len(content) - 1
        assert backlog_count >= 0
    return backlog_count


def run_main():
    create_config_dict(config)

    path_list = get_relevant_paths()
    time_since_redraw = 0.0
    terminal_size_old = (0, 0)
    filter_given = len(sys.argv) > 1
    if filter_given:
        taskw_filter = sys.argv[1:]
    else:
        taskw_filter = "ready"

    try:
        while True:
            terminal_size = os.popen('stty size', 'r').read().split()
            file_age_seconds = get_minimal_age_secs(path_list)
            lazy_factor = 5 if (file_age_seconds > config.get("get_lazy_after_secs")) else 1
            force_redraw_secs = config.get("force_redraw_secs_default") * lazy_factor
            loop_delay_seconds = config.get("loop_delay_secs_default") * lazy_factor

            terminal_size_did_change = (terminal_size != terminal_size_old)
            force_redraw = (time_since_redraw > force_redraw_secs)
            file_changed = (file_age_seconds < (loop_delay_seconds * 1.8))

            if terminal_size_did_change or force_redraw or file_changed:
                redraw(calc_terminal_size_limit(terminal_size), taskw_filter, file_age_seconds)
                #             print('\a') # terminal bell for debug
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

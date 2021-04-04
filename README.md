# cyclenext.py

A helper script that I wrote for usage with [taskwarrior](https://taskwarrior.org) as a helper that
shows the tasks on the ``next`` report (hence the name). 

## Usage
Call with any filter as you would run taskwarrior. Press \<Ctrl\>+\<C\> to quit.

## Features
- detect changes in terminal size to redraw
- detect when no changes are made in quite some time and then redraw less frequently

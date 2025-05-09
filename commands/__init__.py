import glob, importlib, versions

_submodules = []
for i in glob.glob("commands/*.py"):
    if (i == "commands/__init__.py") or (i == "commands/framework.py") or (i == "commands\\__init__.py") or (i == "commands\\framework.py"): continue
    _submodules.append(importlib.import_module("commands." + i[9:-3]))

# This folder is used to define the commands used by Nihonium.
# Editing this file directly is not recommended.

__version__ = versions.Version(2, 2, 0)     # This defines the version of the module's framework.

nihonium_minver = versions.Version(0)
alt_minvers = {}
commands = {}
ex_commands = {}
do_last = []
do_first = []
for j in _submodules:
    commands.update(j.commandlist)
    do_last.extend(j.do_last)
    do_first.extend(j.do_first)
    if j.nihonium_minver > nihonium_minver: nihonium_minver = j.nihonium_minver
    for k in j.ex_commandlist:
        try: ex_commands[k].update(j.ex_commandlist[k])
        except KeyError:
            ex_commands[k] = {}
            ex_commands[k].update(j.ex_commandlist[k])
    for k in j.alt_minvers:
        try: alt_minvers[k] = j.alt_minvers[k]
        except KeyError:
            alt_minvers[k] = {}
            alt_minvers[k] = j.alt_minvers[k]

"""
A command framework designed for Roentgenium.
"""
# The nuclear terminology joke persists by tradition. =)
# Now we only need something called "photon" to make it complete.

from dataclasses import dataclass
from collections.abc import Mapping, Callable
from datetime import datetime
from inspect import signature, Parameter
import re

import versions


@dataclass
class Context:
    """Context for the command call. Data such as bot version, topic ID and tags are stored here."""

    uptime: datetime
    "The time that this bot is started."
    tid: int
    "ID number of the calling message's topic."
    uid: int
    "ID number of the calling message's user."
    user_name: str
    "Name of the calling message's user."
    types: list[str]
    "Category of the calling message's topic."
    config: dict
    "Configuration of this bot."
    topic_store: Mapping
    "Topic-local persistent data storage."
    user_store: Mapping
    "User-local persistent data storage."
    version: versions.Version
    "Version of the bot."
    bot_id: str
    "Internal ID name of the bot."
    statistics: dict
    "Statistics of the bot's actions."


@dataclass
class Command(Callable):
    """A Gluon command. (The Gluon name is to distinguish it with legacy commands.)

    Commands may have their documentation stored in the docstring, formatted in `reStructuredText`_.
    They will be converted into BBC for the TBGs.

    Supported reStructuredText markups are:
    * emphasis and boldface
    * some fields (param and type)

    .. _reStructuredText: https://docutils.sourceforge.io/rst.html
    """

    function: Callable
    "What this command does."
    short_help: str = None
    "A terse description of the command. If ``None``, the first line is used instead."
    expect: Callable[(Context,), bool] = lambda ctx: True
    "Requirements of this command."

    def __post_init__(self):
        self.name = self.function.__name__

        # Convert reST markups to BBC markups.
        docstring = self.function.__doc__
        docstring = re.sub(r"(?<![0-9A-Za-z])\*\*(\S.*?\S?)\*\*(?![0-9A-Za-z])", r"[b]\1[/b]", docstring)
        docstring = re.sub(r"(?<![0-9A-Za-z])\*(\S.*?\S?)\*(?![0-9A-Za-z])", r"[i]\1[/i]", docstring)
        fields = re.findall(r":(\S+)(?: (\S.*?)?)?(?<!\\):(?: +(.+))?\n?", docstring)
        docstring = re.sub(r":(\S+)(?: (\S.*?)?)?(?<!\\):(?: +(.+))?\n?", "", docstring)
        docstring = docstring.strip()
        self.long_help = docstring
        if self.short_help is None:
            self.short_help = docstring.splitlines()[0]

        # Parse the fields on the docstring.
        self.param_descs = {}
        self.param_types = {}
        for field_name, field_args, field_body in fields:
            if field_name == "param":
                # We support the :param: shorthand which also lists the parameter type.
                *type_, name = re.split(r"\s+", field_args)
                if len(type_) == 1:
                    self.param_types[name] = type_[0]
                self.param_descs[name] = field_body
            elif field_name == "type":
                self.param_types[field_args] = field_body

        sig = signature(self.function)
        self.param_defaults = {name: param.default for name, param in sig.parameters.items() if name != "ctx"}

    def get_help(self, concise=False):
        """Returns the help string of this command in BBC from the function's docstring."""
        docstring = self.short_help if concise else self.long_help

        if not concise and len(self.param_descs) > 0:
            docstring += "\n\n[b]Arguments:[/b]\n"
            docstring += "[list]\n"
            for name, desc in self.param_descs.items():
                item = name
                parenthesis = []
                if name in self.param_types:
                    parenthesis.append(str(self.param_types[name]))
                if name in self.param_defaults and self.param_defaults[name] != Parameter.empty:
                    if self.param_defaults[name] is None:
                        parenthesis.append("optional")
                    else:
                        parenthesis.append(f"default {self.param_defaults[name]}")
                if parenthesis != []:
                    item += f" ({', '.join(parenthesis)})"
                item += f": {desc}"
                docstring += f"[li]{item}[/li]"
            docstring += "\n[/list]"

        return docstring

    def get_args(self, concise=False):
        """Returns the formatted arguments of this command."""
        command_argv = []
        if concise:
            command_argv.extend(
                arg
                for arg in self.param_defaults.keys()
            )
        else:
            command_argv.extend(
                arg
                + (f":{self.param_types[arg]}" if arg in self.param_types else "")
                + (
                    "" if self.param_defaults[arg] == Parameter.empty
                    else "?" if self.param_defaults[arg] is None
                    else f"={self.param_defaults[arg]}"
                )
                for arg in self.param_defaults.keys()
            )
        return " ".join(command_argv)

    def run(self, event, *args):
        """Execute the command."""
        return self.function(event, *args)

    __call__ = run


commands: dict[Command] = {}


def add_command(*, short_help: str | None = None, expect: Callable[(Context,), bool] = lambda ctx: True):
    """Add this function to the list of commands.

    :param short_help: A terse description of the command. If ``None``, the first line is used instead.
    :param expect: A callable determining the conditions of this command that must be met in order to be considered compatible.
    """
    def adder(func):
        command = Command(func, short_help, expect)
        name = func.__name__
        commands[name] = command
        return command
    return adder


def alias(*names):
    """Assign aliases of this command.

    .. code-block: python

        @alias("bar", "baz")
        @add_command()
        def foo(ctx, arg):
            ...
    """
    def adder(cmd):
        if not isinstance(cmd, Command):
            raise ValueError("not a Command")
        for name in names:
            commands[name] = cmd
        return cmd
    return adder

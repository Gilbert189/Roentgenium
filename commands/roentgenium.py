from . import gluon  # This import is required.

# Your commands may import more modules.
import random
import math
from collections import defaultdict


# Commands in here are adapted from Nihonium's commands/nihonium.py
# TODO: a more helpful guide


@gluon.add_command()
def coin(ctx):
    """Flips a coin and gives you the result."""
    return "You flip a coin, and get " + random.choice(["heads", "tails"]) + "."


@gluon.add_command()
def dice(ctx, num=1, sides=6):
    """Rolls *num* *sides*-sided dice, and gives you the result.

    :param int num: The number of dice.
    :param sides: The number of sides on the die.
    :type sides: int"""
    num = int(float(num))
    sides = int(float(sides))

    only_summary = False
    if num < 0:
        return "\N{CROSS MARK} You can't roll negative dice."
    elif num == 0:
        return "\N{CROSS MARK} You roll no dice, and get nothing."
    elif sides < 0:
        return "\N{CROSS MARK} You can't roll something that doesn't exist."
    elif sides == 0:
        return f"\N{LEAF FLUTTERING IN WIND} You roll {num} pieces of air, and get air."
    elif num * sides >= 1_000_000_000:
        return "\N{COLLISION SYMBOL} That's [i]way[/i] too many for me to roll."  # avoid MemoryError
    elif num > math.floor(5000 // math.log(sides)):
        only_summary = True

    rolls = []
    for _ in range(num):
        rolls.append(random.randint(1, sides))

    if num >= 1:
        summary = f"(Total: {sum(rolls)}, Min: {min(rolls)}, Max: {max(rolls)})"
    else:
        summary = ""
    if only_summary:
        return f"\N{GAME DIE} You roll {num}d{sides}, and get: [i]{summary}[/i]"
    else:
        return f"\N{GAME DIE} You roll {num}d{sides}, and get: [code]{', '.join(map(str, rolls))}[/code] [i]{summary}[/i]"


@gluon.alias("newHelp")
@gluon.add_command()
def help2(ctx, command=None):
    """Provides documentation of all supported commands.

    :param command: The specific command to get help for."""
    BOT_NAME = ctx.config['bot']['auth']['username']
    if command is None:
        unique_cmd_names = defaultdict(list)
        unique_cmd_docs = {}
        unique_cmd_args = {}
        for name, command in gluon.commands.items():
            unique_cmd_names[id(command)].append(name)
            unique_cmd_docs[id(command)] = command.get_help(concise=True)
            unique_cmd_args[id(command)] = command.get_args(concise=False)

        result = "[size=3][b]Commands:[/b][/size]"
        for cmd_id in unique_cmd_names:
            if len(unique_cmd_names[cmd_id]) == 1:
                cmd_name = unique_cmd_names[cmd_id][0]
            else:
                cmd_name = "{%s}" % "|".join(unique_cmd_names[cmd_id])
            cmd_docs = unique_cmd_docs[cmd_id]
            cmd_args = unique_cmd_args[cmd_id]
            result += f"[quote][b]@{BOT_NAME} {cmd_name} {cmd_args}[/b]\n{cmd_docs}[/quote]"
        result += "Arguments are in the form \"name:type=default\". ? means it's optional."
        return result
    elif command not in gluon.commands:
        return f"Unknown command. Maybe try \"@{BOT_NAME} help\" instead?"
    else:
        command = gluon.commands[command]
        cmd_docs = command.get_help(concise=False)
        cmd_args = command.get_args(concise=True)
        return f"[size=3][b]@{BOT_NAME} {command} {cmd_args}[/b][/size]\n{cmd_docs}"

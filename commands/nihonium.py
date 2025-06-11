import versions
from . import framework as fw  # These imports are required. (The "as fw" is not required, and is only here to shorten lines.)
import random, math, datetime  # These imports are dependent on what your commands need.

# This file can be used as an example of a command file.

version = versions.Version(2, 0, 0)  # This defines the version of the user-added commands.
nihonium_minver = versions.Version(0, 15, 0)  # This defines the minimum version of Nihonium needed to run these commands.
alt_minvers = {"nihonium2": versions.Version(0, 13, 0)}  # Used to define minimum versions for other bots. Format: {"<id>": versions.Version(<version>)}

# Commands can take any number of placement arguments and should return a string containing the output of the command.
# (Beginning/trailing newline not required.)
# Commands can take inputs that are Integers, Floats, Strings, and Booleans.
# If a command raises TypeError, ValueError, KeyError, IndexError, OverflowError, or ZeroDivisionError, it will be caught by Nihonium.
# Other errors will not be caught.
# The first argument a command recieves will contain information about the bot.
# The second argument a command recieves will contain information about the thread the command was called in.
# The third argument a command recieves will contain information about the user who called the command.

# The functions below are executed when certain commands are called:


def coin(bot_data, thread_data, user_data):
    return "You flip a coin, and get " + random.choice(["heads", "tails"]) + "."


def coin2(bot_data, thread_data, user_data):
    return "You flip a coin 2, and get " + random.choice(["heads 2", "tails 2"]) + "."


def dice(bot_data, thread_data, user_data, num=1, size=20):
    num = int(float(num))
    size = int(float(size))
    hold = []
    doSanity = False  # sanity check, prevent the post from getting too long
    if (num < 0): return "You can't roll negative dice."
    elif (num == 0): return "You roll no dice, and get nothing."
    elif (size < 0): return "You can't roll something that doesn't exist."
    elif (size == 0): return "You roll " + str(num) + " pieces of air, and get air."
    elif (num*size >= 1000000000): return "That's [i]way[/i] too many for me to roll."  # avoid MemoryError
    elif (num > math.floor(5000/math.floor(math.log(size)))): doSanity = True
    for _ in range(num):
        hold.append(random.randint(1, size))
    if doSanity: return "You roll " + str(num) + "d" + str(size) + ", and get: [i]" + str(sum(hold)) + "[/i]"
    else: return "You roll " + str(num) + "d" + str(size) + ", and get: [code]" + str(hold)[1:-1] + "[/code] (Total: [i]" + str(sum(hold)) + "[/i])"


def bot(bot_data, thread_data, user_data):
    output = "Bot Statistics:"
    output += "[table]"
    output += f"\n[tr][td]Nihonium Version:  [/td][td]{bot_data['version']}[/td][/tr]"
    output += f"\n[tr][td]Fork Version:  [/td][td]{bot_data['forkversion']}[/td][/tr]"
    output += f"\n[tr][td]Uptime:  [/td][td]{datetime.datetime.now() - bot_data['uptime']}[/td][/tr]"
    output += f"\n[tr][td]Parse Cycles:  [/td][td]{bot_data['data']['parse_cycles']}[/td][/tr]"
    output += f"\n[tr][td]Commands Found:  [/td][td]{bot_data['data']['commands_found']}[/td][/tr]"
    output += f"\n[tr][td]Commands Parsed:  [/td][td]{bot_data['data']['commands_parsed']}[/td][/tr]"
    output += f"\n[tr][td]Valid Commands:  [/td][td]{bot_data['data']['valid_commands']}[/td][/tr]"
    output += f"\n[tr][td]Alerts Received:  [/td][td]{bot_data['data']['alerts_received']}[/td][/tr]"
    output += "[/table]"
    return output


def _help(bot_data, thread_data, user_data):
    output = "Commands:"
    output += "\n[quote]  nh!coin\n    Flips a coin and gives you the result.[/quote]"
    output += "\n[quote]  nh!{dice|roll} num;int;1 sides;int;20\n    Rolls [i]num[/i] [i]sides[/i]-sided dice, and gives you the result.[/quote]"
    output += "\n[quote]  nh!bot\n    Returns various statistics about the bot.[/quote]"
    output += "\n[quote]  nh!help\n    Returns this help message.[/quote]"
    output += "\n[quote]  nh!suggest suggestion;str;allows_spaces\n    Make a suggestion.[/quote]"
    output += "\n[quote]  nh!threadInfo\n    Get information about the current thread.[/quote]"
    output += "\n[quote]  nh!text command;str;no_spaces;'read' filename;str;no_spaces;'_' other;varies\n    Text file modificaton.[/quote]"
    output += "\n[quote]  nh!{file|files} command;str;no_spaces;'read' filename;str;no_spaces;'_.txt' other;varies\n    File modificaton.[/quote]"
    output += "\n[quote]  nh!estimate tID;int;<current_thread>\n    Estimates when a thread will be completed.[/quote]"
    output += "\n[quote]  nh!choose options;multi_str;no_spaces\n    Picks one of the given options.[/quote]"
    output += "\n[quote]  nh!estimate action;str;no_spaces;'roll'\n    Used for [topic=5893]TGOHNRADFYASWH[/topic].[/quote]"
    output += "\nArguments are in the form \"name;type;spaces;default\". Arguments with no default are required, [i]spaces[/i] is only present for strings."
    output += "\nFor more information (updated quicker), visit [url=https://realicraft.github.io/Nihonium/index.html]the webpage[/url]."
    output += "\n(Note: I plan on adding a system to auto-generate the results of this command. It hasn't been added yet, though.)"
    return output


def suggest(bot_data, thread_data, user_data, *suggestion):
    if (len(suggestion) == 0): return "Your empty space has been recorded."
    suggestion_full = " ".join(suggestion)
    with open("suggestions.txt", "a", encoding="utf-8") as suggestFile:
        suggestFile.write(suggestion_full + "\n")
    return "Your suggestion has been recorded."


def threadInfo(bot_data, thread_data, user_data):
    first_post_date = thread_data["store"]["first_post_date"]
    today_date = datetime.datetime.now().astimezone()
    diff = today_date - first_post_date
    ppd = thread_data["store"]["recent_post"] / (diff.days + (diff.seconds / 86400))
    output = "Thread Info:"
    output += "[table]"
    output += f"\n[tr][td]Name:  [/td][td]{thread_data['store']['name']}[/td][/tr]"
    output += f"\n[tr][td]ID:  [/td][td]{thread_data['thread_id']}[/td][/tr]"
    output += f"\n[tr][td]Types:  [/td][td]{thread_data.get('types', [])}[/td][/tr]"
    output += f"\n[tr][td]Date:  [/td][td]{first_post_date:%b %d, %Y %I:%M:%S %p}[/td][/tr]"
    output += f"\n[tr][td]Posts/Day:  [/td][td]~{round(ppd, 5)}[/td][/tr]"
    output += f"\n[tr][td]Posts/Hour:  [/td][td]~{round(ppd/24, 5)}[/td][/tr]"
    if "goal" in thread_data:
        output += f"\n[tr][td]Goal:  [/td][td]{thread_data['goal']}[/td][/tr]"
        if "postID" in thread_data["types"]:
            progress = thread_data["store"]["recent_post"] / thread_data["goal"]
            output += (
                f"\n[tr][td]Completion:  [/td][td]{round(progress*100, 2)} % "
                f"({thread_data['store']['recent_post']}/{thread_data['goal']})[/td][/tr]"
            )
            until = thread_data["goal"] / ppd
            complete_date = first_post_date + datetime.timedelta(days=until)
            output += f"\n[tr][td]Est. Completion Date:[/td][td]{complete_date:%b %d, %Y %I:%M:%S %p}[/td][/tr]"
    output += "[/table]"
    return output


def estimate(bot_data, thread_data, user_data):
    # nofix: removed the feature on estimating other topics, for two reasons
    # 1. coupling = bad
    # 2. now not possible since only one thing can open the shelve
    if "goal" in thread_data:
        first_post_date = thread_data["store"]["first_post_date"]
        today_date = datetime.datetime.now().astimezone()
        diff = today_date - first_post_date
        ppd = thread_data["store"]["recent_post"] / (diff.days + (diff.seconds / 86400))

        until = thread_data["goal"] / ppd
        complete_date = first_post_date + datetime.timedelta(days=until)
        output = f"Est. Completion Date: {complete_date:%b %d, %Y %I:%M:%S %p}"
        if len(thread_data["store"].setdefault("estimates", [])) >= 1:
            output += "\nPrevious Estimates: [code]"
            for today, complete in thread_data["store"]["estimates"]:
                output += f"\n({today:%b %d, %Y %I:%M:%S %p}) {complete:%b %d, %Y %I:%M:%S %p}"
            output += "[/code]"

        thread_data["store"]["estimates"].append((today_date, complete_date))
    else:
        output = "This topic does not have a set goal."
    return output


def choose(bot_data, thread_data, user_data, *options):
    if (len(options) == 0):
        return "You didn't give anything for me to choose."
    else:
        return random.choice([
            "I'll go with ",
            "How about...",
            "Rolled a 1d"+str(len(options))+", and got ",
            "Picked randomly, and got ",
            "The bot chooses ",
            "Let's go with ",
            "That one, the one that says ",
        ]) + "\"" + random.choice(options) + "\"."


# These turn the functions above into commands:
coin_command = fw.Command("coin", coin, [], helpShort="Flips a coin and gives you the result.", helpLong="Flips a coin and gives you the result.")
dice_command = fw.Command("dice", dice,
                          [fw.CommandInput("num", "int", "1", "The number of dice."), fw.CommandInput("size", "int", "20", "The number of sides on the dice.")],
                          helpShort="Rolls [i]num[/i] [i]sides[/i]-sided dice, and gives you the result.",
                          helpLong="Rolls [i]num[/i] [i]sides[/i]-sided dice, and gives you the result.")
bot_command = fw.Command("bot", bot, [], helpShort="Returns various statistics about the bot.", helpLong="Returns various statistics about the bot.")
help_command = fw.Command("help", _help, [])
suggest_command = fw.Command("suggest", suggest, [fw.CommandInput("suggestion", "str")])
ti_command = fw.Command("threadInfo", threadInfo, [])
esti_command = fw.Command("estimate", estimate, [])
choose_command = fw.Command("choose", choose, [fw.CommandInput("options", "multi_str")])

# This registers the commands for use by Nihonium.
commandlist = {
    "coin": coin_command, "dice": dice_command, "roll": dice_command, "bot": bot_command, "botinfo": bot_command, "help": help_command,
    "suggest": suggest_command, "threadinfo": ti_command, "estimate": esti_command, "choose": choose_command, "choise": choose_command
}
# This registers commands exclusive to certain bots.
# Format: {"<id>": {"<command_name>": "<function>"}}
ex_commandlist = {"nihonium2": {"coin2": coin2}}
# This registers functions to be performed at the end of a parse-cycle.
do_last = []
# This registers functions to be performed at the beginning of a parse-cycle.
do_first = []

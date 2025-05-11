import random, tomllib, datetime, traceback, asyncio, shelve, logging  # built-in modules

# custom modules
import versions
import commands
from utils import InlineDict
import regex
from tbgclient import Session, User, Alert, Message
import tbgclient


nihonium_version = versions.Version(0, 14, 0)
"""The version of the base nihonium install; try not to modify this"""
fork_version = versions.Version(0, 15, 0)
"""The version of the current fork"""

db = shelve.open("persistent.store", writeback=True)
# As cool as Nihonium's TUI is, it's nothing but bells and whistles, so we're getting rid of it
# This will be a systemd service anyway
logger = logging.getLogger(__name__)
statistics = InlineDict(db, "stats")
"""Statistics of the bot's actions."""
uptime = datetime.datetime.now()
outbox_messages = InlineDict(db, "outbox")
"""Messages that's going to be posted to the TBGs."""

incompatible_commands = ()
"""Commands this copy is incompatible with."""
disabled_commands = ("rolladice", "rolldice")
"""Commands disabled in this copy. Overridden by `topics.<tid>.exclusive_commands`."""

# sense if dbm.sqlite3 is present
try:
    __import__("dbm").sqlite3
except (ImportError, AttributeError):
    logger.warn("dbm.sqlite3 doesn't seem to exist. This might be a bad omen.")

with open("config.toml", "r", encoding="utf-8") as infofile:
    config = tomllib.load(infofile)  # General configuration of the bot.
    bot_info = config["bot"]  # Info about the bot.
    bot_strings = bot_info["strings"]
    topic_info = config["topics"]


def motd():
    return random.choice([
        "beep",
        "a",
        str(fork_version),
        ":)",
        "boop",
        ":(",
        ":|",
        # str(loopNo),
        "Also try "+random.choice([
            "Minecraft",
            "Terraria",
            "Fighting Simulator 3",
            "Legends of Idleon",
            "Nickel",
            "Flerovium",
            "Grogar",
            "We Play Cards",
            "Shef Kerbi News Network",
            "Platinum",
            "Gaul Soodman",
            "Nihonium",
        ])+"!",
        "yo",
        "motd",
        "today's lucky number: "+str(random.randint(1, random.randint(1, 1000))),
        "",
        "lorem ipsum",
        "so how's your day been",
        "happy current holiday",
        repr(fork_version),
        "You can't roll right now, you can roll again in about 600 minutes.",
        "You can't roll right now, you can roll again in about 240 minutes.",
        "Spy!",
        "It pulls the strings and makes them ring.",
    ])


def assemble_botdata():
    return {
        "uptime": uptime,
        "data": statistics,
        "thread_ids": config["topics"].keys(),
        "post_ids": config["topics"],
        "cookies": tbgclient.session.default_session.cookies,
        "session": tbgclient.session.default_session.session,
        "headers": {},
        "version": nihonium_version,
        "forkversion": fork_version,
        "bot_info": config,
    }


def assemble_threaddata(tid: int):
    # TODO: replace the stub with something configurable
    return {**topic_info.get(tid, {}), "thread_id": tid}


def assemble_userdata(user: User):
    return {
        "name": user.name,
        "uID": user.uid,
    }


def parse_commands(msg: Message):
    # Escape the [quote], [spoiler], and [code] tags.
    # This is a quick and dirty regex pattern for parsing BBC tags
    # and also the reason why we use the external "regex" instead of the built-in "re"
    escape_pattern = r"""
    \[(\w+)(?:[^\n]*?)\]  # start of tag
    (?:  # the contents
        (?R)  # either recurse
        | [^\[\]]  # or match anything that's not brackets
    )*
    \[/\1\]  # end of tag
    """
    # HACK: Had to un-roll a bit since the recursive method doesn't work by itself currently
    base_escape_pattern = escape_pattern
    for i in range(2, 100):
        escape_pattern = escape_pattern.replace("(?R)", "(?:"+base_escape_pattern.replace("1", str(i))+")")
    # escape_pattern = escape_pattern.replace("(?R)", "$^")
    escape_pattern = regex.compile(escape_pattern, regex.X | regex.S)
    escaped_text = escape_pattern.sub(
        lambda x: "" if x[1] in ("quote", "spoiler", "code") else x[0],
        msg
    )

    # Process every parsed commands.
    command_pattern = regex.compile(fr"^\[member.*\]{regex.escape(bot_info['auth']['username'])}\[/member\] (\w.*)")
    responses = []
    for command_line in command_pattern.finditer(escaped_text):
        statistics["commands_found"] += 1
        words = regex.split(r"\s+", command_line[1].strip())
        command_string = " ".join(words)

        # Execute the command, if it exists or allowed.
        command_name, *arguments = words
        command_name = command_name.lower()
        try:
            # Should we respond to this command?
            if (
                "exclusive_commands" in topic_info.get(msg.tid, {})
                and command_name in topic_info[msg.tid]["exclusive_commands"]
            ):
                # This condition overrides the bottom one.
                pass
            elif command_name in incompatible_commands:
                continue
            if msg.user.name in bot_info["ignore_list"]:
                continue

            # Does this command even exist?
            if command_name in commands.commands:
                command = commands.commands[command_name]
            elif bot_info["id"] in commands.ex_commands:
                command = commands.ex_commands[bot_info["id"]]

            # If so, then do it!
            statistics["valid_commands"] += 1
            output = command.run(
                assemble_botdata(),
                assemble_threaddata(msg.tid),
                assemble_userdata(msg.user),
                *arguments
            )
            if output == "":
                # No idea why this is distinguished with output being None
                # maybe ask reali for this one
                response = ""
            elif output is None:
                logger.warn(f"Command produces no output: {command_string!r}")
                response = bot_strings['no_output']
            else:
                response = output
                statistics["commands_parsed"] += 1
        except (TypeError, ValueError, KeyError, IndexError, OverflowError, ZeroDivisionError):
            stack_trace = traceback.format_exc()
            logger.error(
                f"Error processing {command_string!r}:\n"
                f"{stack_trace}"
            )
            response = f"{bot_strings['on_error']}\n[code]{stack_trace}[/code]"
            statistics["errors_thrown"] += 1

        # Don't forget to reference the quote.
        response = f"[quote author={msg.user.name} link=msg={msg.mid} date={msg.date:%s}]{command_string}[/quote]\n{response}"
        responses.append(response)
    return responses


# Doing this with async functions is kinda pointless, since tbgclient uses synchronous requests
# But since Nihonium uses it, we might as well use it anyway
async def process_loop():
    """Retrieves all new alerts, processes them, and store them in the outbox."""
    from itertools import chain

    last_aid = db.get(b"last_aid", 0)

    while True:
        # Retrieve all new alerts.
        logger.info("Retrieving alerts")
        statistics["parse_cycles"] += 1
        for alert in chain.from_iterator(Alert.pages()):
            match alert:
                case Alert.Mentioned(aid=aid, msg=msg) if aid > last_aid:
                    # We got a ping.
                    logger.info(f"Got alert ID {aid}")
                    statistics["alerts_received"] += 1
                    db["last_aid"] = aid
                    # Process them.
                    outbox_messages[str(msg.tid)].setdefault([]).extend(parse_commands(msg))
        db.sync()
        await asyncio.sleep(config["periods"]["process_loop"])


async def publish_loop():
    """Retrieves all messages in the outbox and POSTs them."""
    while True:
        no_items = True  # in outbox

        # HACK: need to iterate through a tuple since we're going to delete the keys
        for tid in tuple(outbox_messages):
            no_items = False
            tid = int(tid)
            logger.info(f"Posting response for topic ID {tid}")
            msg = Message(tid, content="\n\n".join(outbox_messages[tid]))
            msg.submit()
            # Message posted, we can delete it from the outbox
            del outbox_messages[tid]
            db.sync()
            await asyncio.sleep(config["periods"]["publish_loop"])

        if no_items:
            await asyncio.sleep(config["periods"]["no_publish_loop"])


async def main_loop():
    """Starts everything that Roentgenium needs."""
    try:
        await asyncio.gather(
            process_loop(),
            publish_loop(),
        )
        return 0
    except Exception:
        logger.critical("Main loop caught an exception:\n" + traceback.format_exc())
        return 1


# Log in to the TBGs.
try:
    with open("pass.txt", "r") as f: password = f.read()
except OSError:
    # If there's no password file, it's probably in config.toml
    try:
        password = bot_info["auth"]["username"]
    except KeyError:
        # If it's not, prompt for one
        logger.warn(
            "No password file found, and bot.auth.password isn't defined. Roentgenium will need to prompt for one. "
            "If this is running as a service, \x1B[1myou should reconfigure it now.\x1B[0m"
        )
        import getpass
        password = getpass.getpass("Enter password: ")

session = Session()
session.login(bot_info["auth"]["username"])
session.make_default()

# Action!
exit_code = asyncio.run(main_loop())
exit(exit_code)

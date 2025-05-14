# built-in modules
import sys, random, tomllib, datetime, traceback, asyncio, shelve, logging, argparse
from pprint import pformat

# custom modules
import versions
import commands
from utils import InlineDict
import regex
from tbgclient import Session, User, Alert, Message
import tbgclient

parser = argparse.ArgumentParser(
    prog='Roentgenium',
    description='A bot for the TBGs, round 2.',
    epilog='For more info, visit https://github.com/Gilbert189/Roentgenium'
)
parser.add_argument('-v', '--verbose',
                    action='store_const', const=logging.DEBUG, default=logging.INFO,
                    help='Make logging more detailed'
                    )
parser.add_argument('-I', '--repl',
                    action='store_true',
                    help='Enter REPL mode'
                    )
args = parser.parse_args()

logger = logging.getLogger("rontgen" if __name__ == "__main__" else __name__)
logging.basicConfig(format="%(levelname)s@%(name)s: %(message)s", level=args.verbose)

nihonium_version = versions.Version(0, 15, 0)
"""The version of the base nihonium install; try not to modify this"""
fork_version = versions.Version(0, 15, 0)
"""The version of the current fork"""


db = shelve.open("persistent.data", writeback=True)
# As cool as Nihonium's TUI is, it's nothing but bells and whistles, so we're getting rid of it
# This will be a systemd service anyway
statistics = InlineDict(db, "stats")
"""Statistics of the bot's actions."""
uptime = datetime.datetime.now()
outbox_messages = InlineDict(db, "outbox")
"""Messages that's going to be posted to the TBGs."""
outbox_lock = asyncio.Lock()
"""Ensures only one async function is touching the outbox."""
outbox_attention = asyncio.Event()
"""Tells :py:func:`publish_loop()` if new messages is waiting to be published."""

incompatible_commands = ()
"""Commands this copy is incompatible with."""
disabled_commands = ("rolladice", "rolldice")
"""Commands disabled in this copy. Overridden by `topics.<tid>.exclusive_commands`."""

# sense if dbm.sqlite3 is present
try:
    __import__("dbm").sqlite3
except (ImportError, AttributeError):
    logger.warning("dbm.sqlite3 doesn't seem to exist. This might be a bad omen.")

with open("config.toml", "rb") as infofile:
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
    return {**topic_info.get(str(tid), {}), "thread_id": tid, "store": InlineDict(db, f"topic.{tid}")}


def assemble_userdata(user: User):
    return {
        "name": user.name,
        "uID": user.uid,
    }


def parse_commands(msg: Message):
    my_logger = logger.getChild('parse_commands')
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
    for i in range(2, 20):
        escape_pattern = escape_pattern.replace("(?R)", "(?:"+base_escape_pattern.replace("1", str(i))+")")
    # escape_pattern = escape_pattern.replace("(?R)", "$^")
    escape_pattern = regex.compile(escape_pattern, regex.X | regex.S)
    escaped_text = escape_pattern.sub(
        lambda x: "" if x[1] in ("quote", "spoiler", "code") else x[0],
        msg.content
    )

    # Process every parsed commands.
    command_pattern = regex.compile(fr"^\[member.*\]{regex.escape(bot_info['auth']['username'])}\[/member\] (\w.*)")
    my_logger.debug(f"Parsing message {escaped_text!r} with pattern {command_pattern}")
    responses = []
    for command_line in command_pattern.finditer(escaped_text):
        statistics["commands_found"] += 1
        words = regex.split(r"\s+", command_line[1].strip())
        command_string = " ".join(words)
        my_logger.debug(f"[!] Parsing command {command_string!r}")

        # Execute the command, if it exists or allowed.
        command_name, *arguments = words
        command_name = command_name.lower()
        try:
            # Should we respond to this command?
            if not bot_info["all_topics"] and str(msg.tid) not in topic_info:
                # No trespassing.
                my_logger.debug("[X] No trespassing, aborting")
                continue
            if (
                "exclusive_commands" in topic_info.get(str(msg.tid), {})
                and command_name in topic_info[str(msg.tid)]["exclusive_commands"]
            ):
                # This condition overrides the bottom one.
                my_logger.debug("[!] Exclusive command, continuing")
                pass
            elif command_name in incompatible_commands:
                # Not supposed to use this command.
                my_logger.debug("[X] Incompatible command, aborting")
                continue
            if msg.user.name in bot_info["ignore_list"]:
                # I don't like this user.
                my_logger.debug("[X] User in ignore list, aborting")
                continue

            # Does this command even exist?
            if command_name in commands.commands:
                my_logger.debug("[!] Identified command as a standard command.")
                command = commands.commands[command_name]
            elif bot_info["id"] in commands.ex_commands:
                my_logger.debug("[!] Identified command as an extra command.")
                command = commands.ex_commands[bot_info["id"]]
            else:
                my_logger.debug("[X] Unknown command, aborting.")
                continue

            # If so, then do it!
            statistics["valid_commands"] += 1
            output = command.run(
                assemble_botdata(),
                assemble_threaddata(msg.tid),
                assemble_userdata(msg.user),
                *arguments
            )
            my_logger.debug(f"[!] Command outputted {output!r}")
            if output == "":
                # No idea why this is distinguished with output being None
                # maybe ask reali for this one
                response = ""
            elif output is None:
                my_logger.warning(f"Command produces no output: {command_string!r}")
                response = bot_strings['no_output']
            else:
                response = output
                statistics["commands_parsed"] += 1
        except (TypeError, ValueError, KeyError, IndexError, OverflowError, ZeroDivisionError):
            stack_trace = traceback.format_exc()
            my_logger.error(
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
    my_logger = logger.getChild('process_loop')
    from itertools import chain

    while True:
        # Retrieve all new alerts.
        my_logger.info("Retrieving alerts")
        statistics["parse_cycles"] += 1
        total_alerts = 0
        processed_alerts = 0
        last_aid = db.get("last_aid", 0)

        async with outbox_lock:
            for alert in chain.from_iterable(Alert.pages()):
                match alert:
                    case Alert.Mentioned(aid=aid, msg=msg) if aid > last_aid:
                        # We got a ping.
                        my_logger.info(f"Got alert ID {aid}")
                        statistics["alerts_received"] += 1

                        # Process them.
                        msg = msg.update()
                        msg = msg.update(method="quotefast")  # this retrieves the BBC instead of the raw HTML
                        outbox_messages.setdefault(str(msg.tid), [])
                        result = parse_commands(msg)
                        my_logger.debug(f"Command resulted in {result=}")
                        if len(result) > 0:  # we got something!
                            outbox_messages[str(msg.tid)].extend(result)
                            outbox_attention.set()

                        # Do some metrics.
                        processed_alerts += 1
                        db["last_aid"] = max(db["last_aid"], aid)
                total_alerts += 1
            my_logger.info(f"Done retrieving alerts. Processed {processed_alerts} out of {total_alerts} alerts.")
            db.sync()

        await asyncio.sleep(bot_info["periods"]["process_loop"])


async def publish_loop():
    """Retrieves all messages in the outbox and POSTs them."""
    my_logger = logger.getChild('process_loop')
    while True:
        # Wait until we get something
        await outbox_attention.wait()

        # HACK: need to iterate through a tuple since we're going to delete the keys
        async with outbox_lock:
            tids_todo = tuple(outbox_messages)
            my_logger.info(f"Need to publish {len(tids_todo)} messages: {tids_todo}")
            for tid in tids_todo:
                my_logger.info(f"Posting response for topic ID {tid}")

                # Sometimes the list given is blank (because no commands gave any result)
                if len(outbox_messages[tid]) > 0:
                    msg = Message(
                        tid=int(tid),
                        subject=f"Response from Roentgenium {fork_version} @ {sys.version}",
                        content="\n\n".join(outbox_messages[tid]),
                    )
                    msg.submit()
                    my_logger.debug("Response posted")  # IDEA: tell what ID the new message is posted?
                    await asyncio.sleep(bot_info["periods"]["publish_loop"])
                else:
                    my_logger.info("Response has no content, aborting")
                    await asyncio.sleep(bot_info["periods"]["no_publish_loop"])

                # Either posted or not, we can delete it from the outbox
                del outbox_messages[tid]
                db.sync()

        my_logger.debug("Done publishing the outbox for now.")
        await asyncio.sleep(bot_info["periods"]["no_publish_loop"])
        outbox_attention.clear()


async def update_siggy(session: Session, going_down=False):
    """Update the bot's signature."""
    logger.info("Updating signature")
    # Retrieve the initial profile
    user = session.user.update()

    # Construct the siggy
    siggy = ""
    siggy += motd()
    siggy += "\n[br]\n"
    siggy += f"[b]{bot_info['name']}[/b] (version {fork_version})\n"
    siggy += f"[i]{bot_info['strings']['tagline']}[/i]\n"
    if going_down:
        siggy += bot_info['strings']['offline']
    else:
        siggy += bot_info['strings']['online']

    user.signature = siggy
    user.blurb = bot_info['strings']['tagline']
    if "footer" in bot_info['strings'] and bot_info['strings']['footer'].strip() != "":
        siggy += "\n[br]\n"
        siggy += bot_info['strings']['footer']
    user.submit()


async def siggy_loop(session: Session):
    """Update the bot's signature periodically."""
    while True:
        await update_siggy(session, going_down=False)
        await asyncio.sleep(bot_info["periods"]["siggy_loop"])


async def scraping_loop(session: Session):
    """Does anything related to scraping the TBGs."""
    my_logger = logger.getChild("scraping_loop")
    from tbgclient import api, parsers, Page

    while True:
        statistics["last_scrape"] = datetime.datetime.now().astimezone()
        # For threadInfo, scrape the newest post in the topic listed in the config
        for tid in topic_info:
            tid = int(tid)
            my_logger.info(f"Retrieving data of topic ID {tid}'s most recent post")

            thread_data = assemble_threaddata(tid)
            res = api.get_topic_page(session, tid, "new")
            page = Page(**parsers.forum.parse_page(res.content, parsers.forum.parse_topic_content), content_type=Message)

            total_posts = (page.total_pages-1) * api.TOPIC_PER_PAGE + len(page.contents)
            thread_data["store"]["recent_post"] = total_posts

        await asyncio.sleep(bot_info["periods"]["scraping_loop"])


async def main_loop(session: Session):
    """Starts everything that Roentgenium needs."""
    logger.info("Enter main loop")
    statistics.setdefault("parse_cycles", 0)
    statistics.setdefault("alerts_received", 0)
    statistics.setdefault("commands_found", 0)
    statistics.setdefault("valid_commands", 0)
    statistics.setdefault("commands_parsed", 0)
    statistics.setdefault("errors_thrown", 0)
    statistics.setdefault("last_scrape", None)

    # See if there's still some messages left in the outbox
    for tid in outbox_messages:
        if len(outbox_messages[tid]) > 1:
            outbox_attention.set()
            break

    exit_code = 0
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(process_loop())
            group.create_task(publish_loop())
            group.create_task(siggy_loop(session))
            group.create_task(scraping_loop(session))
    except Exception:
        logger.critical("Main loop caught an exception:\n" + traceback.format_exc())
        exit_code = 1
    finally:
        logger.critical("Roentgenium is going to shut down now!")
        await update_siggy(session, going_down=True)
    return exit_code


# Log in to the TBGs.
try:
    with open("pass.txt", "r") as f: password = f.read()
except OSError:
    # If there's no password file, it's probably in config.toml
    try:
        password = bot_info["auth"]["username"]
    except KeyError:
        # If it's not, prompt for one
        logger.warning(
            "No password file found, and bot.auth.password isn't defined. Roentgenium will need to prompt for one. "
            "If this is running as a service, \x1B[1myou should reconfigure it now.\x1B[0m"
        )
        import getpass
        password = getpass.getpass("Enter password: ")

logger.info("Logging in as " + bot_info["auth"]["username"])
session = Session()
session.login(bot_info["auth"]["username"], password)
session.make_default()


def run():
    exit_code = asyncio.run(main_loop(session))
    db.close()
    exit(exit_code)


# Action!
if args.repl:
    import code
    code.interact(
        banner="You are now in the Roentgenium REPL. Call the run() function to continue execution.",
        exitmsg="",
        local=globals()
    )
else:
    run()

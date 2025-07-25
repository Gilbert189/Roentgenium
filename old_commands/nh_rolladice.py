import versions
from . import framework as fw
import random, json, datetime, math

version = versions.Version(1, 10, 0)
nihonium_minver = versions.Version(0, 14, 0)
alt_minvers = {}

did_roll = False

# TODO: Replace with something else
"""
with open("botInfo.json", "r", encoding="utf-8") as infofile:
    bot_info = json.loads(infofile.read())  # Info about the bot.

pc_len = datetime.timedelta(seconds=bot_info["cycleDelay"])
"""


def roll_a_dice(bot_data, thread_data, user_data, action="roll"):
    global did_roll
    with open("user_data.json", "r+", encoding="utf-8") as rollfile:
        roll_data = json.loads(rollfile.read())
    output = ""
    uID = str(user_data["uID"])
    if uID not in roll_data: roll_data[uID] = {"rd_points": 0, "rd_timer": 0, "rd_limit": 0}  # will be changed later
    fw.logEntry(str(roll_data[uID]))
    if (action == "roll") and (roll_data[uID]["rd_limit"] < 5):
        roll_data2 = {**roll_data}
        del roll_data2["roll_last"]
        timenow = datetime.datetime.now(tz=datetime.timezone.utc)
        if roll_data[uID]["rd_timer"] > timenow.timestamp():
            output = (
                "You can't roll right now, you can roll again in about " + str(math.ceil((roll_data[uID]["rd_timer"] - timenow.timestamp())/60)) + " minutes."
            )
            roll_data[uID]["rd_limit"] += 1
            fw.logEntry(str(roll_data[uID]))
            fw.logEntry("a")
            if (roll_data[uID]["rd_limit"] == 5):
                output += "\nThis is your 5th roll this parse-cycle, so you won't be able to roll again until the next parse-cycle."
                fw.logEntry("b")
            with open("user_data.json", "w", encoding="utf-8") as rollfile:
                rollfile.write(json.dumps(roll_data, indent=4))
        else:
            fw.logEntry("c")
            done = False
            while not done:
                done = True
                result = random.randint(1, 10)
                output += "You rolled a " + str(result)
                # FIXME: Make this use f-strings
                if result == 1:
                    roll_data[uID]["rd_points"] += 1
                    output += ", and gained one point."
                elif result == 2:
                    roll_data[uID]["rd_points"] += 2
                    roll_data[uID]["rd_timer"] = int((timenow + (pc_len*8)).timestamp())
                    output += ", and gained two points. You can't roll for the next eight parse-cycles."
                elif result == 3:
                    hold = math.floor((int(timenow.timestamp()) - roll_data["roll_last"])/(60*60))
                    roll_data[uID]["rd_points"] += hold
                    output += ", and gained " + str(hold) + " point" + ("s" if hold != 1 else "") + "."
                elif result == 4:
                    hold = random.randint(1, 10)
                    target = random.choice(list(roll_data2.keys()))
                    roll_data[target]["rd_points"] -= hold
                    output += ", causing someone random to lose " + str(hold) + " point" + ("s" if hold != 1 else "") + "."
                elif result == 5:
                    hold = random.randint(1, 5)
                    target = random.choice(list(roll_data2.keys()))
                    roll_data[target]["rd_points"] -= hold
                    roll_data[uID]["rd_points"] += hold
                    output += (
                        ", causing someone random to lose " + str(hold) + " point" + ("s" if hold != 1 else "") + ", and for you to recieve said lost points."
                    )
                elif result == 6:
                    roll_data[uID]["rd_points"] -= 1
                    output += ", and lost one point."
                elif result == 7:
                    roll_data[uID]["rd_points"] += 1
                    done = False
                    output += ", gained one point, and get to roll again!\n"
                elif result == 8:
                    roll_data[uID]["rd_points"] += 1
                    target = random.choice(list(roll_data2.keys()))
                    roll_data[target]["rd_points"] += 2
                    output += ", and gained one point, while someone random gained two."
                elif result == 9:
                    if (random.randint(1, 3) == 1): hold = (random.randint(1, random.randint(1, 60)))
                    else: hold = 0
                    roll_data[uID]["rd_points"] += hold
                    output += ", and gained points equal to how long you have on the 60 second rule.\n...we'll pretend that's " + str(hold) + "."
                elif result == 10:
                    roll_data[uID]["rd_points"] += 10
                    roll_data[uID]["rd_timer"] = int((timenow + (pc_len*20)).timestamp())
                    output += ", and gained ten points! You can't roll for the next twenty parse-cycles, though."
            output += "\nYou now have " + str(roll_data[uID]["rd_points"]) + " point" + ("s" if roll_data[uID]["rd_points"] != 1 else "") + "."
            roll_data[uID]["rd_limit"] += 1
            fw.logEntry("d")
            if (roll_data[uID]["rd_limit"] == 5):
                output += "\nThis is your 5th roll this parse-cycle, so you won't be able to roll again until the next parse-cycle."
                fw.logEntry("e")
            with open("user_data.json", "w", encoding="utf-8") as rollfile:
                rollfile.write(json.dumps(roll_data, indent=4))
            did_roll = True
    elif (action == "roll") and (roll_data[uID]["rd_limit"] >= 5):
        output = ""
    elif action in ["rd_points", "score", "check"]:
        hold = roll_data[uID]["rd_points"]
        output += "You have " + str(hold) + " point" + ("s" if hold != 1 else "") + "."
    elif action in ["scoreboard", "leaderboard", "scores"]:
        output += "Current leaderboard:\n[code]"
        roll_data2 = {**roll_data}
        del roll_data2["roll_last"]
        # based off of careerkarma.com/blog/python-sort-a-dictionary-by-value/
        for i in sorted(roll_data2, key=lambda x: roll_data[x]["rd_points"]):
            output += str(i).rjust(4) + ": " + str(roll_data2[i]["rd_points"]) + " point" + ("s" if roll_data2[i]["rd_points"] != 1 else "") + "\n"
        output += "[/code][i](Note: the leaderboard uses user IDs rather than usernames, as that is all that is stored.)[/i]"
    return output


rollADice = roll_a_dice


def update_roll_last():
    global did_roll
    if did_roll:
        with open("user_data.json", "r+", encoding="utf-8") as rollfile:
            roll_data = json.loads(rollfile.read())
        timenow = datetime.datetime.now(tz=datetime.timezone.utc)
        roll_data["roll_last"] = int(timenow.timestamp())
        with open("user_data.json", "w", encoding="utf-8") as rollfile:
            rollfile.write(json.dumps(roll_data, indent=4))


updateRollLast = update_roll_last


def reset_did_roll():
    global did_roll
    did_roll = False


resetDidRoll = reset_did_roll


def empty_limits():
    with open("user_data.json", "r+", encoding="utf-8") as rollfile:
        roll_data = json.loads(rollfile.read())
    roll_data2 = {**roll_data}
    del roll_data2["roll_last"]
    for i in roll_data2:
        roll_data[i]["rd_limit"] = 0
    with open("user_data.json", "w", encoding="utf-8") as rollfile:
        rollfile.write(json.dumps(roll_data, indent=4))


emptyLimits = empty_limits


diceCommand = fw.Command("rolladice", rollADice, [fw.CommandInput("action", "str", "roll", "What action you want to perform.")],
                         helpShort="Roll a dice and see what happens.")


commandlist = {"rolladice": diceCommand, "rolldice": diceCommand}
ex_commandlist = {}
do_last = [updateRollLast, emptyLimits]
do_first = [resetDidRoll]

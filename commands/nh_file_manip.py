import versions
from . import framework as fw
import shutil, os, datetime, math

version = versions.Version(1, 9, 0)
nihonium_minver = versions.Version(0, 10, 3)
alt_minvers = {}


def sanitize_filename(fn):
    # codes:
    # 0 | valid
    # 1 | contains ".."
    # 2 | is bad device name
    # 3 | contains invalid character ( < > : " \ | ? *)
    if "../" in fn: return [False, 1]
    elif fn == "con": return [False, 2]
    elif fn == "com": return [False, 2]
    elif fn == "prn": return [False, 2]
    elif any(x in fn for x in ('<', '>', ':', '"', '\\', '|', '?', '*')): return [False, 3]  # https://stackoverflow.com/a/21406748
    else: return [True, 0]


sanitizeFilename = sanitize_filename


# from Nihonium
def log_entry(entry: str, timestamp=None):  # Used to add entries to the log files.
    if timestamp is None: timestamp = datetime.datetime.now()
    with open("logs/" + timestamp.strftime("%Y%m%d") + ".log", "a", encoding="utf-8") as logfile:
        logfile.write("[" + timestamp.strftime("%I:%M:%S.%f %p") + "] " + entry + "\n")


logEntry = log_entry


def text(bot_data, thread_data, user_data, command="read", filename="_", *other):
    # commands:
    # read       | outputs the contents of the file
    # write      | replaces the contents of the file with " ".join(other)
    # append     | add " ".join(other) to the end of the file
    # appendline | add a new line at the end of the file, followed by " ".join(other)
    # insert     | insert " ".join(other[1:]) after character other[0]
    # cut        | cut a section of the file, removing it (clipboard will be emptied on paste)
    # copy       | copy a section of the file, trunciated if it ends outside the file
    # paste      | paste onto the end of the file, fails if the clipboard is empty
    # create     | create a file, fails if it exists
    # duplicate  | duplicate a file, fails if it does not exist
    # delete     | delete a file, fails if it does not exist
    # _.txt is unique in that append and insert behave like write, copy and cut select everything, paste overwrites everything...
    # ...and create, duplicate, and delete all fail
    if filename == "_":
        if command == "append": command = "write"
        if command == "insert": command = "write"
    sani = sanitize_filename(filename)
    if sani[0]: pass
    else:
        return "It seems like somethings wrong with that filename.[code]" + [
            "Wait, no, this is a bug.", "Cannot go up a folder.", "Invalid device name.", "Contains a forbidden character."
        ][sani[1]] + "[/code]"
    if command == "read":
        try:
            with open("files/" + filename + ".txt", "r", encoding="utf-8") as file:
                logEntry("Read file '" + filename + ".txt'")
                return "Contents of [i]" + filename + ".txt[/i]: \n" + file.read()
        except IOError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    elif command == "write":
        try:
            with open("files/" + filename + ".txt", "w+", encoding="utf-8") as file:
                file.write(" ".join(other))
                file.seek(0)
                logEntry("Wrote to file '" + filename + ".txt'")
                return "New contents of [i]" + filename + ".txt[/i]: \n" + file.read()
        except IOError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    elif command == "append":
        try:
            with open("files/" + filename + ".txt", "a+", encoding="utf-8") as file:
                file.write(" ".join(other))
                file.seek(0)
                logEntry("Wrote to file '" + filename + ".txt'")
                return "New contents of [i]" + filename + ".txt[/i]: \n" + file.read()
        except IOError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    elif command == "appendline":
        try:
            with open("files/" + filename + ".txt", "a+", encoding="utf-8") as file:
                file.write("\n")
                file.write(" ".join(other))
                file.seek(0)
                logEntry("Wrote to file '" + filename + ".txt'")
                return "New contents of [i]" + filename + ".txt[/i]: \n" + file.read()
        except IOError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    elif command == "insert":
        index = int(other[0])
        try:
            with open("files/" + filename + ".txt", "r", encoding="utf-8") as file: temp = file.read()
            with open("files/" + filename + ".txt", "w+", encoding="utf-8") as file:
                file.write(temp[:index] + " ".join(other[1:]) + temp[index:])
                file.seek(0)
                logEntry("Wrote to file '" + filename + ".txt'")
                return "New contents of [i]" + filename + ".txt[/i]: \n" + file.read()
        except IOError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    elif command == "create":
        try:
            with open("files/" + filename + ".txt", "x", encoding="utf-8") as file:
                logEntry("Created file '" + filename + ".txt'")
                return "Successfully created [i]" + filename + ".txt[/i]"
        except IOError: return "A file by the name [i]" + filename + ".txt[/i] already exists."
    elif command == "duplicate":
        if filename == "_": return "Can't duplicate _."
        else:
            try:
                shutil.copy2("files/" + filename + ".txt", "files/copy_" + filename + ".txt")
                logEntry("Copied file '" + filename + ".txt' to 'copy_" + filename + ".txt'")
                return "Successfully duplicated [i]" + filename + ".txt[/i]"
            except FileNotFoundError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    elif command == "delete":
        if filename == "_": return "Can't delete _."
        else:
            try:
                os.remove("files/" + filename + ".txt")
                logEntry("Deleted file '" + filename + ".txt'")
                return "Successfully deleted [i]" + filename + ".txt[/i]"
            except IOError: return "No file by the name [i]" + filename + ".txt[/i] exists."
    else: return "Invalid command: " + command


def files(bot_data, thread_data, user_data, command="read", filename="_.txt", *other):
    # commands:
    # read      | read the hex data of a file
    # rename    | rename a file
    # list      | list all files
    # move      | move a file
    # cut       | cut a section of the file, removing it (clipboard will be emptied on paste)
    # copy      | copy a section of the file, trunciated if it ends outide the file
    # paste     | paste onto the end of the file, fails if the clipboard is empty
    # create    | create a file, fails if it exists
    # duplicate | duplicate a file, fails if it does not exist
    # delete    | delete a file, fails if it does not exist
    sani = sanitize_filename(filename)
    if sani[0]: pass
    else:
        # FIXME: Apply DRY here: this isn't sufficient
        return "It seems like somethings wrong with that filename.[code]" + [
            "Wait, no, this is a bug.", "Cannot go up a folder.", "Invalid device name.", "Contains a forbidden character."
        ][sani[1]] + "[/code]"
    if command == "read":
        try:
            with open("files/" + filename, "rb") as file:
                logEntry("Read file '" + filename + "'")
                output = "Contents of [i]" + filename + "[/i]: \n[code]"
                filehex = file.read().hex()
                filehexlist = []
                for i in range(0, len(filehex), 2):
                    filehexlist.append(filehex[i:i+2])
                d = "         x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF\n        ------------------------------------------------\n"
                for j in range(math.ceil(len(filehexlist) / 16)):
                    d += "0x" + hex(j)[2:].rjust(3, "0") + "x |"
                    e = ""
                    for k in filehexlist[j * 16:(j * 16) + 16]:
                        e += " " + k
                    d += e.ljust(48)
                    d += " | "
                    for byte in filehexlist[j * 16:(j * 16) + 16]:
                        if byte == "0a":  # newline
                            d += "↕"
                        elif byte == "09":  # tab
                            d += "↔"
                        elif byte == "00":  # null
                            d += "Φ"
                        elif int(byte, 16) > 126:  # outside ascii
                            d += "·"
                        elif int(byte, 16) < 32:  # before printable
                            d += "•"
                        elif byte == "20":  # space
                            d += "˽"
                        else:  # other
                            m = bytes.fromhex(byte)
                            d += m.decode("ASCII")
                    d += "\n"
                d = d[0:-1]
                output += d
                output += "[/code]"
                return output
        except IOError: return "No file by the name [i]" + filename + "[/i] exists."
    elif command == "rename":
        sani = sanitize_filename(other[0])
        if sani[0]: pass
        else:
            return "It seems like somethings wrong with that filename.[code]" + [
                "Wait, no, this is a bug.", "Cannot go up a folder.", "Invalid device name.", "Contains a forbidden character."
            ][sani[1]] + "[/code]"
        try:
            os.rename("files/" + filename, "files/" + other[0])
            logEntry("Renamed file '" + filename + "' to '" + other[0] + "'")
            return "Renamed file [i]" + filename + "[/i] to [i]" + other[0] + "[/i]"
        except FileNotFoundError: return "No file by the name [i]" + filename + "[/i] exists."
        except FileExistsError: return "A file by the name [i]" + other[0] + "[/i] already exists."
    elif command == "list":
        output = "Files: [quote]"
        for i in os.listdir("files"):
            output += i + "\n"
        output += "[/quote]"
        return output
    elif command == "create":
        try:
            with open("files/" + filename, "x", encoding="utf-8") as file: pass
            logEntry("Created file '" + filename + "'")
            return "Successfully created [i]" + filename + "[/i]"
        except IOError: return "A file by the name [i]" + filename + "[/i] already exists."
    elif command == "duplicate":
        if filename == "_": return "Can't duplicate _."
        else:
            try:
                shutil.copy2("files/" + filename, "files/copy_" + filename)
                logEntry("Copied file '" + filename + "' to 'copy_" + filename + "'")
                return "Successfully duplicated [i]" + filename + "[/i]"
            except FileNotFoundError: return "No file by the name [i]" + filename + "[/i] exists."
    elif command == "delete":
        if filename == "_": return "Can't delete _."
        else:
            try:
                os.remove("files/" + filename)
                logEntry("Deleted file '" + filename + "'")
                return "Successfully deleted [i]" + filename + "[/i]"
            except IOError: return "No file by the name [i]" + filename + "[/i] exists."
    else: return "Invalid command: " + command


text_command = fw.Command("text", text, [fw.CommandInput("command", "str", "read", "The subcommand to use."),
                                         fw.CommandInput("filename", "str", "_", "The file to use."),
                                         fw.CommandInput("other", "varies", "", "Varies by subcommand.")],
                          helpShort="Text file modificaton.",
                          helpLong="A set of subcommands for manipulating text files.\n(You can see the list of subcommands on Nihonium's website.)")
file_command = fw.Command("files", files, [fw.CommandInput("command", "str", "read", "The subcommand to use."),
                                           fw.CommandInput("filename", "str", "_", "The file to use."),
                                           fw.CommandInput("other", "varies", "", "Varies by subcommand.")],
                          helpShort="File modificaton.",
                          helpLong="A set of subcommands for manipulating files.\n(You can see the list of subcommands on Nihonium's website.)")


commandlist = {"text": text_command, "files": file_command, "file": file_command}
ex_commandlist = {}
do_last = []
do_first = []

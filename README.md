# Roentgenium
Roentgenium (or just Röntgen) is a reimplementation of [Nihonium](https://github.com/realicraft/Nihonium) using [tbgclient](https://github.com/tbgers/tbgclient). The bot script is rewritten from scratch, but it still retains the command framework (for now).

## Configuration
Röntgen uses a single configuration file, the `config.toml` file. See the file for the documentation.

## New files and directories
Röntgen uses these files and directories, creating them if not present:

* `persistent.data`
  A Python [shelve](https://docs.python.org/3/library/shelve.html) store. Its purpose is self-explanatory.
  You might see `persistent.data-shm` and `persistent.data-wal` files as well when Röntgen is in operation.
  In **very** rare cases, `persistent.data.dat` and `persistent.data.dir` might be used instead.
* `files/`
  The directory where Röntgen saves the files from its file manipulation commands.
* `suggestions.txt`
  A file containing a list of submitted suggestions.

## Commands
Instead of using command prefixes, Röntgen uses mentions to identify commands. Aside from that, everything stays the same.

So, instead of posting something like this:

    rg!dice 10

post this instead:

    @Röntgen dice 10

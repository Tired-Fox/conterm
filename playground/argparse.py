"""
Resources:
    [Typer]()
    [Click]()
    [CMD2]()

Features:
    - tab completion (generate on first run)
    - gracefull exit
    - help message from any sub command
    - pass argument string

<command>
    nested commands

option (-s, --something)
argument (named, list, single, assignment or flag)

Commands:
    - set
        - client
        - database
    - collect
        - find
        - from
        - --name
    - list
    - load
    - intersect
    - run/done
    - show
"""


class Action:
    def __init__(self, callback):
        self._callback_ = callback

    def run():
        pass

COMMANDS = {
    "set": {
        "_type_": "parent",
        "_help_": "Set base application interfaces",
        "client": {},
        "database": {},
    },
    "collect": {},
    "list": {},
    "load": {},
    "intersect": {},
    "done": {},
    "show": {}
}

CMDS = [
    "set client typedb_client",
    "set database typedb_client",
    "collect find ip 192.* --name local_ips",
    "collect find hunt.has.tag --name csc2_hunts",
    "collect from csc2_hunts find hunt.players.found.ip --name csc2_hunts",
    "list collections",
    "load plugin compare_things",
    "intersect local_ips csc2_hunts --name local_csc2_ips",
    "done", # Maybe a better name
    "show local_csc2_ips",
]

if __name__ == "__main__":
    for cmd in CMDS:
        print(cmd.replace("  ", " ").split(" "))



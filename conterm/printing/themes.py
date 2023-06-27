from typing import TypedDict

class Theme(TypedDict):
    keyword: str
    object: str
    string: str
    number: str
    comment: str

DRACULA: Theme = {
    "keyword": "255,184,108",
    "object": "80,250,123",
    "string": "241,250,140",
    "number": "189,147,249",
    "comment": "98,114,164",
}


GRUVBOX: Theme = {
    "keyword": "167",
    "object": "214",
    "string": "142",
    "number": "175",
    "comment": "241",
}

ONE_DARK: Theme = {
    "keyword": "#C678DD",
    "object": "#61AFEF",
    "string": "#98C379",
    "number": "#E5C07B",
    "comment": "#ABB2BF",
}

NORD: Theme = {
    "keyword": "#5E81AC",
    "object": "#88C0D0",
    "string": "#A3BE8C",
    "number": "#B48EAD",
    "comment": "#434C5E",
}

class Catpuccin:
    MACCHIATO: Theme = {
        "keyword": "238,212,159",
        "object": "245,169,127",
        "string": "166,218,149",
        "number": "245,169,127",
        "comment": "128,135,162",
    }
    FRAPPE: Theme = {
        "keyword": "229,200,144",
        "object": "239,159,118",
        "string": "166,209,137",
        "number": "239,159,118",
        "comment": "131,139,167",
    }
    LATTE: Theme = {
        "keyword": "223,142,29",
        "object": "254,100,11",
        "string": "64,160,43",
        "number": "254,100,11",
        "comment": "140,143,161",
    }
    MOCHA: Theme = {
        "keyword": "249,226,175",
        "object": "250,179,135",
        "string": "166,227,161",
        "number": "250,179,135",
        "comment": "127,132,156",
    }

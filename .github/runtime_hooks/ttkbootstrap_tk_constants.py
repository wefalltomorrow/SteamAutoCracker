"""Runtime compatibility for SteamAutoCracker's `import ttkbootstrap as tk` alias.

ttkbootstrap provides Tk/ttk widgets but does not expose classic tkinter
constants such as BOTH, LEFT, END, NORMAL, or DISABLED at its package root.
Older SteamAutoCracker GUI code references those names through the `tk` alias.
PyInstaller loads this hook before the application so those references resolve
to the same string values tkinter itself uses.
"""

import ttkbootstrap as tk

_TK_CONSTANTS = {
    "END": "end",
    "NORMAL": "normal",
    "DISABLED": "disabled",
    "LEFT": "left",
    "RIGHT": "right",
    "BOTH": "both",
    "Y": "y",
}

for _name, _value in _TK_CONSTANTS.items():
    if not hasattr(tk, _name):
        setattr(tk, _name, _value)

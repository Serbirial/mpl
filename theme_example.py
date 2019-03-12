colors = {
    "other": "",
    "other2": "",
    "main": "",
    "main2": "",
    "volume": "",
    "volume2": "",
    "repeat": "",
    "repeat2": "",
    "keys": "",
    "keys2": "",
    "playing": "\033[01;34m",
    "playing2": "\033[00m",
    "time": "\033[01;32m",
    "time2": "\033[00m",
}



# Here is where the chars are inserted
"""
{theme.colors["other"]}     {cache["other"]}               {theme.colors["other2"]}
{theme.colors["main"]}      {cache["main"]}                {theme.colors["main2"]}
{theme.colors["volume"]}    Volume -> {cache["volume"]}    {theme.colors["volume2"]}
{theme.colors["repeat"]}    Repeating -> {cache["repeat"]} {theme.colors["repeat2"]}
{theme.colors["keys"]}      {cache["keys"]}                {theme.colors["keys2"]}
{theme.colors["playing"]}   {cache["playing"]}             {theme.colors["playing2"]}

{theme.colors["time"]} {cache["time"]} {theme.colors["time2"]}
"""
# key is inserted before
# key2 is inserted after

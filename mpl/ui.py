import os, sys
import textwrap



class MainUi:
    def __init__(self):
        pass

    def init_ui(self):
        if "enabled" in self.config["theme"] and self.config["theme"]["enabled"]==True and "colors" in self.config["theme"]:
            from colorama import init as init_color
            from colorama import Fore, Back, Style
            if os.name == "nt": init_color(convert=True)
            self.color_enable = True

    def print(self, *content, flush=False):
        if flush:sys.stdout.flush()
        sys.stdout.write(str(*content))

    def show_ui(self, cache=None):
        if cache is None:
            return False
        os.system('cls' if os.name == 'nt' else 'clear')
        # oh b o y   this is going to look bad
        if hasattr(self, "color_enable") and self.color_enable: # i need a better way to do this
            try:
                ui = f"""
{self.config["theme"]["colors"]["other"]}{cache["other"]} {self.config["theme"]["colors"]["other2"]}
{self.config["theme"]["colors"]["main"]}{cache["main"]} {self.config["theme"]["colors"]["main2"]}
{self.config["theme"]["colors"]["volume"]}Volume -> {cache["volume"]} {self.config["theme"]["colors"]["volume2"]}
{self.config["theme"]["colors"]["repeat"]}Repeating -> {cache["repeat"]} {self.config["theme"]["colors"]["repeat2"]}
{self.config["theme"]["colors"]["keys"]}{cache["keys"]} {self.config["theme"]["colors"]["keys2"]}
{self.config["theme"]["colors"]["playing"]}{cache["playing"]} {self.config["theme"]["colors"]["playing2"]}

{self.config["theme"]["colors"]["time"]}{cache["time"]}{self.config["theme"]["colors"]["time2"]}

    -> """
            except:
                self.color_enable = False
                ui = f'err: color theme error, please wait a second.'
        else:
            ui = f"""
{cache["other"]}
{cache["main"]}
Volume -> {cache["volume"]}
Repeating -> {cache["repeat"]}
{cache["keys"]}
{cache["playing"]}

{cache["time"]}

    -> """
        self.print(ui, flush=True)

    def reload_theme(self):
        import config
        color_theme = config.theme_import
        # does this even work.

        
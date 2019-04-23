import os, sys
import config
import textwrap

if config.themes:
	from colorama import init as init_color
	from colorama import Fore, Back, Style
	if os.name == "nt": init_color(convert=True)
	color_theme = config.theme_import

class MainUi:
	def __init__(self):
		pass

	def print(self, *content, flush=False):
		if flush:sys.stdout.flush()
		sys.stdout.write(str(*content))

	def show_ui(self, cache=None):
		if cache is None:
			return False
		os.system('cls' if os.name == 'nt' else 'clear')
		# oh b o y   this is going to look bad
		if color_theme: # i need a better way to do this
			ui = f"""
{color_theme.colors["other"] if config.themes is not None else None}{cache["other"]} {color_theme.colors["other2"] if config.themes is not None else None}
{color_theme.colors["main"] if config.themes is not None else None}{cache["main"]} {color_theme.colors["main2"] if config.themes is not None else None}
{color_theme.colors["volume"] if config.themes is not None else None}Volume -> {cache["volume"]} {color_theme.colors["volume2"] if config.themes is not None else None}
{color_theme.colors["repeat"] if config.themes is not None else None}Repeating -> {cache["repeat"]} {color_theme.colors["repeat2"] if config.themes is not None else None}
{color_theme.colors["keys"] if config.themes is not None else None}{cache["keys"]} {color_theme.colors["keys2"] if config.themes is not None else None}
{color_theme.colors["playing"] if config.themes is not None else None}{cache["playing"]} {color_theme.colors["playing2"] if config.themes is not None else None}

{color_theme.colors["time"]}{cache["time"]}{color_theme.colors["time2"]}

	-> {cache["_typed"]}"""
		else:
			ui = f"""
{cache["other"]}
{cache["main"]}
Volume -> {cache["volume"]}
Repeating -> {cache["repeat"]}
{cache["keys"]}
{cache["playing"]}

{cache["time"]}

	-> {cache["_typed"]}"""
		self.print(ui, flush=True)

	def reload_theme(self):
		pass
	

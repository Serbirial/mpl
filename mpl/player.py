import os, sys
import time, datetime

if os.name == 'nt':
	sys.stdout.write("Expect alot of errors from vlc...\n")
	time.sleep(2)
#	self.ui.print('Sorry windows is not supported, if you still want to try to get around the error comment out these lines\n')
#	self.ui.print('Exiting...\n')
#	time.sleep(6)
#	sys.exit(0)

import vlc, librosa
import sqlite3
import psutil

import threading
import asyncio

import config
from . import other, ui, uinp
import util
instr = """
Instructions:
	Press esc to stop
	Press space bar to pause (press once again to unpause)
"""
client_id = '495106015273025546'

class MainPlayer:
	vlc_instance = vlc.Instance()
	def __init__(self):
		self.ui = ui.MainUi
		self.other = other.Helper
		self.songs = self.other.get_songs()
		self.rpc = False
		if config.discord_rpc:
			try:
				self.rpc = True
				from pypresence import Presence as pr
				try:
					self.rpc_connection = pr(client_id,pipe=0)
					self.rpc_connection.connect()
					self.rpc_connection.update(large_image="mpl", details="Just loaded",state=f"Idle")
				except FileNotFoundError:
					self.ui.print("Discord is not open or not installed (you must have the client not the web version)")
					
					config.discord_rpc = False
					self.rpc = False
					time.sleep(2)
			except ImportError:
				self.ui.print("pypresence is not installed (pip install pypresence)")
				
				self.rpc = False
				time.sleep(2)
		self.uinp = uinp.KBHit()
		self.reset_terminal = self.uinp.set_normal_term()
		self.player = self.vlc_instance.media_player_new()
		self.paused = False
		self.cache = {
			"main": "Null - You should not see this at all",
			"playing": "Null - This is really bad",
			"time": "Null - If you see this somthing is not right",
			"other": "",
			"volume": "100",
			"repeat": "False",
			"keys": "",
			"repeat_cache": {
				"last_song": None
			}}
		self.input_loop = threading.Thread(target=self._input_loop)
		self.input_loop.daemon = True
		self.input_loop.name = 'Input Thread'
		self.playing = False
	def play(self, url):
		self.ui.print("\n")
		
		if not self.input_loop.is_alive():
			self.input_loop.start()
		song = url["path"]
		name = url["name"]
		self.ui.print("\033]2;Media player : Playing "+name+"\007")
		
		vlc_instance = self.vlc_instance
		player = self.player
		media  = vlc_instance.media_new(song)
		media.get_mrl()
		player.set_media(media)
		player.play()
		time.sleep(1)
		duration = player.get_length() / 1000
		now = duration
		duration_human = "%02d:%02d" % divmod(duration, 60)
		self.cache["main"] = self.songs
		self.cache["playing"] = "Current song is : "+name+" Length: "+duration_human
		self.cache["other"] = " 	Song Loaded!"
		if self.cache["repeat"]=="True":
			self.cache["other"] += " 	Song is looped"
		self.playing = True
		# The main player loop that updates the ui and check for user input
		while 1:
			if not self.paused:
				now -= 1
				duration_left = "%02d:%02d" % divmod(duration - now, 60)
				if now == 0 or 0 > now or not self.playing:
					self.cache["playing"] = 'Finished playing '+name+'\n\n'
					self.cache["time"] = "00:00"
					self.cache["other"] = " Finished... restarting"
					self.playing = False
					if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details="Finished playing "+name,state="00:00")
					time.sleep(0.4)
					player.stop()
					return self.clsprg()
				if self.paused is False: self.cache["time"] = f"Time left -> {duration_left}/{duration_human}"
				if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details=""+name+" Length: "+duration_human,state=f"{duration_left}/{duration_human}")
				self.ui.print_ui(self.cache)
				time.sleep(1)


	def _input_loop(self):
		""""forever loop that constantly check for input"""
		while True:
			if self.playing:
				c = self.uinp.getch()
				if c=="r":
					if self.cache["repeat"]=="False":
						self.cache["repeat"] = "True"
						pass
					elif self.cache["repeat"]=="True":
						self.cache["repeat"] = "False"
						self.cache['repeat_cache']["last_song"] = None
						pass
				elif c=="q":
					self.playing = False
					self.cache['repeat_cache']["last_song"] = None
				elif c=="p":
					self.ui.print_ui(self.cache)
					
					if self.player.is_playing():
						self.paused = True
						self.player.pause()
					else:
						self.paused = False
						self.player.play()
	def clsprg(self):
		"""Clear screen, print, Go"""
		os.system('cls' if os.name == 'nt' else 'clear')
		self.ui.print("\033]2;Media player : Idling\007")
		if self.cache['repeat'] == "True" and self.cache['repeat_cache']["last_song"] is not None:
			return self.play(self.other.get_song_from_id(self.cache['repeat_cache']["last_song"]))
		if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details="Idle",state=f"Idle")
		self.ui.print(self.songs)
		self.ui.print("\nPlease input a number next to the song you want to play")
		
		song = input("   -> ")
		if "exit" in song: # TODO: use a tuple ?
			self.exit()
		if "/repeat" in song:
			song = song.split(" /repeat")[0]
			if self.cache["repeat"]=="False":
				self.cache["repeat"] = "True"
			elif self.cache["repeat"]=="True":
				self.cache["repeat"] = "False"
				self.cache['repeat_cache']["last_song"] = None
		if "/refresh" in song:
			self.ui.print("Refreshing\n")
			self.songs = self.other.get_songs()
			time.sleep(1)
			self.ui.print("Refreshed songs")
			
			time.sleep(2)
			self.clsprg()
		get_song = self.other.get_song_from_id(song)
		if get_song is None:
			self.ui.print(" Not a valid song id\n")
			self.ui.print(" Or that song was not found")
			
			time.sleep(2)
			self.clsprg()
		elif get_song is not None:
			self.cache['repeat_cache']["last_song"] = str(song)
			return self.play(get_song)

	def exit(self): 
		sys.stdout.write("\n\nExiting... please wait")
		sys.exit(0)
		

def start():
	try:
		MainPlayer().clsprg()
	except KeyboardInterrupt:
		sys.stdout.write("\n\nExiting... please wait")
		import gc
		gc.collect()
		sys.exit(0)

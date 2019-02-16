import vlc
import sqlite3
import psutil
import librosa

import os
import sys
import multiprocessing
import time
import asyncio
import datetime

import config
from . import other
from . import ui
from . import uinp
import util
instr = """
Instructions:
	Press esc to stop
	Press space bar to pause (press once again to unpause)
"""
client_id = '495106015273025546'

class MainPlayer:
	def __init__(self):
		self.ui = ui.MainUi
		self.other = other.Helper
		self.songs = self.other.get_songs()
		self.rpc = False
		if config.discord_rpc:
			try:
				self.rpc = True
				from pypresence import Presence as pr
			except ImportError:
				print("pypresence is not installed (pip install pypresence)")
				time.sleep(2)
		self.uinp = uinp.KBHit()
		self.reset_terminal = self.uinp.set_normal_term()
		if self.rpc:
			try:
				self.rpc_connection = pr(client_id,pipe=0)
				self.rpc_connection.connect()
				self.rpc_connection.update(large_image="mpl", details="Just loaded",state=f"Idle")
			except FileNotFoundError:
				print("Discord is not open or not installed (you must have the client not the web version)")
				config.discord_rpc = False
				self.rpc = False
				time.sleep(2)

		self.vlc_instance = vlc.Instance()
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
		#self.player = self.play
	def play(self, url):
		print("\n")
		song = url["path"]
		name = url["name"]
		if os.name != "nt": print("\033]2;Media player : Playing "+name+"\007")
		vlc_instance = self.vlc_instance
		player = vlc_instance.media_player_new()
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
		time_left = "Play"
		# the while loop checks every x seconds if the song is finished.
		while time_left == "Play":
			if self.paused is False: now -= 1
			duration_left = "%02d:%02d" % divmod(duration - now, 60)
			if now == 0 or 0 > now:
				self.cache["playing"] = 'Finished playing '+name+'\n\n'
				self.cache["time"] = "00:00"
				self.cache["other"] = " Finished... restarting"
				time_left = "Stop"
				if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details="Finished playing "+name,state="00:00")
				time.sleep(0.4)
				self.clsprg()
				player.stop()
			if self.paused is False: self.cache["time"] = f"Time left -> {duration_left}/{duration_human}"
			if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details=""+name+" Length: "+duration_human,state=f"{duration_left}/{duration_human}")
			self.ui.print_ui(self.cache)
			if self.uinp.kbhit():
				c = self.uinp.getch()
				if c=="r":
					if self.cache["repeat"]=="False":
						self.cache["repeat"] = "True"
						self.cache["other"] = "Next song will loop"
						pass
					elif self.cache["repeat"]=="True":
						self.cache["repeat"] = "False"
						self.cache["other"] = "Next song will not loop"
						self.cache['repeat_cache']["last_song"] = None
						pass
				elif c=="q":
					player.stop()
					self.cache['repeat_cache']["last_song"] = None
					self.clsprg()
				elif c=="p":
					if player.is_playing():
						self.cache["playing"] = "Current song is : "+name+" Length: "+duration_human + " | Paused"
						self.paused = True
						player.pause()
					else:
						self.cache["playing"] = "Current song is : "+name+" Length: "+duration_human
						self.paused = False
						player.play()
			time.sleep(1)

	def clsprg(self):
		"""Clear screen, Print, Go"""
		os.system('cls' if os.name == 'nt' else 'clear')
		if os.name != "nt": print("\033]2;Media player : Idling\007")
		if self.cache['repeat'] == "True" and self.cache['repeat_cache']["last_song"] is not None:
			return self.play(self.other.get_song_from_id(self.cache['repeat_cache']["last_song"]))
		if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details="Idle",state=f"Idle")
		print(self.songs)
		print("Please input a number next to the song you want to play")
		song = input("   -> ")
		if "/repeat" in song:
			song = song.split(" /repeat")[0]
			if self.cache["repeat"]=="False":
				self.cache["repeat"] = "True"
				self.cache["other"] = "Next song will loop"
			elif self.cache["repeat"]=="True":
				self.cache["repeat"] = "False"
				self.cache["other"] = "Next song will not loop"
				self.cache['repeat_cache']["last_song"] = None
		if "/refresh" in song:
			print("Refreshing")
			self.songs = self.other.get_songs()
			time.sleep(1)
			print("Refreshed songs")
			time.sleep(2)
			self.clsprg()
		get_song = self.other.get_song_from_id(song)
		if get_song is None:
			print(" Not a valid song id")
			print(" Or that song was not found")
			time.sleep(2)
			self.clsprg()
		elif get_song is not None:
			self.cache['repeat_cache']["last_song"] = str(song)
			return self.play(get_song)

def start():
	try:
		MainPlayer().clsprg()
	except KeyboardInterrupt:
		print("\n\nExiting...")
		sys.exit(0)

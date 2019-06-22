import os, sys
import time, datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--single", help="play a single song", required=False)
parser.add_argument("-u", "--util", help="activate the util menu", action='store_true', required=False)

if os.name == 'nt':
    # Now supports windows, comes with a basket full of bugs.
    sys.stdout.write("You might get cache errors...\n")


import vlc, librosa
import sqlite3
import psutil, threading
import asyncio


from . import other, ui, uinp
from .helpers import youtube


# Id for the discord rpc.
client_id = '495106015273025546'


# TODO:
#	Improve on memory usage, kill the vlc instance and remake it every few songs?
#	Volume handling
#	Get someone to look over my horrible code
#	Better and faster way of printing the ui
#	Move from vlc if there is a better way of playing music (MUST BE FASTER AND EASIER TO DEAL WITH)

class MainPlayer(other.Helper,ui.MainUi):
    vlc_instance = vlc.Instance('-q') # Tries to stop the cache errors
    def __init__(self):
        super().__init__()
        self.check_config() # makes sure all the needed parts are there, if not then make them
        self.init_ui()
        if "prefpage" in self.config["main"]:
            self.songs = self.get_songs(self.config["main"]["prefpage"])
        else:
            self.songs = self.get_songs()
        self.rpc = False
        if self.config["main"]["discord_rpc"]:
            try:
                self.rpc = True
                from pypresence import Presence as pr
                try:
                    self.rpc_connection = pr(client_id,pipe=0)
                    self.rpc_connection.connect() 
                    self.rpc_connection.update(large_image=self.config["main"]["rpc_large_image"], details="Just loaded",state=f"Idle")
                except FileNotFoundError:
                    self.print("Discord is not open or not installed (you must have the client not the web version)", flush=True)
                    self.print("If the discord client is open and it still says this, check if you have another rpc (That might be the cause)\nOr restart discord", flush=True)
                    self.config["main"]["discord_rpc"] = False
                    self.rpc = False
                    time.sleep(2)
            except ImportError:
                self.print("pypresence is not installed (pip install pypresence)\n\n")
                self.rpc = False
                time.sleep(2)
        self.uinp = uinp.KBHit()
        self.reset_terminal = self.uinp.set_normal_term()
        self.player = self.vlc_instance.media_player_new()
        self.youtube = youtube.Youtube()
        self.paused = False
        self.playing = False
        self.cache = {
            "main": "Null - You should not see this at all",
            "playing": "Null - This is really bad",
            "time": "Null - If you see this somthing is not right",
            "other": "",
            "volume": "100",
            "repeat": "False",
            "keys": "",
            "repeat_cache": {
                "yt": False,
                "last_song": None
            },
            "lastchar": ""}
    def play(self, url):
        self.print("\n")
        song, name = url["path"], url["name"]
        if os.name != 'nt':
            self.print("\033]2;Media player : Playing "+name+"\007")
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
        self.cache["main"] = ''.join([x for x in self.songs]) if self.config["main"]["show_songs_while_playing"] else ''
        self.cache["playing"] = "Current song is : "+name+" ("+duration_human+")"
        self.cache["other"] = " 	Song Loaded!"
        if self.cache["repeat"]=="True":
            self.cache["other"] += " 	Song is looped"
        self.playing = True
        self.check_input_loop() # check if its dead, if it is remake the thread.
        # The main player loop that updates the ui and check for user input
        while 1:
            if not self.paused:
                now -= 1
                duration_left = "%02d:%02d" % divmod(duration - now, 60)
                self.show_ui(self.cache)
                if now == 0 or 0 > now or not self.playing:
                    self.cache["playing"] = 'Finished playing '+name+'\n\n'
                    self.cache["time"] = "00:00"
                    self.cache["other"] = " Finished... restarting"
                    self.playing = False
                    if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details="Finished playing "+name,state="00:00")
                    time.sleep(0.4)
                    player.stop()
                    if self.cache["repeat"]=="True" and self.cache['lastchar']!='q':
                        return self.play(self.cache['repeat_cache']['last_song']) 
                    else:
                        return
                if self.paused is False: self.cache["time"] = f"Time left -> {duration_left}/{duration_human}"
                if self.rpc is not False: self.rpc_connection.update(large_image="mpl", details=""+name+" Length: "+duration_human,state=f"{duration_left}/{duration_human}")
                time.sleep(1)
            elif self.paused: time.sleep(0.5) # not the best way to handle pauses but it works

    def check_input_loop(self):
        if not hasattr(self, 'input_loop'):
            self.input_loop = threading.Thread(target=self._input_loop)
            self.input_loop.daemon = True
            self.input_loop.name = 'Input Thread'
            self.input_loop.start()			
        if not self.input_loop.is_alive():
            self.input_loop = threading.Thread(target=self._input_loop)
            self.input_loop.daemon = True
            self.input_loop.name = 'Input Thread'
            self.input_loop.start()
            return False

    def _input_loop(self):
        """"forever loop that constantly check for input"""
        while True:
            if not self.playing:
                break # if the music has stopped break
            elif self.playing:
                try:
                    c = self.uinp.getch()
                    self.cache["lastchar"] = c
                    if c=="r":
                        if self.cache["repeat"]=="False":
                            self.cache["repeat"] = "True"
                        elif self.cache["repeat"]=="True":
                            self.cache["repeat"] = "False"
                            self.cache['repeat_cache']["last_song"] = None
                    elif c=="q":
                        self.playing = False
                        self.cache['repeat_cache']["last_song"] = None
                    elif c=="p":
                        self.show_ui(self.cache)
                        if self.player.is_playing():
                            self.paused = True
                            self.player.pause()
                        else:
                            self.paused = False
                            self.player.play()
                except UnicodeDecodeError:
                    if self.playing:
                        pass
                    elif not self.playing:
                        break # break the loop, we are not playing, the thread will be remade next time music plays
    def clsprg(self):
        """Clear screen, print, Go"""
        os.system('cls' if os.name == 'nt' else 'clear')
        if os.name != 'nt':
            self.print("\033]2;Media player : Idling\007")
        if self.cache['repeat'] == "True" and self.cache['repeat_cache']["last_song"] is not None:
            return self.play(self.cache['repeat_cache']['last_song'])
        if self.rpc: self.rpc_connection.update(large_image="mpl", details="Idle",state=f"Idle")
        self.print(''.join([x for x in self.songs]))
        self.print("\nPlease input a number next to the song you want to play")
        
        song = input("   -> ")
        if "exit" in song: # TODO: use a tuple ?
            self.exit()
        if "help" in song:
            self.print(f" \
(Config file is in {pathlib.Path.home()})/.config/mpl/config.json \
When selecting a song:\n \
    /repeat:\n    Repeat the song you plan on playing ex: 2 /repeat\n \
    /help:\n    Shows this message\n \
    /refresh:\n    Reloads the songs (for database changes)\n \
    /pages:\n    Shows how many pages (and songs) there are total\n \
    /page=page_number:\n    Changes the current page, numbers only (do /page=all to not have a 5 song per page limit, or /page=1,2 to mix them)\n \
    /ytsearch=url_or_name:\n    Searches youtube for the url and plays it \
When playing a song:\n \
    r:\n    Turn repeat on/off\n \
    q:\n    quit the current song\n \
    p:\n    Pause the current songs", flush=True)
            input("\nPress enter to continue")
            return self.clsprg()
        if "/repeat" in song:
            song = song.split(" /repeat")[0]
            if self.cache["repeat"]=="False":
                self.cache["repeat"] = "True"
            elif self.cache["repeat"]=="True":
                self.cache["repeat"] = "False"
                self.cache['repeat_cache']["last_song"] = None
        elif '/ytsearch=' in song:
            song = song.split('/ytsearch=')[1]
            self.print(f"\nDownloading {song} please wait...", flush=True)
            youtube = self.youtube.search_and_download(song)
            temp = {
                'name': f'{youtube.title} By {youtube.uploader}',
                'path': f'{youtube.path}'
            }
            self.cache['repeat_cache']["last_song"] = temp
            self.cache['repeat_cache']["yt"] = True
            self.print(f'\nPlaying {temp["name"]}', flush=True)
            return self.play(temp)

        elif '/pages' in song:
            self.print(f'{self.pages()}', flush=True)
            input("\nEnter to continue ")
            self.clsprg()
        elif '/page=' in song:
            pageu = song.split('/page=')[1]
            if ',' in pageu:
                songs = []
                for x in pageu.split(','):
                    songs += self.get_songs(page=int(x))
                self.songs = songs
                self.clsprg()
            self.print(f"Changing page to {pageu}", flush=True)
            if 'all' in pageu:
                self.songs = self.get_songs(page=None)
            elif 'dir' in pageu:
                self.songs = self.get_songs(page="dir")
            else:
                self.songs = self.get_songs(page=int(pageu))
            self.print("Refreshing...\n", flush=True)
            self.clsprg()
        elif "/refresh" in song:
            self.print("Refreshing\n", flush=True)
            self.songs = self.get_songs()
            self.print("Refreshed songs\n")
            time.sleep(2)
            self.clsprg()
        get_song = self.get_song_from_id(song)
        if get_song is None:
            self.print(" Not a valid song id", flush=True)
            self.print(" Or that song was not found", flush=True)

            self.print(f'\n({song})\n')
            
            time.sleep(2)
            self.clsprg()
        elif get_song is not None:
            self.cache['repeat_cache']["last_song"] = get_song
            return self.play(get_song)



    def exit(self): 
        sys.stdout.write("\n\nExiting... please wait\n")
        sys.exit(0)
        

def main():

    if os.name != "nt": print("\033]2;Media player : idle\007")

    mp = MainPlayer()

    args = parser.parse_args()
    if args.single:
        try:
            name = args.single.split("/")
            name = name[len(name)-1]
            data = {'path': args.single ,'name': f'{name} by ?'}
            mp.cache['repeat_cache']["last_song"] = data
            mp.play(data)
        except KeyboardInterrupt:
            mp.paused = True
            mp.player.pause() 
            sys.stdout.write("\n\nExiting... please wait\n")
            sys.exit(0)
    elif args.util:
        from .helpers.utilmenu import repl
        repl() 
    else:
        try:
            while True:
                mp.clsprg()
        except KeyboardInterrupt:
            sys.stdout.write("\n\nExiting... please wait\n")
            sys.exit(0)


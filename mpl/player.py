import os, sys
import time 
import argparse
import pathlib

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--single", help="Play a single song", required=False)
parser.add_argument("-r", "--repeat", help="Activate repeat mode", action='store_true', required=False)
parser.add_argument("-u", "--util", help="Activate the util menu", action='store_true', required=False)


import vlc, librosa
import threading


from . import other, ui, uinp
from .helpers import youtube_helper as youtube


# Id for the discord rpc.
client_id = '495106015273025546'


# TODO:
#	Improve on memory usage, kill the vlc instance and remake it every few songs?
#	Volume handling
#	Get someone to look over my horrible code
#	Better and faster way of printing the ui
#	Move from vlc if there is a better way of playing music (MUST BE FASTER AND EASIER TO DEAL WITH)

# BUG:
#   With /playlist it will *always* stop after the 2nd, no known way to fix, no known cause  (HIGH PRIO)
#   Sometimes you need to hit enter to get input read when a song is playing                (LOW PRIO / DONT CARE) 


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
        if self.config["main"]["discord_rpc"]==True:
            try:
                self.rpc = True
                from pypresence import Presence as pr
                try:
                    self.rpc_connection = pr(client_id,pipe=0)
                    try:
                        self.rpc_connection.connect() 
                    except ConnectionRefusedError:
                        self.print("RPC didnt connect...\n", flush=True)
                        self.rpc = False
                    else:
                        self.rpc_connection.update(large_image=self.config["main"]["rpc_large_image"], details="Just loaded",state=f"Idle")
                except FileNotFoundError:
                    self.print("Discord is not open or not installed (you must have the client not the web version)\nIf the discord client is open and it still says this, check if you have another rpc (That might be the cause), Or restart discord", flush=True)
                    self.config["main"]["discord_rpc"] = False
                    self.rpc = False
                    time.sleep(2)
            except ImportError:
                self.print("pypresence is not installed (pip install pypresence)\n\n")
                self.rpc = False
                time.sleep(2)
        self.uinp = uinp.KBHit
        self.uinp_ob = None
        self.reset_terminal = self.uinp.set_normal_term
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
            "playlist": "False",
            "keys": "",
            "repeat_cache": {
                "last_song": None
            },
            "playlist_cache": {
                "songs": []
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
        while 1:
            if not self.paused:
                now -= 1
                self.cache["time"] = f"Time left -> {'%02d:%02d' % divmod(duration - now, 60)}/{duration_human}"
                if now == 0 or 0 > now or not self.playing:
                    self.cache["playing"] = 'Finished playing '+name+'\n\n'
                    self.cache["time"] = "00:00"
                    self.cache["other"] = " Finished... restarting"
                    self.playing = False
                    if self.rpc is not False: self.rpc_connection.update(large_image=self.config["main"]["rpc_large_image"], details="Finished playing "+name,state="00:00")
                    time.sleep(0.4)
                    player.stop()
                    self.reset_terminal(self.uinp_ob)
                    if self.cache["repeat"]=="True" and self.cache['repeat_cache']['last_song']!=None:
                        return self.play(self.cache['repeat_cache']['last_song']) 
                    else:
                        return
                if self.rpc is not False: self.rpc_connection.update(large_image=self.config["main"]["rpc_large_image"], details=name,state=f"{'%02d:%02d' % divmod(duration - now, 60)}/{duration_human}/{duration_human}")
                self.show_ui(self.cache)
                time.sleep(1)
            elif self.paused: time.sleep(0.5) # not the best way to handle pauses but it works

    def check_input_loop(self):
        if not hasattr(self, "input_loop") or not self.input_loop.is_alive():
            self.input_loop = threading.Thread(target=self._input_loop)
            self.input_loop.daemon = True
            self.input_loop.name = 'Input Thread'
            self.input_loop.start()
            return False

    def _input_loop(self):
        """"forever loop that constantly check for input"""
        uinp = self.uinp()
        self.uinp_ob = uinp
        while self.playing:
            try:
                c = uinp.getch()
                self.cache["lastchar"] = c
                if c=="r":
                    if self.cache["repeat"]=="False":
                        self.cache["repeat"] = "True"
                        self.cache["other"] += " 	Song is now looped!"
                    elif self.cache["repeat"]=="True":
                        self.cache["repeat"] = "False"
                        self.cache["other"] = " 	Song Loaded!"
                elif c=="q":
                    self.cache["repeat"] = "False"
                    self.cache["repeat_cache"]["last_song"] = None
                    self.playing = False
                elif c=="p":
                    self.show_ui(self.cache)
                    if self.player.is_playing():
                        self.paused = True
                        self.player.pause()
                    else:
                        self.paused = False
                        self.player.play()
                elif c=="c":
                    self.cache["playlist_cache"]["songs"].clear()
                    self.cache["playlist"] = "False"
                time.sleep(0.3) # dont kill the cpu
            except UnicodeDecodeError:
                pass
        #c = None
        # return c # :weary: python 3.8 = return c := None

    def playlist_next(self):
        song = self.cache["repeat_cache"]["last_song"] = self.cache["playlist_cache"]["songs"][0]
        self.cache["playlist_cache"]["songs"].remove(self.cache["playlist_cache"]["songs"][0])
        self.play(song)

    def clear(self):
        """Clear the screen, and make sure it actually does it""" # fucking bugs made me do this ree
        self.print("\n"*50)
        os.system('cls' if os.name == 'nt' else 'clear')

    def clsprg(self):
        """Clear screen, print, Go"""
        if self.rpc: self.rpc_connection.update(large_image="mpl", details="Idle",state=f"Idle")
        if os.name != 'nt':
            self.print("\033]2;Media player : Idling\007")
        if self.cache['repeat'] == "True" and self.cache['repeat_cache']["last_song"] is not None:
            return self.play(self.cache['repeat_cache']['last_song'])
        elif self.cache["playlist"]=="True":
            self.playlist_next()
        self.clear()
        self.print(''.join([x for x in self.songs]))
        self.print("\nPlease input a number next to the song you want to play")
        
        song = input("   -> ")
        if "exit" in song: # TODO: use a tuple ?
            self.exit()
        if "help" in song:
            self.print(f"""
(Config file is in {pathlib.Path.home()}/.config/mpl/config.json)\n
When selecting a song:\n
    /repeat: Repeat the song you plan on playing ex: 2 /repeat\n
    /help: Shows this message\n
    /refresh: Reloads the songs (for database changes)\n
    /pages: Shows how many pages (and songs) there are total\n
    /page=page_number: Changes the current page, numbers only (do /page=all to not have a 5 song per page limit, or /page=1,2 to mix them)\n
    /ytsearch=url_or_name: Searches youtube for the url and plays it\n
When playing a song:\n
    r: Turn repeat on/off\n
    q: quit the current song\n
    p: Pause the current songs\n""", flush=True)
            input("\nPress enter to continue")
            return self.clsprg()
        if "/queue=" in song:
            self.cache["playlist"] = "True"
            for song_id in song.split("/queue=")[1].split(","):
                song_info = self.get_song_from_id(song_id)
                if song_info is None:
                    self.print(f"{song_id} is not a song id, passing", flush=True)
                else:
                    self.cache["playlist_cache"]["songs"].append(song_info)
            self.print("\n\nI will play:\n"+'\n'.join([x['name'] for x in self.cache['playlist_cache']['songs'] if x is not None ])+"\n")
            if input("! to quit, enter to continue")!="!":
                return self.playlist_next()
            else:
                return self.cache["playlist_cache"]["songs"].clear()
        elif any(x in song for x in ["/repeat", "/r"]):                     # "it just works"
            song = song.split(f" {'/r' if '/r' in song else '/repeat'}")[0] #                 - todd howard
            if self.cache["repeat"]=="False":
                self.cache["repeat"] = "True"
            elif self.cache["repeat"]=="True":
                self.cache["repeat"] = "False"
                self.cache['repeat_cache']["last_song"] = None
        elif '/ytsearch=' in song:
            song = song.split('/ytsearch=')[1]
            self.print(f"\nDownloading {song} please wait...", flush=True)
            song = self.youtube.search_and_download(song)
            temp = {
                'name': f'{song.title} By {song.uploader}',
                'path': f'{song.path}'
            }
            self.cache['repeat_cache']["last_song"] = temp
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
                return self.clsprg()
            self.print(f"Changing page to {pageu}", flush=True)
            if 'all' in pageu:
                self.songs = self.get_songs(page=None)
            else:
                self.songs = self.get_songs(page=pageu)
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
        else:
            self.cache['repeat_cache']["last_song"] = get_song
            return self.play(get_song)



    def exit(self):
        self.paused = True
        self.player.pause()
        if hasattr(self, "uinp_ob") and self.uinp_ob != None:
            self.reset_terminal(self.uinp_ob)
        sys.stdout.write("\n\nExiting... please wait\n")
        sys.exit(0)
        

def main():
    if os.name == 'nt':
        sys.stdout.write("This will not work... You can try though\n")
        input("Press enter to continue")

    else: print("\033]2;Media player : idle\007")

    mp = MainPlayer()
    args = parser.parse_args()
    if args.repeat:
        mp.cache["repeat"] = "True"
        pass
    if args.single:
        try:
            name = args.single.split("/")
            name = name[len(name)-1]
            data = {'path': args.single ,'name': f'{name.replace("_", " ")} by Local'}
            mp.cache['repeat_cache']["last_song"] = data
            # NOTE:
            #      Add youtube support later
            mp.play(data)
        except KeyboardInterrupt:
            mp.exit()
    elif args.util:
        from .helpers.utilmenu import repl
        repl() 
    else:
        try:
            while True:
                mp.clsprg()
        except KeyboardInterrupt:
            mp.exit()

# Psuedo was here
    # wolf was here
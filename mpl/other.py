import sqlite3
import json
import pathlib, librosa

class Helper:
    def __init__(self):
        self.check_db()


    def check_config(self):
        home = pathlib.Path.home()
        config_path = home.joinpath('.config/mpl')
        if not config_path.exists():
            config_path.mkdir()
        if not config_path.joinpath('config.json').is_file():
            with open(f"{config_path}/config.json", "w+") as f:
                data = {
                    "main": { "discord_rpc": False, "rpc_large_image": "mpl", "show_songs_while_playing": False, "dir": [f"{home}/Music"]},
                    "theme": { "enabled": False, "colors": {
                        "other": "", "other2": "", "main": "", "main2": "", "volume": "", "volume2": "",
                        "repeat": "", "repeat2": "", "keys": "", "keys2": "", "playing": "\033[01;34m", "playing2": "\033[00m",
                        "time": "\033[01;32m", "time2": "\033[00m", "input_arrow": "\033[01;34m", "input_arrow2": "\033[00m",}}}
            
                json.dump(data, f, indent=4)
        else:
            with open(f"{config_path}/config.json", "r") as f:
                data = json.load(f)
        self.config = data

    def check_db(self):
        con = sqlite3.connect(f'{pathlib.Path.home().joinpath(".config/mpl")}/database.db')
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS songs (song TEXT, author TEXT, length TEXT, id INT, path TEXT, page INT)")
        con.commit()

    def pages(self, num=False):
        con = sqlite3.connect(f'{pathlib.Path.home().joinpath(".config/mpl")}/database.db')
        cur = con.cursor()
        pages = cur.execute("SELECT page FROM songs").fetchall()
        if not num:
            string = f'There are {len(set(pages))} pages and {len(pages)} songs'
        elif num is True:
            return len(set(pages))
        con.close()
        return string

    def get_songs(self, page=0):
        returned = []
        con = sqlite3.connect(f'{pathlib.Path.home().joinpath(".config/mpl")}/database.db')
        cur = con.cursor()  # handles requests made to the database
        # check for songs
        from audioread.exceptions import NoBackendError
        if page=="dir":
            if "dir" in self.config["main"]:
                for dir in self.config["main"]["dir"]:
                    realdir = pathlib.Path(dir)
                    print(f'\nSearching {dir}/{realdir}')
                    for file in realdir.iterdir():
                        print(f'Is {file} valid? checking')
                        try:
                            librosa.core.get_duration(filename=file)
                            returned.append(str(file)+"\n")
                        except EOFError:
                            pass
                        except NoBackendError:
                            pass
                if len(returned)==0:
                    return ["No songs found in the given dirs"]
            else:
                return ["Dirs not found, edit your config"]
            return returned
        if page is None:
            rows = cur.execute(
                'SELECT song,author,length,id FROM songs').fetchall()
            if len(rows) == 0:
                returned.append("No songs found")
            for song, author, length, id in cur.execute(
                    'SELECT song,author,length,id FROM songs'):
                returned.append(f'{id} -> {song} - {author}: {length}\n')
            con.close()
            return returned
        elif type(page) == int:
            rows = cur.execute(
                'SELECT song,author,length,id FROM songs WHERE page=?', (page,)).fetchall()
            if len(rows) == 0:
                returned.append("No songs found")
            for song, author, length, id in cur.execute(
                    'SELECT song,author,length,id FROM songs WHERE page=?', (page,)):
                returned.append(f'{id} -> {song} - {author}: {length}\n')
            con.close()
            return returned

    def get_song_from_id(self, id):
        con = sqlite3.connect(f'{pathlib.Path.home().joinpath(".config/mpl")}/database.db')
        cur = con.cursor()  # handles requests made to the database
        cur.execute('SELECT * FROM songs WHERE id=?', (id, ))
        returned = cur.fetchone()
        cur.execute('SELECT * FROM songs')
        rows = cur.fetchall()
        if len(rows) == 0:
            return None
        elif len(rows) != 0:
            try:
                dictr = {
                    "name": returned[0] + " by " + returned[1],
                    "path": returned[4]
                }
                return dictr
            except:
                return None
        con.close()

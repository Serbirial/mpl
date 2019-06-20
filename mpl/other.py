import sqlite3


class Helper:
    def __init__(self):
        pass

    def pages(self, num=False):
        con = sqlite3.connect('database.db')
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
        con = sqlite3.connect('database.db')
        cur = con.cursor()  # handles requests made to the database
        # check for songs
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
        con = sqlite3.connect('database.db')
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

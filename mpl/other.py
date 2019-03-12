import sqlite3


class Helper:
    def get_songs():
        returned = ''
        con = sqlite3.connect('database.db')
        cur = con.cursor()  # handles requests made to the database
        # check for songs
        cur.execute('SELECT song,author,length,id FROM songs')
        rows = cur.fetchall()
        if len(rows) != 0:
            pass
        elif len(rows) == 0:
            returned += "No songs found"
        for song, author, length, id in cur.execute(
                'SELECT song,author,length,id FROM songs'):
            returned += f'{id} -> {song} - {author}: {length}\n'
        con.close()
        return returned

    def get_song_from_id(id):
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

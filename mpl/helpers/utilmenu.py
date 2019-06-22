import sqlite3
import os, sys
from os import listdir, system
import subprocess
import time
import vlc
import re
import librosa
import pathlib


def manually_insert_song():
    home = pathlib.Path.home()
    music = home.joinpath("Music")
    con = sqlite3.connect(f'{home.joinpath(".config/mpl")}/database.db')
    cur = con.cursor()
    perpage = 5
    print(f'I will search for music in {home}/Music')
    for file in listdir(f'{home}/Music'):
        if file.startswith('.'): pass
        else:
            try:
                cur.execute('SELECT path FROM songs WHERE path=?',(f'{music}/{file}',))
                rows = cur.fetchall()
                if len(rows) != 0:
                    print("This song is already in the database ", file)
                    pass
                elif len(rows) == 0:
                    name = input("song name for "+file+" > ")
                    author = input("author for "+file+" > ")
                    try:
                        length = get_duration(f"{music}/{file}")
                    except FileNotFoundError:
                        print("Got a `FileNotFound`, maybe it was avconv?")
                        print("Stopping")
                        exit(0)
                    returned = cur.execute("SELECT * FROM songs ORDER BY CAST(id as INTEGER) DESC").fetchone()
                    try:
                        id_ = int(returned[3]) + 1
                    except TypeError:
                        id_ = 1
                    print("Setting page...")
                    startpage = cur.execute('SELECT page FROM SONGS ORDER BY CAST(page as INTEGER) DESC').fetchone()
                    if not startpage is None:
                        currentpage = int(startpage[0])
                    else:
                        currentpage = 0
                    songsinpage = len(cur.execute('SELECT page FROM SONGS WHERE page=? ORDER BY CAST(page as INTEGER)',(currentpage,)).fetchall())
                    if songsinpage >= perpage:	
                        print('PAGES LARGER THAN 5 (',str(songsinpage), ')')
                        currentpage += 1
                        print('NEW PAGE (', currentpage,')') 
                    print(f"{name} - {author} - {length} Id {id_}")
                    print(f"Name -> {name} Author -> {author} Length -> {length} Id -> {id_}")
                    print("Is this correct?")
                    input("Press enter to pass (CTRL+C to stop)")
                    cur.execute('INSERT INTO songs VALUES (?,?,?,?,?,?)', (str(name), str(author), str(length), str(id_), f'{music}/{file}', str(currentpage)))
                    con.commit()
                    pass
            except EOFError: print("Not a valid audio file"); pass
    con.close()

def get_duration(url):
        duration = librosa.core.get_duration(filename=url) # Raises EOFError if it is not a valid audio file
        duration_human = "%02d:%02d" % divmod(duration, 60)
        return str(duration_human)

def mass_download(urls):
    """wow this is broken - pls nerf"""
    home = pathlib.Path.home()
    music = home.joinpath('Music')
    for url in urls:
        print("Downloading ", url)
        system(f"youtube-dl -o '{music}/%(title)s.%(ext)s' -x '{url}'")

def page_db():
    con = sqlite3.connect(f'{pathlib.Path.home().joinpath(".config/mpl")}/database.db')
    cur = con.cursor()
    PAGE = 0
    CURRENT = 0
    for song,author,id in cur.execute("SELECT song,author,id FROM songs").fetchall():
        CURRENT += 1
        if CURRENT >= 10:
            PAGE += 1
        print(f'{song} - {author} ({id}) {CURRENT} INTO THE DB NEW PAGE {PAGE}')
        cur.execute('UPDATE songs SET page = ? WHERE id=?', (PAGE, id))
    con.commit()
    con.close()

def repl():
    while 1:
        a = input("1 - add new songs to database\n2 - mass download urls (the audio from urls\n3 - quit\n ->")
        if "1" in a:
            manually_insert_song()
        elif "2" in a:
            print("Please paste the urls (seperated by a space) ->")
            urls = input()
            urlss = []
            split = urls.split(" ")
            for url in split:
                urlss.append(url)
            print(urlss)
            input("press enter to continue")
            mass_download(urlss)
        elif '3' in a:
            break
        elif '4' in a:
            page_db()
        else: pass

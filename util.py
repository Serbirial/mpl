import sqlite3
from os import listdir, system
import subprocess
import time
import vlc
import re
import librosa
from pathlib import Path

# con.execute('CREATE TABLE songs (song,author,length,id,path)')
def get_songs():
	returned = ''
	con = sqlite3.connect('database.db')
	cur = con.cursor() # handles requests made to the database
	# check for songs
	cur.execute('SELECT song,author,length,id FROM songs')
	rows = cur.fetchall()
	if len(rows) != 0:
		pass
	elif len(rows) == 0:
		returned += "No songs found"
	for song,author,length,id in cur.execute('SELECT song,author,length,id FROM songs'):
		returned += f'{id} -> {song} - {author}: {length}\n'
	con.close()
	return returned

def get_song_from_id(id):
	con = sqlite3.connect('database.db')
	cur = con.cursor() # handles requests made to the database
	cur.execute('SELECT * FROM songs WHERE id=?', (id,))
	returned = cur.fetchone()
	cur.execute('SELECT * FROM songs')
	rows = cur.fetchall()
	if len(rows) == 0:
		return None
	elif len(rows) != 0:
		try:
			dictr = {
			"name": returned[0] +" by "+ returned[1],
			"path": returned[4]}
			return dictr
		except:
			return None
	con.close()


def manually_insert_song():
	con = sqlite3.connect('database.db')
	cur = con.cursor()
	for file in listdir('songs'):
		cur.execute('SELECT path FROM songs WHERE path=?',("./songs/"+file,))
		rows = cur.fetchall()
		if len(rows) != 0:
			print("This song is already in the database ", file)
			pass
		elif len(rows) == 0:
			name = input("song name for "+ file+" > ")
			author = input("author for "+ file+" > ")
			length = get_duration("./songs/"+file)
			cur.execute("SELECT * FROM songs ORDER BY CAST(id as INTEGER) DESC")
			returned = cur.fetchone()
			try:
				id_ = int(returned[3]) + 1
			except TypeError:
				id_ = 1
			print(f"{name} - {author} - {length} Id {id_}")
			qui = input("Press ! to save > ")
			if "!" in qui:
				print(f"{name} - {author} - {length} {id_}")
				print("Is this correct?")
				print("5 seconds to force quit (ctrl+c) or i will save")
				time.sleep(5)

				cur.execute('INSERT INTO songs VALUES (?,?,?,?,?)', (str(name), str(author), str(length), str(id_), str("./songs/"+file),))
				con.commit()
				pass

	con.close()


def get_duration(url):
		duration = librosa.core.get_duration(filename=url)
		duration_human = "%02d:%02d" % divmod(duration, 60)
		return str(duration_human)

def update_already_done():
	con = sqlite3.connect('database.db')
	cur = con.cursor() # handles requests made to the database
	id_ = 1
	strong = ""
	for path,id in cur.execute("SELECT path,id FROM songs"):
		if int(id) != int(id_): pass
		elif int(id) == id_:
			strong += path + "\n"
			id_ += 1
	with open("tmp.txt", "w") as f: f.write(strong)
	with open("tmp.txt", "r") as f:
		for line in f:
			if line != "" or " " and "\n":
				line = line.replace("\n", "")
				cur.execute("INSERT INTO already_done_paths VALUES(?)", (line,))
				print(line)
	con.commit()
	con.close()

def mass_download(urls):
	"""wow this is broken - pls nerf"""
	for url in urls:
		print("Downloading ", url)
		system(f"youtube-dl -o './songs/%(title)s.%(ext)s' -x '{url}'")

if __name__ == "__main__":
	a = input("1 - add new songs to database\n2 - mass download urls (the audio from urls\n ->")
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
	else: print("wrong")
import spotipy

# Currently not supported


class Spotify(object):
	def __init__(self):
		self.spotify = spotipy.Spotify()

	def search(self, song, limit=1):
		return self.spotify.search(song, limit=limit)
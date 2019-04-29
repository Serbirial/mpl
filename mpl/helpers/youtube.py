import os, sys

try:
	import youtube_dl
except ImportError:
	sys.stdout.write("\n\nYOUTUBE-DL IS NOT INSTALLED\n")
	sys.exit(0)
	

youtube_dl_o = {
	'format': 'bestaudio/best',
	'outtmpl': 'songs/%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

class Video(object):
	def __init__(self, ytdlobj, search, download):
		''' Returns video result object when given a url'''
		with ytdlobj:
			result = ytdlobj.extract_info(
				search,
				download=False # just want to extract the info for now
			)
			if 'entries' in result:
				result = result['entries'][0]
			self.title = result['title']
			self.video_url = result["webpage_url"]
			self.uploader = result["uploader"]
			self.thumbnail = result["thumbnail"]
			self.views = result['view_count']
			self.duration = "%02d:%02d" % divmod(result['duration'], 60)
			self.rating = int(result['like_count']) - int(result['dislike_count'])
			if download:
				ytdlobj.download([self.video_url])
				self.path = ytdlobj.prepare_filename(result)


class Youtube:
	def __init__(self):
		self.yt = youtube_dl.YoutubeDL(youtube_dl_o)

	def get_info(self, search, download=False):
		return Video(ytdlobj=self.yt, search=search, download=download)


	def search_and_download(self, search):
		try:
			info = self.get_info(search=search, download=True)
			return info
		except Exception as e:
			raise e

if __name__ == "__main__":
	ytin = Youtube()
	objs = {
	"1": ytin.get_info,
	"2": ytin.search_and_download 
	}
	inp = input(">>>")
	if inp in objs:
		inp2 = input("url\n >>>")
		video = objs[inp](inp2)
		print(
			f'Video name     : {video.title}\n',
			f'Video duration : {video.duration}\n'
			f'Video uploader : {video.uploader}\n',
			f'Video Views    : {video.views}\n',
			f'Video rating   : {video.rating}\n',
			f'Video url      : {video.video_url}'

		)
		if hasattr(video, 'path'):
			print(f'VLC PATH : {video.path}\n')
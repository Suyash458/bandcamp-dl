'''
1. Take command line arguments. //Done
2. Change directory. //Done
3. Validate file name. //Done
4. Check existing files. //Done
5. Make it robust.
6. Improve progressbar.
'''

import re,json,requests,HTMLParser
from bs4 import BeautifulSoup
import sys,os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC,APIC


class Downloader():
	
	def __init__(self,url = None,dirname = None):
		self.url = url
		self.dirname = dirname
		
	def getData(self,soup):	
		content = soup.find('meta',{'name':'Description'})['content']		
		JSdata = soup.findAll('script')
		var = re.search('trackinfo.*}]',str(JSdata)).group()[11::]
		tracks = json.loads(var)
		artist = re.search('artist: .*"',str(JSdata)).group()[9:-1]
		album = re.search('album_title.*"',str(JSdata)).group().split(':')[1][2:-1]
		year = content.strip()[-1:-5:-1][::-1]
		metadata = {'artist' : artist,
					'album' : album,
					'year' : year}
		return metadata,tracks
	
	def getAlbumArt(self,soup,parser):
		JSdata = soup.findAll('script')
		albumArtURL = re.search('artFullsizeUrl.*"',str(JSdata)).group()[17:-1]
		print "Downloading Album Art."
		format = albumArtURL.split('.')[-1]
		self.getFile('album-art.' + format,parser.unescape(albumArtURL))
		
	def progressBar(self,done,file_size):
		percentage = ((done/file_size)*100)
		sys.stdout.flush()
		sys.stdout.write('\r')	
		sys.stdout.write('[' + '#'*int((percentage/5)) + ' '*int((100-percentage)/5) + '] ')
		sys.stdout.write('%.2f' % percentage + ' %')
				
	def getFile(self,filename,link):
		print "Connecting to stream..."
		response = requests.get(str(link), stream=True)
		print "Response: "+ str(response.status_code)		
		file_size = float(response.headers['content-length'])
		filename = re.sub('[\/:*"?<>|]','_',filename)
		if(os.path.isfile(filename)):
			if os.path.getsize(filename) >= long(file_size):
				print filename + " already exists, skipping."
				return new_filename
			else:
				print "Incomplete download, restarting."
		print "File Size: " + '%.2f' % (file_size/(1000**2)) + ' MB'
		print "Saving as: " + filename
		done = 0
		with open(filename,'wb') as file:
			for chunk in response.iter_content(chunk_size=1024):
				if chunk:
					file.write(chunk)
					file.flush()
					done += len(chunk)
					self.progressBar(done,file_size)
		return new_filename
		print "\nDownload complete."
	
	def tagFile(self,filename,metadata,track):
		audio = MP3(filename,ID3=ID3)
		try:
			audio.add_tags()
		except:
			pass
		with open('album-art.jpg','rb') as file:
			image = file.read()
		audio.tags.add(
			APIC(
				encoding=3,
				mime='image/jpeg',
				type=3,
				desc=u'Cover',
				data=image
			)
		)
		audio.tags["TIT2"] = TIT2(encoding=3, text=track['title'])
		audio.tags["TALB"] = TALB(encoding=3, text=metadata['album'])
		audio.tags["TPE1"] = TPE1(encoding=3, text=metadata['artist'])
		audio.tags["TDRC"] = TDRC(encoding=3, text=unicode(metadata['year']))
		audio.save()
				
	def Download(self):
		if self.url is None:
			print "No URL entered."
			return
		elif 'bandcamp' not in self.url:
			print "Invalid URL"
			return
		try:
			if self.dirname is not None:
				os.chdir(str(self.dirname))
			print "Connecting ... "
			response = requests.get(self.url)
		except WindowsError:
			print "Invalid Directory"
			return
		except requests.exceptions:
			print "Network Error"
			return
		print "Response: " + str(response.status_code)
		assert response.status_code == 200
		parser = HTMLParser.HTMLParser()
		soup = BeautifulSoup(parser.unescape(response.text))
		metadata,tracks = self.getData(soup)
		folder = re.sub('[\/:*"?<>|]','_',metadata['artist'] + ' - ' + metadata['album'])
		if not os.path.isdir(folder):
			os.mkdir(folder)
		os.chdir(os.getcwd() + '\\' + str(folder))
		self.getAlbumArt(soup,parser)
		print "Saving in : " + os.getcwd()
		print str(len(tracks)) + " track(s) found."
		print "Album : " + metadata['album']
		print "Artist: " + metadata['artist']
		for track in tracks:
			filename = parser.unescape(str(track['track_num']) + '. ' + track['title'].encode('utf-8') + '.mp3')
			link = parser.unescape(track['file']['mp3-128'])
			new_filename = self.getFile(filename,link)
			self.tagFile(new_filename,metadata,track)
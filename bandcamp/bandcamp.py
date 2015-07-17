import re,json,requests,HTMLParser
from bs4 import BeautifulSoup
import sys,os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC,APIC
from contextlib import closing
from time import sleep
import socket


class Downloader():
	
	def __init__(self,args):
		self.url = args.url
		self.dirname = args.dir
		self.session = requests.Session()
		self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
		self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
	
	def connectionHandler(self,url,stream = False,timeout = 15):
		try:
			response = self.session.get(url,stream = stream,timeout = timeout)
			assert response.status_code == 200
			return response
		except requests.exceptions.ConnectionError:
			print "Connection error. Retrying in 15 seconds."
			sleep(15)
			return self.connectionHandler(url,stream)
		except TypeError:
			print "Type error.Retrying in 15 seconds."
			sleep(15)
			return self.connectionHandler(url,stream)
		except AssertionError:
			print "Connection error or invalid URL."
			sys.exit(0) 
		except requests.exceptions.HTTPError:
			print "Invalid URL."
			return
		except KeyboardInterrupt:
			print "\nExiting."
			sys.exit(0)
				
	def getData(self,soup):	
		content = soup.find('meta',{'name':'Description'})['content']		
		JSdata = soup.findAll('script')
		var = re.search('trackinfo.*}]',str(JSdata)).group()[11::]
		tracks = json.loads(var)
		artist = re.search('artist: .*"',str(JSdata)).group()[9:-1]
		album = re.search('album_title.*"',str(JSdata)).group().split(': ')[1][1:-1]
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
		self.getFile('album-art.' + format,parser.unescape(albumArtURL),True)
		
	def progressBar(self,done,file_size):
		percentage = ((done/file_size)*100)
		sys.stdout.flush()
		sys.stdout.write('\r')	
		sys.stdout.write('[' + '#'*int((percentage/5)) + ' '*int((100-percentage)/5) + '] ')
		sys.stdout.write('%.2f' % percentage + ' %')
				
				
	def getFile(self,filename,link,silent = False):
		new_filename = re.sub('[\/:*"?<>|]','_',filename)
		if link is not None:
			if silent:
				try:
					with closing(self.connectionHandler(link,True,5)) as response:
						with open(new_filename,'wb') as file:
							for chunk in response.iter_content(chunk_size=1024):
								if chunk:
									file.write(chunk)
									file.flush()
					return new_filename
				except KeyboardInterrupt:
					print "\nExiting."
					sys.exit(0)
				except socket.error:
					return self.getFile(filename,link,silent)
				except requests.exceptions.ConnectionError:
					return self.getFile(filename,link,silent)		
			print "\nConnecting to stream..."
			try:
				with closing(self.connectionHandler(link,True,5)) as response:
					print "Response: "+ str(response.status_code)		
					file_size = float(response.headers['content-length'])	
					if(os.path.isfile(new_filename)):
						if os.path.getsize(new_filename) >= long(file_size):
							print new_filename + " already exists, skipping."
							return new_filename
						else:
							print "Incomplete download, restarting."
					print "File Size: " + '%.2f' % (file_size/(1000**2)) + ' MB'
					print "Saving as: " + new_filename
					done = 0
					try:
						with open(new_filename,'wb') as file:
							for chunk in response.iter_content(chunk_size=1024):
								if chunk:
									file.write(chunk)
									file.flush()
									done += len(chunk)
									self.progressBar(done,file_size)
									
						if os.path.getsize(new_filename) < long(file_size):
							print "\nConnection error. Restarting in 15 seconds."
							sleep(15)
							return self.getFile(filename,link,silent)
						print "\nDownload complete."
						return new_filename
					except KeyboardInterrupt:
						print "\nExiting."
						sys.exit(0)
					except socket.error:
						return self.getFile(filename,link,silent)
					except requests.exceptions.ConnectionError:
						return self.getFile(filename,link,silent)
			except KeyboardInterrupt:
				print "\nExiting." 
				sys.exit(0)
		else:
			return 
	
	def tagFile(self,filename,metadata,track):
		audio = MP3(filename,ID3=ID3)
		try:
			audio.add_tags()
		except:
			return 
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
			response = self.connectionHandler(self.url)
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
		print metadata['album']
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
from __future__ import print_function
import re,json,requests
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
		self.args = args
		self.completed = 0
	
	def connectionHandler(self,url,stream = False,timeout = 15):
		try:
			response = self.session.get(url,stream = stream,timeout = timeout)
			assert response.status_code == 200
			return response
		except (requests.exceptions.ConnectionError,
				TypeError,
				socket.error):
			print("Connection error. Retrying in 15 seconds.")
			sleep(15)
			return self.connectionHandler(url,stream)
		except (AssertionError,requests.exceptions.HTTPError):
			print("Connection error or invalid URL.")
			sys.exit(0) 
		except KeyboardInterrupt:
			print ("\nExiting.")
			sys.exit(0)
				
	def getData(self,soup):	
		content = soup.find('meta',{'name':'Description'})['content']		
		JSdata = soup.findAll('script')
		var = re.search('trackinfo : .*?}]',str(JSdata))
		var = var.group()[11::]
		tracks = json.loads(var)
		artist = re.search('artist: [^,]*',str(JSdata)).group()[8::].replace('"','')
		album = re.search('album_title: [^,]*"',str(JSdata))
		album = album.group().split(': ')[1][1:-1] if album is not None else None
		year = content.strip()[-1:-5:-1][::-1]
		metadata = {'artist' : artist,
					'album' : album,
					'year' : year
					}
		return metadata,tracks
	
	def getAlbumArt(self,soup):
		JSdata = soup.findAll('script')
		albumArtURL = re.search('artFullsizeUrl.*",',str(JSdata)).group()
		albumArtURL = re.search('artFullsizeUrl.*",', albumArtURL[0:100]).group()[17:-2]
		print ("Downloading Album Art.")
		format = albumArtURL.split('.')[-1]
		self.getFile('album-art.' + format, albumArtURL, True)
		
	def progressBar(self,done,file_size):
		percentage = ((done/file_size)*100)
		temp = '#'*int((percentage/5))
		progressString = '\r[{0: <20}] | {1:2.2f} %'.format(temp, percentage)
		print(progressString,end ='')
		sys.stdout.flush()
				
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
					print ("\nExiting.")
					sys.exit(0)
				except socket.error:
					return self.getFile(filename,link,silent)
				except requests.exceptions.ConnectionError:
					return self.getFile(filename,link,silent)		
			print ("\nConnecting to stream...")
			try:
				with closing(self.connectionHandler(link,True,5)) as response:
					print ("Response: "+ str(response.status_code))		
					file_size = float(response.headers['content-length'])	
					if(os.path.isfile(new_filename)):
						if os.path.getsize(new_filename) >= long(file_size):
							print (new_filename + " already exists, skipping.")
							return new_filename
						else:
							print ("Incomplete download, restarting.")
					print ("File Size: " + '%.2f' % (file_size/(1000**2)) + ' MB')
					print ("Saving as: " + new_filename)
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
							print( "\nConnection error. Restarting in 15 seconds.")
							sleep(15)
							return self.getFile(filename,link,silent)
						print ("\nDownload complete.")
						return new_filename
					except KeyboardInterrupt:
						print ("\nExiting.")
						sys.exit(0)
					except (socket.error,
							requests.exceptions.ConnectionError):
						return self.getFile(filename,link,silent)
			except KeyboardInterrupt:
				print ("\nExiting." )
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
	
	def getAlbum(self,tracks,metadata):
		for index, track in enumerate(tracks):
			if track['file'] is None:
				continue
			if track['track_num'] is not None:
				filename = str(track['track_num']) + '. ' + str(track['title'].encode('utf-8')) + '.mp3'
			else:
				filename = str(track['title'].encode('utf-8') + '.mp3')
			link = 'https:' + track['file']['mp3-128']
			if self.args.limit is not None:
				if self.completed == self.args.limit:
					return
			if self.args.include is not None:
				if self.completed == len(self.args.include):
					break
				if(index + 1) not in self.args.include:
					if self.args.range:
						if not (self.args.range[0] <= (index + 1) <= self.args.range[1]):
							continue
					else:
						continue
			elif self.args.exclude is not None:
				if (index + 1) in self.args.exclude:
					print ("Skipping " + str(track['title'].encode('utf-8')))
					continue
			new_filename = self.getFile(filename,link)
			self.tagFile(new_filename,metadata,track)	
					
	def Download(self):
		if self.url is None:
			print ("No URL entered.")
			return
		try:
			if self.dirname is not None:
				os.chdir(str(self.dirname))
			print ("Connecting ... ")
			response = self.connectionHandler(self.url)
		except WindowsError:
			print ("Invalid Directory")
			return
		except requests.exceptions:
			print ("Network Error")
			return
		print ("Response: " + str(response.status_code))
		assert response.status_code == 200
		soup = BeautifulSoup(response.text,'html.parser')
		metadata,tracks = self.getData(soup)
		if metadata['album'] is not None:
			folder = re.sub('[\/:*"?<>|]','_',metadata['artist'] + ' - ' + metadata['album'])
		else:
			folder = re.sub('[\/:*"?<>|]','_',metadata['artist'])
		if not os.path.isdir(folder):
			os.mkdir(folder)
		os.chdir(os.getcwd() + '\\' + str(folder))
		self.getAlbumArt(soup)
		print ("Saving in : " + os.getcwd())
		print (str(len(tracks)) + " track(s) found.")
		if metadata['album'] is not None:
			print ("Album : " + metadata['album'])
		print ("Artist: " + metadata['artist'])
		self.getAlbum(tracks,metadata)
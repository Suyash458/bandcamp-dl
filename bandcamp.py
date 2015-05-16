'''
1. Take command line arguments.
2. Change directory.
3. Validate file name. //Done
4. Check existing files. //Done
5. Make it robust.
6. Improve progressbar.
'''

import re,json,requests,HTMLParser
from bs4 import BeautifulSoup
import sys,os


class Downloader():
	
	def __init__(self,url = None,dirname = None):
		self.url = url
		self.dirname = dirname
		
	def getMetaData(self,soup):
		metadata = soup.find('meta',{'name':'Description'})['content']		
		album = soup.find('meta',{'name':'title'})['content']		
		trackInfo = re.findall('\d+\. .*',metadata)
		if 'track' in self.url:
			return None,album
		if 'album' in self.url:
			return album,trackInfo
			
	def getLinks(self,soup,parser):
		JSdata = soup.findAll('script')
		var = re.search('trackinfo.*}]',str(JSdata))
		var = var.group()[11::]
		var = json.loads(var)
		links = []
		for i in var:
			links.append(parser.unescape(i['file']['mp3-128']))
		return links
		
	def getFile(self,filename,link):
		print "Connecting to stream..."
		response = requests.get(str(link), stream=True)
		print "Response: "+ str(response.status_code)		
		file_size = float(response.headers['content-length'])
		filename = re.sub('[\/:*"?<>|]','_',filename)
		if(os.path.isfile(filename)):
			if os.path.getsize(filename) == long(file_size):
				print "File already exists, skipping."
				return
			else:
				print "Incomplete download, restarting."
		print "File Size: " + '%.2f' % (file_size/(1024**2)) + ' MB'
		print "Saving as: " + filename
		done = 0
		with open(filename,'wb') as file:
			for chunk in response.iter_content(chunk_size=1024):
				if chunk:
					file.write(chunk)
					file.flush()
					done += len(chunk)
					percentage = ((done/file_size)*100)
					sys.stdout.flush()
					sys.stdout.write('\r')
					sys.stdout.write('#'*int((percentage/5)) + ' ')
					sys.stdout.write('%.2f' % percentage + ' %')
		print "\nDownload complete."
				
	def Download(self):
		if self.url is None:
			print "No URL entered."
			return
		elif 'bandcamp' not in self.url:
			print "Invalid URL"
			return
		print "Connecting ... "
		response = requests.get(self.url)
		print "Response: " + str(response.status_code)
		parser = HTMLParser.HTMLParser()
		soup = BeautifulSoup(parser.unescape(response.text))
		album,tracks = self.getMetaData(soup)
		links = self.getLinks(soup,parser)
		if album is None:
			print "1 track found.";
			print tracks
			self.getFile(tracks,links[0])
		else:
			os.chdir(str(self.dirname))
			folder = re.sub('[\/:*"?<>|]','_',album)
			if not os.path.isdir(folder):
				os.mkdir(folder)
			os.chdir(os.getcwd() + '\\' + str(folder))
			print "Saving in : " + os.getcwd()
			print str(len(tracks)) + " tracks found."
			print "Album : " + album
			for track,link in zip(tracks,links):
				self.getFile(track + '.mp3',link)
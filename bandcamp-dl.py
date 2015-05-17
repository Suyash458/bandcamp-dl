from bandcamp import bandcamp
import sys

if __name__ == '__main__':
	downloader = bandcamp.Downloader()
	downloader.url = sys.argv[1]
	downloader.dirname = sys.argv[2]
	downloader.Download()
	
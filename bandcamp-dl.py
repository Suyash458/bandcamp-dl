from bandcamp import bandcamp
import sys,argparse,os

parser = argparse.ArgumentParser()
parser.add_argument('--url',default = None, type = str, help = 'URL to download tracks from.')
parser.add_argument('--dir',default = os.getcwd(), type = str, help = 'Directory to save tracks in. Default value is the current working directory.')

if __name__ == '__main__':
	args = parser.parse_args()
	if args.url == None:
		print "No URL entered."
		sys.exit(0)
	downloader = bandcamp.Downloader(args)
	downloader.Download()
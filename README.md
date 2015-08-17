# Bandcamp-dl
A small command-line program to download tracks from Bandcamp.com 

==================================================================
##Installation

####From Source
* Clone the repo or download the zip
* Make sure you have pip installed
* `cd` to the folder
* `pip -install -r "requirements.txt"`

##Usage
* On the terminal or Command Prompt Type
  `python bandcamp-dl.py --url "url" --dir "directory"`
* The current working directory is the default download location.
* Adding the --include option overrides the --exclude option. 
* Example : `python bandcamp-dl.py --url "URL" --dir "D:\Music"`
* Example : `python bandcamp-dl.py --url "URL" --dir "D:\Music" --exclude 1 2 3`

##Options
     -h, --help  show this help message and exit
     --url URL   URL to download tracks from.
     --dir DIR   Directory to save tracks in. Default value is the current
                 working directory.
     --exclude   exclude a list of tracks.(List of space separeted integers)
     --include   specifically download a list of tracks.(List of space separated integers)
     --limit     limits the number of tracks to be downloaded.(Single integer)
     --range     Range of track numbers to download.(Two space separated integers)
  
###Dependencies
* BeautifulSoup - HTML parsing
* Requests - for retrieving HTML
* Mutagen - To tag mp3 files and add album art

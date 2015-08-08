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
  
###Dependencies
* BeautifulSoup - HTML parsing
* Requests - for retrieving HTML
* Mutagen - To tag mp3 files and add album art

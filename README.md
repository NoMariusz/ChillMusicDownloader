# Chill Music Downloader 
![Logo](data/graphics/CMDownloader_logo.png "Logo")

Program downloads .mp3, .aac and others audio files to destination folder, from youtube.com, by address, or name of song

CMDownloader also remember last downloaded song from each channel, so you can download new released songs from your favourite youtube channels by few clicks !!!

## Main menu
![Menu](data/graphics/screenshots/Screen1.jpg "Menu")
- Downloading multiple music from given channel
- Section which finds 5 videos with most similar name to that entered by user, then enable uster to download one of them
- Dowload video by address url
- Menu with options, enable to change save path, file extension, channel

### Downloading from channel menu
![Channel download menu](data/graphics/screenshots/Screen2.jpg "Channel download menu")
- Load 50 lastest videos from channel
- Download all new videos so, that are bellow last download song
- Enable to select exacly what songs to download
- Changes the last download song name to given by user
- Load all music from channel or that much as Youtube Api will allow


## Main python modules
* requests
* BeautifulSoup
* youtube_dl
* kivy
* google-api-python-client

## Notes

App uses [YouTube Data API](https://developers.google.com/youtube/v3) so have limited count of queries send to api per day

To correct work, app must also have ffmpeg.exe file in app folder, can be download from [here](https://ffmpeg.org/download.html)

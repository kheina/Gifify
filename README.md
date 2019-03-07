# Gifify Bot
## About
Allows telegram users to more easily access and share media content from twitter and the rest of the web.  

To do this, the bot takes a twitter url and retrieves the tweet ID from the link. Using the tweet ID, the bot then sends a request to the twitter API for status information from that ID. This information includes whether or not a tweet contains a video and, if it does, what the source of that video is. The bot then uses FFmpeg to convert it into an audio-less mp4 format so that telegram displays it like an animated GIF.  

For other urls, the bot first checks whether or not it is a direct link to one of the supported media types (currently this is just via checking the file extension in a url. There are better ways to do this, but checking formats of remote data can be rather difficult). If the url is not a direct link, the bot will attempt to parse the page for supported media. Afterwards, it will download the media and pass it through FFmpeg after gathering some information about the media and determining what parameters to give to FFmpeg to get the highest quality conversion.  

## Usage
Just send a link or file to [t.me/gififybot](https://t.me/gififybot)  

### Note:
Requires [FFmpeg and FFprobe](https://www.ffmpeg.org/download.html) version 4+ to run  
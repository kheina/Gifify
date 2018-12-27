# Gifify Bot
## About
Allows telegram users to more easily access and share media content from twitter.

To do this, the bot takes a twitter url and retrieves the tweet ID from the link. Using the tweet ID, the bot then sends a request to the twitter API for status information from that ID. This information includes whether or not a tweet contains a video and, if it does, what the source of that video is. The bot then uses FFmpeg to convert it into an audio-less mp4 format so that telegram displays it like an animated GIF.

## Usage
Just send a link to [t.me/gififybot](https://t.me/gififybot)

### Note:
Requires [FFmpeg and FFprobe](https://www.ffmpeg.org/download.html) to run
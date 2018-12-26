import os
import sys
import time
import json
import shutil
import twitter
import requests
import subprocess

def IsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def getstatusfromurl(url) :
	# https://twitter.com/AMAZlNGNATURE/status/1076962168078102528
	if '//twitter.com' in url and '/status/' in url :
		url = url.split('?')    # trim off any excess stuff
		url = url[0].split('/') # and only use the main url
		for i in range(-1, len(url) * -1, -1) : # ideally goes from -1 to -5
			if IsInt(url[i]) and int(url[i]) > 10 : # sometimes there are other numbers in the url, but there are no statuses under 10
				return url[i]
	return False

def getvideourl(url) :
	global api
	global length
	global bitrate
	print(' (', url, ') ', end='')
	status = getstatusfromurl(url)
	status = api.GetStatus(status)
	#with open('status.json','w') as f : # debug
	#	f.write(str(json.dumps(json.loads(str(status)), indent=2)))
	status = status.AsDict()
	bitrate = 0
	streamurl = None
	largestindex = -1
	if 'media' in status and 'video_info' in status['media'][0] : 
		length = status['media'][0]['video_info']['duration_millis'] / 1000 # for seconds
		for i in range(len(status['media'][0]['video_info']['variants'])) :
			if status['media'][0]['video_info']['variants'][i]['content_type'] == 'application/x-mpegURL' :
				videourl = status['media'][0]['video_info']['variants'][i]['url']
			elif status['media'][0]['video_info']['variants'][i]['bitrate'] > bitrate :
				bitrate = status['media'][0]['video_info']['variants'][i]['bitrate']
				largestindex = i
		#if videourl is not None :
		#	#print('bitrate:', bitrate, ' length:', length, ' est-size:', (bitrate/8192)*length, 'kb', sep='')
		#	return videourl
		else :
			return status['media'][0]['video_info']['variants'][largestindex]['url']

def converturltogif(url) :
	global length
	global bitrate
	quality = '-c copy'
	width = 1920  # assume worst case
	height = 1080 # assume worst case
	ar = '16:9'
	misc = ''
	#print('\ntwitter est:', (bitrate/8192)*length, 'kb', sep='')
	try :
		if '.m3u8' in url :
			if (bitrate/8192)*length > 10000 : # estimating final size to determine if it should be compressed
				quality =  '-b:v ' + str(75000 / length) + 'k' # 75,000 seems to work best to keep it under 10mb 
				print('(compressing)...', end='', flush=True)
			subprocess.call('ffmpeg -i ' + url + ' -loglevel quiet ' + quality + ' -an tempgif.mp4 -y')
			return True
		elif '.mp4' in url :
			response = requests.get(url, stream=True) # stream=True IS REQUIRED
			if response.status_code == 200 :
				with open('temp.mp4', 'wb') as tobegif :
					shutil.copyfileobj(response.raw, tobegif)
			ffprobe = subprocess.check_output('ffprobe -v quiet -print_format json -show_streams temp.mp4').decode('utf-8')
			ffprobe = json.loads(ffprobe)
			for i in range(len(ffprobe['streams'])) :
				if ffprobe['streams'][i]['codec_type'] == 'video' :
					if 'bit_rate' in ffprobe['streams'][i] :
						bitrate = int(ffprobe['streams'][i]['bit_rate'])
					else :
						bitrate = 5000000 # assume the worst
					if 'width' in ffprobe['streams'][i] :
						width = int(ffprobe['streams'][i]['width'])
					if 'height' in ffprobe['streams'][i] :
						height = int(ffprobe['streams'][i]['height'])
					break
			#print('ffprobe est:', (bitrate/8192)*length, 'kb', sep='')
			if (bitrate/8192)*length > 10000 : # estimating final size to determine if it should be compressed
				quality =  '-b:v ' + str(75000 / length) + 'k' # 75,000 seems to work best to keep it under 10mb 
				print('(compressing)...', end='', flush=True)
			subprocess.call('ffmpeg -i temp.mp4 ' + quality + misc + ' -loglevel quiet -an tempgif.mp4 -y')
			return True
		elif '.webm' in url :
			response = requests.get(url, stream=True) # stream=True IS REQUIRED
			if response.status_code == 200 :
				with open('temp.webm', 'wb') as tobegif :
					shutil.copyfileobj(response.raw, tobegif)
			ffprobe = subprocess.check_output('ffprobe -v quiet -print_format json -show_streams temp.webm').decode('utf-8')
			ffprobe = json.loads(ffprobe)
			for i in range(len(ffprobe['streams'])) :
				if ffprobe['streams'][i]['codec_type'] == 'video' :
					if 'bit_rate' in ffprobe['streams'][i] :
						bitrate = int(ffprobe['streams'][i]['bit_rate'])
					else :
						bitrate = 5000000 # assume the worst
					if 'width' in ffprobe['streams'][i] :
						width = int(ffprobe['streams'][i]['width'])
					if 'height' in ffprobe['streams'][i] :
						height = int(ffprobe['streams'][i]['height'])
					break
			if width >= height and width > 1280 :
				misc = ' -vf scale=1280:-1'
			elif height > width and height > 1280 :
				misc = ' -vf scale=-1:1280'
			#print('ffprobe est:', (bitrate/8192)*length, 'kb', sep='')
			#if (bitrate/8192)*length > 10000 : # estimating final size to determine if it should be compressed
			quality =  '-b:v 3000k' # no way to measure length OR bitrate of webm files, so just do 3mb/s and hope for the best
			print('(compressing)...', end='', flush=True)
			subprocess.call('ffmpeg -i temp.webm ' + quality + misc + ' -loglevel quiet -an tempgif.mp4 -y')
			return True
	except Exception as e :
		print(e)
		return False

def linkonly(url) :
	if '//twitter.com' in url and '/status/' in url :
		return getvideourl(url)
	elif '.mp4' in url or '.webm' in url :
		return url

def start(update) :
	request = 'https://api.telegram.org/bot' + token + '/sendMessage'
	response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&text=I can quickly convert twitter video content into a gif for you to share!\n\nJust send me a link to get started.')

def incrementloadloop() :
	global loadloop
	global loadindex
	print('\r' + loadloop[loadindex], end=' ')
	loadindex = loadindex + 1
	if loadindex > 3 : loadindex = 0
	

if __name__ == "__main__" :
	global api
	global token
	global loadloop
	global loadindex
	giffer = sys.modules[__name__]

	# telegram bot auth token (given by @BotFather upon your bot's creation)
	token = ''

	# the id of the bot itself
	botID = 0

	# initialize twitter
	api = ''

	print('loading credentials...', end='', flush= True)
	with open('credentials.json') as userinfo :
		credentials = json.load(userinfo)
		token = credentials['telegramAccessToken']
		botID = credentials['telegramBotID']
		api = twitter.Api(consumer_key = credentials['twitter']['consumerKey'], consumer_secret = credentials['twitter']['consumerSecret'], access_token_key = credentials['twitter']['accessTokenKey'], access_token_secret = credentials['twitter']['accessTokenSecret'], tweet_mode='extended')
		#print(json.dumps(credentials, indent=2))
	print('success.\n')

	maxloops = 10000 # for debugging, so it doesn't run forever
	loadloop = ['|', '/', '-', '\\']
	loadindex = 0

	loops = 0
	mostrecentupdate = 0
	while (True) :
		request = 'https://api.telegram.org/bot' + token + '/getUpdates'
		incrementloadloop()
		response = requests.get(request + '?offset=' + str(mostrecentupdate + 1))
		response = response.json()
		if response['ok'] :
			updateList = response['result']
			if len(updateList) > 0 :
				print('\rupdates:', len(updateList))
				for i in range(len(updateList)) :
					#if 'query' in updateList[i] and 'status' in updateList[i]['query'] : # FOR INLINE
					#	get_video_url(updateList[i]['query'])
					if 'message' in updateList[i] and 'text' in updateList[i]['message'] :
						if 'from' in updateList[i]['message'] :
							if 'username' in updateList[i]['message']['from'] :
								print('(from ', updateList[i]['message']['from']['username'], ')', sep='')
							else :
								print('(from ', updateList[i]['message']['from']['first_name'], ' (', updateList[i]['message']['from']['id'], '))', sep='')

						query = updateList[i]['message']['text'].split(' ')
						if len(query) == 1 and updateList[i]['message']['text'][0] is not '/' :
							command = 'linkonly'
							url = query[0]
						else :
							command = query[0][1:] # remove the slash
							if len(query) > 1 :
								url = query[1]

						if command == 'linkonly' :
							method = getattr(giffer, command)
							print('retrieving url...', end='', flush=True)
							videourl = method(url)
							if videourl is not None :
								print('success. (', videourl, ')')
								
								print('converting to gif...', end='', flush=True)
								if converturltogif(videourl) :
									print('success.')
									print('sending gif...', end='', flush=True)
									request = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + str(updateList[i]['message']['from']['id']) + '&caption=' + url.replace('?', '%3F')
									gif = open('tempgif.mp4', 'rb')
									telegramfile = {'document': gif}
									sentFile = requests.get(request, files=telegramfile)
									print('success.')

								else :
									print('failed, sending url instead...', end='', flush=True)
									request = 'https://api.telegram.org/bot' + token + '/sendMessage'
									response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&text=' + videourl)
									response = response.json()
									if response['ok'] :
										print('done.')
									else :
										print('failed.')
										if 'description' in response :
											print('reason: ' + response['description'])
							else :
								print('failed. (', url,')')
						elif hasattr(giffer, command) :
							method = getattr(giffer, command)
							method(updateList[i])
							
				# clear update list
				mostrecentupdate = updateList[-1]['update_id']
		else :
			print('\rresponse not ok:', response)
			# wait a second before trying again
		#loops = loops + 1
		#time.sleep(1)
	
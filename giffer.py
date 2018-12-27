from requests_html import HTMLSession
import PIL.GifImagePlugin
import subprocess
import requests
import colorama
import twitter
import twitter
import shutil
import json
import time
import sys
import os

def IsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def IsFloat(s):
    try: 
        float(s)
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
	global quality
	global inputoptions
	width = 1920  # assume worst case scenarios
	height = 1080
	ar = '16:9'
	misc = '-pix_fmt yuv420p'
	filesize = None

	url = url.split('?')[0] #remove any extraneous information after and including ?, if there is one

	try :
		if url.endswith('.m3u8') :
			quality = '-c copy'
			if (bitrate/8192)*length > 10000 : # estimating final size to determine if it should be compressed
				quality = str(77000 / length) # ~75,000 seems to work best to keep it under 10mb
				print('(compressing, ', length, 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
			subprocess.call('ffmpeg ' + inputoptions + ' -i ' + url + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an tempgif.mp4 -y')
			return True
		elif url.endswith('.mp4') :
			response = requests.get(url, stream=True) # stream=True IS REQUIRED
			if response.status_code == 200 :
				with open('temp.mp4', 'wb') as tobegif :
					shutil.copyfileobj(response.raw, tobegif)
			bitrate, width, height, length, filesize = FFprobe('temp.mp4')
			if width >= height and width > 1280 :
				misc = misc + ' -vf scale=1280:-2'
			elif height > width and height > 1280 :
				misc = misc + ' -vf scale=-2:1280'
			quality = '-c copy'
			if (bitrate/8192)*length > 10000 : # estimating final size to determine if it should be compressed
				quality = '-b:v ' + str(77000 / length) + 'k' # ~75,000 seems to work best to keep it under 10mb
				print('(compressing, ', length, 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
			subprocess.call('ffmpeg ' + inputoptions + ' -i temp.mp4 ' + quality + ' ' + misc + ' -loglevel quiet -an tempgif.mp4 -y')
			return True
		elif url.endswith('.webm') :
			response = requests.get(url, stream=True) # stream=True IS REQUIRED
			if response.status_code == 200 :
				with open('temp.webm', 'wb') as tobegif :
					shutil.copyfileobj(response.raw, tobegif)
			bitrate, width, height, length, filesize = FFprobe('temp.webm')
			if width >= height and width > 1280 :
				misc = misc + ' -vf scale=1280:-2'
			elif height > width and height > 1280 :
				misc = misc + ' -vf scale=-2:1280'
			elif width % 2 != 0 or height % 2 != 0 :
				misc = misc + ' -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"'
			#print('ffprobe est:', (bitrate/8192)*length, 'kb', sep='')
			if length * float(quality)/8 > 10000 : # estimating final size to determine if it should be compressed
				quality = str(80000 / length) # ~75,000 seems to work best to keep it under 10mb
			elif length == 1 and filesize/8192 > 8000 :
				quality = '1500' # there's no way to estimate what the bitrate or length is, so 1500 seems like a happy medium between quality and likelyhood the result will be under 10mb
			print('(compressing, ', length, 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
			subprocess.call('ffmpeg ' + inputoptions + ' -i temp.webm -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an tempgif.mp4 -y')
			return True
		elif url.endswith('.gif') :
			response = requests.get(url, stream=True) # stream=True IS REQUIRED
			if response.status_code == 200 :
				with open('temp.gif', 'wb') as tobegif :
					shutil.copyfileobj(response.raw, tobegif)
			bitrate, width, height, length, filesize = FFprobe('temp.gif')
			if width >= height and width > 1280 :
				misc = misc + ' -vf scale=1280:-2'
			elif height > width and height > 1280 :
				misc = misc + ' -vf scale=-2:1280'
			elif width % 2 != 0 or height % 2 != 0 :
				misc = misc + ' -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"'
			#print('bitrate:', bitrate, ' length:', length, ' ffprobe est:', (bitrate/8192)*length, 'kb', sep='')
			if length * float(quality)/8 > 10000 : # estimating final size to determine if it should be compressed
				quality = str(80000 / length) # ~75,000 seems to work best to keep it under 10mb
			print('(compressing, ', length, 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
			call = 'ffmpeg ' + inputoptions + ' -i temp.gif -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an tempgif.mp4 -y'
			#print('( ' + call, end=' )...')
			subprocess.call(call)
			return True
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( error: ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		return False

def FFprobe(filename) :
	global length
	ffprobe = subprocess.check_output('ffprobe -v quiet -print_format json -show_streams ' + filename).decode('utf-8')
	ffprobe = json.loads(ffprobe)
	bitrate = -1 # set defaults as worst-case scenario
	width = 1920
	height = 1080
	filesize = None
	for i in range(len(ffprobe['streams'])) :
		if 'codec_type' in ffprobe['streams'][i] and ffprobe['streams'][i]['codec_type'] == 'video' : # ffprobe shows gif codec type as being video, so this still works
			if 'bit_rate' in ffprobe['streams'][i] :
				bitrate = int(ffprobe['streams'][i]['bit_rate'])
			if 'width' in ffprobe['streams'][i] :
				width = int(ffprobe['streams'][i]['width'])
			if 'height' in ffprobe['streams'][i] :
				height = int(ffprobe['streams'][i]['height'])
			if length == 1 and 'tags' in ffprobe['streams'][i] and 'DURATION' in ffprobe['streams'][i]['tags'] :
				length = getsecondsfromtimecode(ffprobe['streams'][i]['tags']['DURATION'])
			if length == 1 and 'duration' in ffprobe['streams'][i] :
				length = float(ffprobe['streams'][i]['duration']) # already seconds
		if length == 1 and 'codec_type' in ffprobe['streams'][i] and ffprobe['streams'][i]['codec_type'] == 'audio' :
			if 'tags' in ffprobe['streams'][i] and 'DURATION' in ffprobe['streams'][i]['tags'] :
				length = getsecondsfromtimecode(ffprobe['streams'][i]['tags']['DURATION'])
			if 'duration' in ffprobe['streams'][i] :
				length = float(ffprobe['streams'][i]['duration']) # already seconds

	filesize = os.path.getsize(filename) * 8 # convert to bits
	if bitrate < 0 :
		bitrate = filesize / length
	if filename.endswith('.gif') :
		with PIL.GifImagePlugin.GifImageFile(fp=filename) as gif :
			length = (gif.n_frames + 1) * gif.info['duration'] / 1000 # divide by 1000 to get seconds
			bitrate = filesize / length
	return bitrate, width, height, length, filesize

def istimecodeformat(timecode) :
	try :
		timecode = timecode.split(':')
		for potentialfloat in timecode :
			if not IsFloat(potentialfloat) :
				return False
		return True
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( error: ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
	return False

def getsecondsfromtimecode(timecode) :
	try :
		timecode = timecode.split(':')
		if len(timecode) == 1 :
			return float(timecode[0])
		elif len(timecode) == 2 :
			return float(timecode[0]) * 60 + float(timecode[1])
		elif len(timecode) == 3 :
			return float(timecode[0]) * 3600 + float(timecode[1]) * 60 + float(timecode[2])
		else :
			return 1
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( error: ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		return 1

def linkonly(url) :
	url = url.split('?')[0] #remove any extraneous information after and including ?, if there is one
	if '//twitter.com' in url and '/status/' in url :
		return getvideourl(url)
	elif url.endswith('.mp4') or url.endswith('.webm') or url.endswith('.gif') :
		return url
	elif url.endswith('.gifv') :
		return url.replace('.gifv', '.mp4')
	else :
		return parseformedia(url)

def geturlfromdocument(document) :
	global acceptedtypes
	if 'mime_type' in document :
		mime_type = document['mime_type'].split('/')
		if len(mime_type) > 1 and mime_type[1] in acceptedtypes :
			request = 'https://api.telegram.org/bot' + token + '/getFile?file_id=' + document['file_id']
			response = requests.get(request)
			response = checkresponsesilent(response)
			if response is not False :
				return 'https://api.telegram.org/file/bot' + token + '/' + response['result']['file_path']

def parseformedia(url) :
	try: 
		session = HTMLSession()
		page = session.get(url)
		source = None
		for sourcetype in ['source[src*=".webm"]', 'source[src*=".mp4"]', 'img[src*=".gif"]'] :
			temp = page.html.find(sourcetype, first=True)
			if temp is not None : source = temp
		return source.attrs['src']
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( error: ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		return None




def start(update) :
	print('responding to /start...', end='', flush=True)
	request = 'https://api.telegram.org/bot' + token + '/sendMessage'
	response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&text=I can quickly convert video content into a gif for you to share!\n\nI can convert .mp4, .gifv, .gif, and .webm URLs, and even parse twitter and many other websites!\n\nJust send me a link or file to get started!\n\nP.S. if you want to help me out, tell me about how long the video is by sending me length=[time in seconds] after your url (webm only)\nex: https://example.com/yourvideo.webm length=73\n\nOr, alternatively, you can send me starting and ending times, and I\'ll turn that clip into a gif!\nex: https://example.com/yourvideo.gif start=5 end=16.2')
	checkresponse(response)

def help(update) :
	print('responding to /help...', end='', flush=True)
	request = 'https://api.telegram.org/bot' + token + '/sendMessage'
	response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&text=Did the gif not turn out correctly?\n\nIf you want to help me out, tell me about how long the video is by sending me length=[time in seconds] after your url (webm only)\nex: https://example.com/yourvideo.webm length=73\n\nOr, alternatively, you can send me starting and ending times, and I\'ll turn that clip into a gif!\nex: https://example.com/yourvideo.gif start=5 end=16.2')
	checkresponse(response)

def incrementloadloop() :
	global loadloop
	global loadindex
	print(colorama.Fore.CYAN + '\r' + loadloop[loadindex] + ' ', end=colorama.Style.RESET_ALL)
	loadindex = loadindex + 1
	if loadindex > loadframes : loadindex = 0
	
def checkresponse(response) :
	try :
		response = response.json()
		if response['ok'] :
			print('success.')
			return response
		else :
			print('failed.')
			if 'description' in response :
				print('reason: ' + response['description'])
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( error: ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='')
		print(response, end='\n\n')
		
def checkresponsesilent(response) :
	try :
		response = response.json()
		if not response['ok'] :
			print('failed.')
			if 'description' in response :
				print('reason: ' + response['description'])
			return False
		else :
			return response
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( error: ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='')
		print(response, end='\n\n')
		return False

if __name__ == "__main__" :
	global api
	global token
	global length
	global quality
	global loadloop
	global loadindex
	global inputoptions
	global acceptedtypes
	giffer = sys.modules[__name__]
	colorama.init()

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
	loadloop = ['⠇', '⠋', '⠙', '⠸', '⢰', '⣠', '⣄', '⡆']
	loadframes = len(loadloop) - 1
	loadindex = 0

	commands = ['linkonly', 'geturlfromdocument']
	othercommands = ['start', 'help']
	acceptedtypes = ['webm', 'mp4', 'gif']
	
	loops = 0
	mostrecentupdate = 0
	while (True) :
		request = 'https://api.telegram.org/bot' + token + '/getUpdates'
		incrementloadloop()
		response = requests.get(request + '?offset=' + str(mostrecentupdate + 1))
		updateList = checkresponsesilent(response)
		if updateList is not False :
			updateList = updateList['result']
			if len(updateList) > 0 :
				print('\rupdates:', len(updateList))
				for i in range(len(updateList)) :
					#if 'query' in updateList[i] and 'status' in updateList[i]['query'] : # FOR INLINE
					#	get_video_url(updateList[i]['query'])
					if 'message' in updateList[i] :
						if 'text' in updateList[i]['message'] or 'document' in updateList[i]['message'] :
							url = ''
							command = ''
							length = 1 # defaults
							inputoptions = ''
							starttime = 0
							endtime = 0
							quality = '4000'
							if 'from' in updateList[i]['message'] :
								if 'username' in updateList[i]['message']['from'] :
									print('(from ', updateList[i]['message']['from']['username'], ')', sep='', end=' ')
								else :
									print('(from ', updateList[i]['message']['from']['first_name'], ' (', updateList[i]['message']['from']['id'], '))', sep='', end=' ')
							
							if 'text' in updateList[i]['message'] :
								query = updateList[i]['message']['text'].split(' ')
							elif 'document' in updateList[i]['message'] :
								command = 'geturlfromdocument'
								url = updateList[i]['message']['document']
								if 'caption' in updateList[i]['message'] :
									query = updateList[i]['message']['caption'].split(' ')
								else : query = []

							if len(query) > 0 and query[0][0] == '/' :
								command = query[0][1:] # remove the slash

							print(query)
							if len(query) == 1 and query[0][0] != '/' and command == '' :
								command = 'linkonly'
								url = query[0]
							else :
								for j in range(len(query)) :
									if len(query[j]) >= 4 and query[j].startswith('http') :
										url = query[j]
									elif query[j] == 'length' and len(query) > j+1 :
										length = getsecondsfromtimecode(query[j+1])
										j = j + 1
									elif 'length=' in query[j] :
										queryj = query[j].split('=')
										if len(queryj) >= 2 : length = getsecondsfromtimecode(queryj[1])
									elif query[j] == 'bitrate' and len(query) > j+1 and istimecodeformat(query[j+1]) :
										quality = query[j+1]
										j = j + 1
									elif 'bitrate=' in query[j] :
										queryj = query[j].split('=')
										if len(queryj) >= 2 and istimecodeformat(queryj[1]) : quality = queryj[1]
									elif query[j] == 'start' and len(query) > j+1 and istimecodeformat(query[j+1]) :
										starttime = getsecondsfromtimecode(query[j+1])
										inputoptions = inputoptions + ' -ss ' + str(starttime)
										j = j + 1
									elif 'start=' in query[j] :
										queryj = query[j].split('=')
										if len(queryj) >= 2 and istimecodeformat(queryj[1]) :
											starttime = getsecondsfromtimecode(queryj[1])
											inputoptions = inputoptions + ' -ss ' + str(starttime)
									elif query[j] == 'end' and len(query) > j+1 and istimecodeformat(query[j+1]) :
										endtime = getsecondsfromtimecode(query[j+1])
										inputoptions = inputoptions + ' -to ' + str(endtime)
										j = j + 1
									elif 'end=' in query[j] :
										queryj = query[j].split('=')
										if len(queryj) >= 2 and istimecodeformat(queryj[1]) :
											endtime = getsecondsfromtimecode(queryj[1])
											inputoptions = inputoptions + ' -to ' + str(endtime)
									elif istimecodeformat(query[j]) :
										length = getsecondsfromtimecode(query[j])
									
								if endtime != 0 :
									length = endtime - starttime

							if command in commands :
								method = getattr(giffer, command)
								print('retrieving url...', end='', flush=True)
								videourl = method(url)
								if videourl is not None :
									print('success. (', videourl, ')')
									
									print('converting to gif...', end='', flush=True)
									if converturltogif(videourl) :
										print('success.')
										print('sending gif...', end='', flush=True)
										if command == 'linkonly' :
											request = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&caption=' + url.replace('?', '%3F')
										else :
											request = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id'])
										gif = open('tempgif.mp4', 'rb')
										telegramfile = {'document': gif}
										sentFile = requests.get(request, files=telegramfile)
										checkresponse(sentFile)
									else :
										print('failed, sending url instead...', end='', flush=True)
										request = 'https://api.telegram.org/bot' + token + '/sendMessage'
										response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&text=' + videourl)
										checkresponse(response)
								else :
									print('failed. ( /', command, ' ', url,' )', sep='', flush=True)
									print('apologizing...', end='', flush=True)
									request = 'https://api.telegram.org/bot' + token + '/sendMessage'
									response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&text=Sorry, I don\'t support that filetype yet!\n\nTo see what I can do, try /start')
									checkresponse(response)
							elif command in othercommands and hasattr(giffer, command) :
								method = getattr(giffer, command)
								method(updateList[i])
							else :
								print('unknown command ( /', command, ' ) apologizing...', sep='', end='', flush=True)
								request = 'https://api.telegram.org/bot' + token + '/sendMessage'
								response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&text=Sorry, I don\'t respond to that command.\n\nTry /start or /help')
								checkresponse(response)
					else :
						print(updateList[i])
							
				# clear update list
				mostrecentupdate = updateList[-1]['update_id']
		else :
			time.sleep(1) # wait a second before trying again
		#loops = loops + 1
	
from requests_html import HTMLSession
import PIL.GifImagePlugin
try : import ujson as json
except : import json
import subprocess
import requests
import colorama
import twitter
import shutil
import time
import sys
import os

def IsInt(s):
    try :
        return int(s)
    except ValueError :
        return None

def IsFloat(s):
    try :
        return float(s)
    except ValueError :
        return None

def isstr(s):
	try :
		return isinstance(s, str)
	except ValueError :
		return None


def getstatusfromurl(url) :
	# https://twitter.com/AMAZlNGNATURE/status/1076962168078102528
	if '//twitter.com' in url and '/status/' in url :
		url = url.split('?')    # trim off any excess stuff
		url = url[0].split('/') # and only use the main url
		for i in range(-1, len(url) * -1, -1) : # ideally goes from -1 to -5
			url[i] = IsInt(url[i])
			if url[i] and int(url[i]) > 10 : # sometimes there are other numbers in the url, but there are no statuses under 10
				return url[i]
	return False

def getvideourl(url) :
	global api
	global length
	global bitrate
	if not api :
		print(' (twitter not initialized) ', end='')
		return None
	print(' (', url, ') ', end='')
	status = getstatusfromurl(url)
	status = api.GetStatus(status)
	#with open('status.json','w') as f : # debug
	#	f.write(str(json.dumps(json.loads(str(status)), indent=2)))
	status = status.AsDict()
	bitrate = 0
	streamurl = None
	largestindex = -1
	try :
		if 'media' in status and 'video_info' in status['media'][0] : 
			for i in range(len(status['media'][0]['video_info']['variants'])) :
				#if status['media'][0]['video_info']['variants'][i]['content_type'] == 'application/x-mpegURL' :
				#	videourl = status['media'][0]['video_info']['variants'][i]['url']
				if 'bitrate' in status['media'][0]['video_info']['variants'][i] and status['media'][0]['video_info']['variants'][i]['bitrate'] > bitrate :
					bitrate = status['media'][0]['video_info']['variants'][i]['bitrate']
					largestindex = i
			#if videourl is not None :
			#	#print('bitrate:', bitrate, ' length:', length, ' est-size:', (bitrate/8192)*length, 'kb', sep='')
			#	return videourl
			#else :
			if largestindex >= 0 : return status['media'][0]['video_info']['variants'][largestindex]['url']
		# twitter url doesn't have a media and video_info, need to search for media
		media = searchformediaintweet(status)
		if media : return media
	except : donothing()
	print(status)

def searchformediaintweet(status) :
	for key, value in status.items() :
		if isstr(value) and value.split('?')[0].endswith('.mp4') : # all twitter videos should be mp4s
			return value
		elif isinstance(value, dict) :
			media = searchformediaintweet(value)
			if media is not None : return media
		elif isinstance(value, list) :
			media = searchformediaintweetlist(value)
			if media is not None : return media
	return None

def searchformediaintweetlist(status) :
	for value in status :
		if isstr(value) and value.split('?')[0].endswith('.mp4') : # all twitter videos should be mp4s
			return value
		elif isinstance(value, dict) :
			media = searchformediaintweet(value)
			if media is not None : return media
		elif isinstance(value, list) :
			media = searchformediaintweetlist(value)
			if media is not None : return media
	return None

def converturltogif(url) :
	url = url.split('?')[0] # remove any extraneous information after and including ?, if there is one
	urllower = url.lower()

	call = ''
	try :
		if urllower.endswith('.m3u8') :
			quality = '-c copy'
			call = 'ffmpeg ' + inputoptions + ' -i ' + url + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an gifify.mp4 -y'
			subprocess.call(call.split())
		elif urllower.endswith('.mp4') and downloadfile(url, 'temp.mp4') :
			call = convertmp4()

		elif urllower.endswith('.webm') and downloadfile(url, 'temp.webm') :
			call = convertwebm()

		elif urllower.endswith('.mov') and downloadfile(url, 'temp.mov') :
			call = convertmov()
			
		elif urllower.endswith('.gif') and downloadfile(url, 'temp.gif') :
			call = convertgif()

		elif urllower.endswith('.swf') and downloadfile(url, 'temp.swf') :
			call = convertswf()

		if os.path.isfile('gifify.mp4') : # check to make sure the file exists
			finalsize = os.path.getsize('gifify.mp4') / 1024
			if finalsize > 1 : return finalsize # return the size of the converted file (and divide by 1024 to get kilobytes)
		# if the file doesn't exist, clearly conversion failed
		print('failed. ( ', call ,' )', sep='', flush=True)
		return False
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		return False

def convertlocalfile(filename) :
	urllower = filename.lower()
	call = ''
	try :
		if urllower.endswith('.m3u8') :
			quality = '-c copy'
			call = 'ffmpeg ' + inputoptions + ' -i ' + url + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an gif.mp4 -y'
			subprocess.call(call.split())
		elif urllower.endswith('.mp4') :
			call = convertmp4(filename=filename, out='gif.mp4')

		elif urllower.endswith('.webm') :
			call = convertwebm(filename=filename, out='gif.mp4')

		elif urllower.endswith('.mov') :
			call = convertmov(filename=filename, out='gif.mp4')
			
		elif urllower.endswith('.gif') :
			call = convertgif(filename=filename, out='gif.mp4')

		elif urllower.endswith('.swf') :
			call = convertswf(filename=filename, out='gif.mp4')

		if os.path.isfile('gif.mp4') : # check to make sure the file exists
			finalsize = os.path.getsize('gif.mp4') / 1024
			if finalsize > 1 : return finalsize # return the size of the converted file (and divide by 1024 to get kilobytes)
		# if the file doesn't exist, clearly conversion failed
		print('failed. ( ', call ,' )', sep='', flush=True)
		return False
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		return False

def convertmp4(filename='temp.mp4', out='gifify.mp4') :
	global length
	global bitrate
	global quality
	global inputoptions
	global estimatedsize
	width = 1920  # assume worst case scenarios
	height = 1080
	misc = '-pix_fmt yuv420p'
	quality = '4000'
	filesize = None
	estimatedsize = -1
	bitrate, width, height, length, filesize = FFprobe(filename)
	rescale = False
	if width > 1280 and width >= height :
		misc = misc + ' -vf scale=1280:-2'
		rescale = True
	elif height > 1280 and height > width :
		misc = misc + ' -vf scale=-2:1280'
		rescale = True
	estimatedsize = (bitrate/8192)*length
	if float(userquality) > 0 :
		quality = userquality + 'k'
		estimatedsize = length * float(userquality)/8
		print('(compressing, ', round(length, 2), 's @ ', quality, 'b/s)...', sep='', end='', flush=True)
		quality = '-b:v ' + quality
	elif rescale or estimatedsize > 8000 : # estimating final size to determine if it should be compressed
		quality = 66000 / length
		if quality > 8000 : quality = 8000
		estimatedsize = length * float(quality)/8
		quality = str(quality) + 'k'
		print('(compressing, ', round(length, 2), 's @ ', quality, 'b/s)...', sep='', end='', flush=True)
		quality = '-b:v ' + quality
	elif endtime > 0 or starttime > 0 :
		quality = '-c copy'
		print('(cutting to ', round(length, 2), 's, lossless)...', sep='', end='', flush=True)
	else : quality = '-c copy'
	call = 'ffmpeg ' + inputoptions + ' -i ' + filename + ' ' + quality + ' ' + misc + ' -loglevel quiet -an ' + out + ' -y'
	subprocess.call(call.split())
	return call

def convertwebm(filename='temp.webm', out='gifify.mp4') :
	global length
	global bitrate
	global quality
	global inputoptions
	global estimatedsize
	width = 1920  # assume worst case scenarios
	height = 1080
	misc = '-pix_fmt yuv420p'
	quality = '4000'
	filesize = None
	estimatedsize = -1
	bitrate, width, height, length, filesize = FFprobe(filename)
	if width > 1280 and width >= height :
		misc = misc + ' -vf scale=1280:-2'
	elif height > 1280 and height > width :
		misc = misc + ' -vf scale=-2:1280'
	elif width % 2 != 0 or height % 2 != 0 :
		misc = misc + ' -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"'
	estimatedsize = length * float(quality)/8
	if float(userquality) > 0 :
		quality = userquality
		estimatedsize = length * float(userquality)/8
	elif estimatedsize > 8000 : # estimating final size to determine if it should be compressed
		quality = str(63500 / length) # ~65,000 seems to work best to keep it under 8mb
		if float(quality) > 8000 : quality = 8000
		estimatedsize = length * float(quality)/8
		quality = str(quality)
	elif length == 1 and filesize/8192 > 8000 :
		quality = '1500' # when there's no way to estimate what the bitrate or length is use 1500 as a happy medium
		estimatedsize = 1
	
	print('(compressing, ', round(length, 2), 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
	call = 'ffmpeg ' + inputoptions + ' -i ' + filename + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an ' + out + ' -y'
	subprocess.call(call.split())
	return call

def convertmov(filename='temp.mov', out='gifify.mp4') :
	global length
	global bitrate
	global quality
	global inputoptions
	global estimatedsize
	width = 1920  # assume worst case scenarios
	height = 1080
	misc = '-pix_fmt yuv420p'
	quality = '4000'
	filesize = None
	estimatedsize = -1
	bitrate, width, height, length, filesize = FFprobe(filename)
	if width > 1280 and width >= height :
		misc = misc + ' -vf scale=1280:-2'
	elif height > 1280 and height > width :
		misc = misc + ' -vf scale=-2:1280'
	elif width % 2 != 0 or height % 2 != 0 :
		misc = misc + ' -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"'
	estimatedsize = length * float(quality)/8
	if float(userquality) > 0 :
		quality = userquality
		estimatedsize = length * float(userquality)/8
	elif estimatedsize > 8000 : # estimating final size to determine if it should be compressed
		quality = str(64000 / length) # ~65,000 seems to work best to keep it under 8mb
		if float(quality) > 8000 : quality = 8000
		estimatedsize = length * float(quality)/8
		quality = str(quality)
	elif length == 1 and filesize/8192 > 8000 :
		quality = '1500' # there's no way to estimate what the bitrate or length is, so 1500 seems like a happy medium between quality and likelyhood the result will be under 10mb
		estimatedsize = 1
	print('(compressing, ', round(length, 2), 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
	call = 'ffmpeg ' + inputoptions + ' -i ' + filename + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an ' + out + ' -y'
	subprocess.call(call.split())
	return call

def convertgif(filename='temp.gif', out='gifify.mp4') :
	global length
	global bitrate
	global quality
	global inputoptions
	global estimatedsize
	width = 1920  # assume worst case scenarios
	height = 1080
	misc = '-pix_fmt yuv420p'
	quality = '4000'
	filesize = None
	estimatedsize = -1
	bitrate, width, height, length, filesize = FFprobe(filename)
	if width > 1280 and width >= height :
		misc = misc + ' -vf scale=1280:-2'
	elif height > 1280 and height > width :
		misc = misc + ' -vf scale=-2:1280'
	elif width % 2 != 0 or height % 2 != 0 :
		misc = misc + ' -vf pad=ceil(iw/2)*2:ceil(ih/2)*2'
	estimatedsize = length * float(quality)/8
	if float(userquality) > 0 :
		quality = userquality
		estimatedsize = length * float(userquality)/8
	elif estimatedsize > 8000 : # estimating final size to determine if it should be compressed
		quality = str(68000 / length) # ~68,000 seems to work best to keep it under 8MB
		estimatedsize = 8000 # 80,000 / 8
	print('(compressing, ', round(length, 2), 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
	call = 'ffmpeg ' + inputoptions + ' -i ' + filename + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an ' + out + ' -y'
	#print('( ' + call, end=' )...')
	subprocess.call(call.split())
	return call

def convertswf(filename='temp.swf', out='gifify.mp4') :
	global length
	global bitrate
	global quality
	global inputoptions
	global estimatedsize
	width = 1920  # assume worst case scenarios
	height = 1080
	misc = '-pix_fmt yuv420p'
	quality = '4000'
	filesize = None
	estimatedsize = -1
	bitrate, width, height, length, filesize = FFprobe(filename)
	if width > 1280 and width >= height :
		misc = misc + ' -vf scale=1280:-2'
	elif height > 1280 and height > width :
		misc = misc + ' -vf scale=-2:1280'
	elif width % 2 != 0 or height % 2 != 0 :
		misc = misc + ' -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2"'
	estimatedsize = length * float(quality)/8
	if float(userquality) > 0 :
		quality = userquality
		estimatedsize = length * float(userquality)/8
	elif estimatedsize > 8000 : # estimating final size to determine if it should be compressed
		quality = str(63500 / length) # ~65,000 seems to work best to keep it under 8mb
		if float(quality) > 8000 : quality = 8000
		estimatedsize = length * float(quality)/8
		quality = str(quality)
	elif length == 1 and filesize/8192 > 8000 :
		quality = '1500' # when there's no way to estimate what the bitrate or length is use 1500 as a happy medium
		estimatedsize = 1
	print('(compressing, ', round(length, 2), 's @ ', quality, 'kb/s)...', sep='', end='', flush=True)
	call = 'ffmpeg ' + inputoptions + ' -i ' + filename + ' -b:v ' + quality + 'k ' + misc + ' -loglevel quiet -an ' + out + ' -y'
	subprocess.call(call.split())
	return call

def downloadfile(url, filename) :
	response = requests.get(url, stream=True) # stream=True IS REQUIRED
	if response.status_code == 200 :
		with open(filename, 'wb') as tobegif :
			shutil.copyfileobj(response.raw, tobegif)
		return True
	return False
	

def FFprobe(filename) :
	global endtime
	global starttime
	global userlength
	bitrate = -1 # set defaults as worst-case scenario
	length = 1
	width = 1920
	height = 1080
	filesize = None
	try :
		call = 'ffprobe -v quiet -print_format json -show_streams ' + filename
		ffprobe = subprocess.check_output(call.split()).decode('utf-8')
		ffprobe = json.loads(ffprobe)
		for i in range(len(ffprobe['streams'])) :
			if 'codec_type' in ffprobe['streams'][i] and ffprobe['streams'][i]['codec_type'] == 'video' : # ffprobe shows gif codec type as being video, so this still works
				if 'bit_rate' in ffprobe['streams'][i] :
					bitrate = int(ffprobe['streams'][i]['bit_rate'])
				if 'width' in ffprobe['streams'][i] and ffprobe['streams'][i]['width'] > 0 :
					width = int(ffprobe['streams'][i]['width'])
				if 'height' in ffprobe['streams'][i] and ffprobe['streams'][i]['height'] > 0 :
					height = int(ffprobe['streams'][i]['height'])
				if 'tags' in ffprobe['streams'][i] and 'DURATION' in ffprobe['streams'][i]['tags'] :
					length = getsecondsfromtimecode(ffprobe['streams'][i]['tags']['DURATION'])
				if 'duration' in ffprobe['streams'][i] :
					length = float(ffprobe['streams'][i]['duration']) # already seconds
			if 'codec_type' in ffprobe['streams'][i] and ffprobe['streams'][i]['codec_type'] == 'audio' :
				if 'tags' in ffprobe['streams'][i] and 'DURATION' in ffprobe['streams'][i]['tags'] :
					length = getsecondsfromtimecode(ffprobe['streams'][i]['tags']['DURATION'])
				if 'duration' in ffprobe['streams'][i] :
					length = float(ffprobe['streams'][i]['duration']) # already seconds
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')

	filesize = os.path.getsize(filename) * 8 # convert to bits
	if bitrate < 0 :
		bitrate = filesize / length
	if filename.endswith('.gif') :
		with PIL.GifImagePlugin.GifImageFile(fp=filename) as gif :
			#print(gif.info)
			length = (gif.n_frames + 1) * gif.info['duration'] / 1000 # divide by 1000 to get seconds
			bitrate = filesize / length
			width, height = gif.size
	if length == 1 :
		length = userlength
	if endtime > 0 :
		length = endtime - starttime
	elif starttime > 0 :
		length = length - starttime
	return bitrate, width, height, length, filesize

def prettysize(filesize) :
	if filesize > 1000 : return str(round(filesize / 1024, 2)) + 'MB'
	else : return str(round(filesize, 2)) + 'KB'

def percent(numerator, denominator) :
	return round(numerator * 100 / denominator, 2)

def istimecodeformat(timecode) :
	try :
		timecode = timecode.split(':')
		for potentialfloat in timecode :
			if IsFloat(potentialfloat) is None : return False
		return True
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
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
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		return 1

def linkonly(url) :
	global acceptedtypes
	url = url.split('?')[0] # remove any extraneous information after and including ?, if there is one
	urllower = url.lower()
	for extension in acceptedtypes :
		if urllower.endswith('.' + extension) : return url
	if '//twitter.com' in url and '/status/' in url :
		return getvideourl(url)
	elif urllower.endswith('.gifv') :
		return url[:-4] + 'mp4' # replace 'gifv' extension with 'mp4'
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
			if response is not None :
				return 'https://api.telegram.org/file/bot' + token + '/' + response['result']['file_path']

def parseformedia(url) :
	try: 
		session = HTMLSession()
		page = session.get(url)
		source = None # search gif first, since they're more likely to appear on a page as 'filler' than videos, so the videos will override if found
		for sourcetype in ['img[src*=".gif"]', 'object[data*=".swf"]', 'embed[src*=".swf"]', 'source[src*=".mov"]', 'source[src*=".webm"]', 'source[src*=".mp4"]'] :
			temp = page.html.find(sourcetype, first=True)
			if temp is not None : source = temp
		if 'src' in source.attrs : return source.attrs['src']
		if 'data' in source.attrs : return source.attrs['data']
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
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
				return response['description']
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		print(response, end='\n\n')

def checkresponsetime(response, starttime) :
	try :
		response = response.json()
		if response['ok'] :
			print('success. ( ', round(time.time() - starttime, 2), 's )', sep='')
			return response
		else :
			print('failed.')
			if 'description' in response :
				print('reason: ' + response['description'])
				return response['description']
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		print(response, end='\n\n')

		
def checkresponsesilent(response) :
	try :
		response = response.json()
		if not response['ok'] :
			print('\rfailed.', end='')
			if 'description' in response : print(' reason: ' + response['description'])
			else : print()
			return None
		return response
	except Exception as e :
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print('\r( ' + colorama.Fore.LIGHTRED_EX + 'error' + colorama.Style.RESET_ALL + ': ', e, ', line:', exc_tb.tb_lineno, ' )...', sep='', end='')
		print(response, end='')
		return None

def donothing() :
	pass

def reset() :
	global endtime
	global starttime
	global userquality
	starttime = 0
	userquality = 0
	endtime = 0

def parsequery(query, url, command) :
	global endtime
	global starttime
	global userlength
	global userquality
	global inputoptions
	inputoptions = ''
	starttime = 0
	userquality = 0
	endtime = 0
	userlength = 1 # default
	if len(query) > 0 :
		if command == '' and query[0][0] != '/' :
			command = 'linkonly'

		for j in range(len(query)) :
			if len(query[j]) >= 4 and query[j].startswith('http') :
				url = query[j]
			elif query[j] == 'length' and len(query) > j+1 :
				userlength = getsecondsfromtimecode(query[j+1])
				j = j + 1
			elif 'length=' in query[j] :
				queryj = query[j].split('=')
				if len(queryj) >= 2 : userlength = getsecondsfromtimecode(queryj[1])
			elif query[j] == 'bitrate' and len(query) > j+1 and istimecodeformat(query[j+1]) :
				userquality = query[j+1]
				j = j + 1
			elif 'bitrate=' in query[j] :
				queryj = query[j].split('=')
				if len(queryj) >= 2 and istimecodeformat(queryj[1]) : userquality = queryj[1]
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
				userlength = getsecondsfromtimecode(query[j])
	return url, command

def getpercentandcolors(finalsize, estimatedsize) :
	pcent = percent(finalsize, estimatedsize)
	color = ''
	if pcent > 102.4 : color = colorama.Fore.LIGHTRED_EX
	elif pcent < 100 : color = colorama.Fore.LIGHTGREEN_EX
	finalcolor = ''
	if finalsize > 8000 : finalcolor = colorama.Fore.LIGHTRED_EX
	return pcent, color, finalcolor

if __name__ == '__main__' :
	global api
	global token
	global endtime
	global starttime
	global userlength
	global userquality
	global inputoptions
	global estimatedsize
	global acceptedtypes
	giffer = sys.modules[__name__]
	colorama.init()

	# telegram bot auth token (given by @BotFather upon your bot's creation)
	token = None

	# the id of the bot itself
	botID = None

	# initialize twitter
	api = None

	# credentials = {
	# 	"telegramAccessToken" : "yyyyyyyyy:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
	# 	"telegramBotID" : yyyyyyyyy,
	# 	"twitter" : {
	# 		"consumerKey" : "xxxxxxxxxxxxxxxxxxxxxxxxx",
	# 		"consumerSecret" : "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
	# 		"accessTokenKey" : "yyyyyyyyyyyyyyyyyyy-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
	# 		"accessTokenSecret" : "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
	# 	}
	# }
	# credentials are saved in credentials.json in the format above (twitter not required)

	print('loading credentials...', end='', flush= True)
	with open('credentials.json') as userinfo :
		credentials = json.load(userinfo)
		token = credentials['telegramAccessToken']
		botID = credentials['telegramBotID']
		try : api = twitter.Api(consumer_key = credentials['twitter']['consumerKey'], consumer_secret = credentials['twitter']['consumerSecret'], access_token_key = credentials['twitter']['accessTokenKey'], access_token_secret = credentials['twitter']['accessTokenSecret'], tweet_mode='extended')
		except : print(' (failed to initialize twitter)... ', end='', flush= True)
		#print(json.dumps(credentials, indent=2))
	print('success.\n')

	if len(sys.argv) > 1 :
		parsequery(sys.argv[2:], sys.argv[1], '/localfile')
		print('converting...', end='', flush=True)
		finalsize = convertlocalfile(sys.argv[1])
		if finalsize :
			pcent, color, finalcolor = getpercentandcolors(finalsize, estimatedsize)
			print('success. ( ' + finalcolor, prettysize(finalsize), colorama.Style.RESET_ALL + '/', prettysize(estimatedsize), ': ' + color, pcent, '%' + colorama.Style.RESET_ALL + ' )' , sep='')
			print('saved as gif.mp4')
		exit(0)

	loadloop = ['|', '/', '―', '\\'] # replace with whatever text-based loading icons you want

	# don't touch these
	loadframes = len(loadloop) - 1
	loadindex = 0

	commands = ['linkonly', 'geturlfromdocument']
	othercommands = ['start', 'help']
	acceptedtypes = ['webm', 'mp4', 'gif', 'mov', 'swf']
	
	mostrecentupdate = 0
	while (True) :
		request = 'https://api.telegram.org/bot' + token + '/getUpdates'
		print(colorama.Fore.CYAN + '\r' + loadloop[loadindex] + ' ', end=colorama.Style.RESET_ALL)
		loadindex = loadindex + 1
		if loadindex > loadframes : loadindex = 0

		response = ''
		try : response = requests.get(request + '?offset=' + str(mostrecentupdate + 1))
		except KeyboardInterrupt :
			print('\rdone.', end='')
			exit(0)
		except : donothing() # sometimes this crashes for no reason
		updateList = checkresponsesilent(response)
		if updateList :
			updateList = updateList['result']
			if len(updateList) > 0 :
				print('\rupdates:', len(updateList))
				for i in range(len(updateList)) :
					#if 'query' in updateList[i] and 'status' in updateList[i]['query'] : # FOR INLINE
					#	get_video_url(updateList[i]['query'])
					if 'message' in updateList[i] :
						if 'text' in updateList[i]['message'] or 'document' in updateList[i]['message'] or 'video' in updateList[i]['message'] :
							commandstarttime = time.time()
							url = ''
							command = ''
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
							elif 'video' in updateList[i]['message'] :
								command = 'geturlfromdocument'
								url = updateList[i]['message']['video']
								if 'caption' in updateList[i]['message'] :
									query = updateList[i]['message']['caption'].split(' ')
								else : query = []

							if len(query) > 0 and query[0][0] == '/' :
								command = query[0][1:] # remove the slash

							print(query, time.ctime(commandstarttime))
							url, command = parsequery(query, url, command)

							if command in commands :
								method = getattr(giffer, command)
								print('retrieving url...', end='', flush=True)
								videourl = method(url)
								if videourl is not None :
									print('success. (', videourl, ')')
									
									print('converting to gif...', end='', flush=True)
									finalsize = converturltogif(videourl)
									if finalsize : #and finalsize > 1 : # a gif should be at least 1KB, makes sure ffmpeg didn't leave an empty file or something
										pcent, color, finalcolor = getpercentandcolors(finalsize, estimatedsize)										
										print('success. ( ' + finalcolor, prettysize(finalsize), colorama.Style.RESET_ALL + '/', prettysize(estimatedsize), ': ' + color, pcent, '%' + colorama.Style.RESET_ALL + ' )' , sep='')
										print('sending gif...', end='', flush=True)
										if command == 'linkonly' :
											request = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&caption=' + url.replace('?', '%3F')
										else :
											request = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id'])
										with open('gifify.mp4', 'rb') as gif :
											telegramfile = {'document': gif}
											sentFile = requests.get(request, files=telegramfile)
											checkresponsetime(sentFile, commandstarttime)
										os.remove('gifify.mp4') # delete file to prevent sending the wrong file in the future
									else :
										print('apologizing...', end='', flush=True)
										request = 'https://api.telegram.org/bot' + token + '/sendMessage'
										text = 'Sorry, I wasn\'t able to convert that!'
										response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&text=' + text)
										checkresponse(response)
										print(updateList[i])
								else :
									print('failed. ( /', command, ' ', url,' )', sep='', flush=True)
									print('apologizing...', end='', flush=True)
									request = 'https://api.telegram.org/bot' + token + '/sendMessage'
									text = 'Sorry, I don\'t support that filetype yet!\n\nTo see what I can do, try /start'
									if 't.co' in url : text = 'I\'m sorry, I can\'t convert shortened urls! Can you send the full url?\nie: `https://twitter.com/user/status/0000000000000000000000`&parse_mode=Markdown'
									response = requests.get(request + '?chat_id=' + str(updateList[i]['message']['from']['id']) + '&reply_to_message_id=' + str(updateList[i]['message']['message_id']) + '&text=' + text)
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
					else :
						print(updateList[i])
							
				# clear update list
				mostrecentupdate = updateList[-1]['update_id']
			else : time.sleep(1) # wait a second before trying again 
		else : time.sleep(1) # an error, or the update list is empty
	# end while loop

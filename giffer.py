import os
import sys
import time
import json
import shutil
import twitter
import requests
from subprocess import call

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
			if IsInt(url[i]) :
				return url[i]
	return False

def getvideourl(url) :
	global api
	global length
	print(' (', url, ') ', end='')
	status = getstatusfromurl(url)
	status = api.GetStatus(status)
	#with open('status.json','w') as f : # debug
	#	f.write(str(json.dumps(json.loads(str(status)), indent=2)))
	status = status.AsDict()
	largest = 0
	largestindex = -1
	if 'media' in status and 'video_info' in status['media'][0] : 
		length = status['media'][0]['video_info']['duration_millis'] / 1000 # for seconds
		for i in range(len(status['media'][0]['video_info']['variants'])) :
			if status['media'][0]['video_info']['variants'][i]['content_type'] == 'application/x-mpegURL' :
				return status['media'][0]['video_info']['variants'][i]['url']
			elif status['media'][0]['video_info']['variants'][i]['bitrate'] > largest :
				largest = status['media'][0]['video_info']['variants'][i]['bitrate']
				largestindex = i
		if largestindex == -1 :
			return url
		else :
			return status['media'][0]['video_info']['variants'][largestindex]['url']

def converturltogif(url) :
	global length
	quality = '-c copy'
	if length > 30 : 
		quality =  '-b:v ' + str(75000 / length) + 'k' # 75,000 seems to work best to keep it under 10mb and 
	if '.m3u8' in url :
		call('ffmpeg -i ' + url + ' ' + quality + ' -an tempgif.mp4 -y')
		return True
	elif '.mp4' in url :
		response = requests.get(url, stream=True) # stream=True IS REQUIRED
		if response.status_code == 200 :
			with open('temp.mp4', 'wb') as tobegif :
				shutil.copyfileobj(response.raw, tobegif)
		print('saved as temp.mp4')
		call('ffmpeg -i temp.mp4 ' + quality + ' -an tempgif.mp4 -y')
		return True

def isURLvalid(url) :
	if '//twitter.com' in url and '/status/' in url :
		return True
	return False

if __name__ == "__main__" :
	global api
	global token
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
	print('success.')

	maxloops = 10000 # for debugging, so it doesn't run forever

	loops = 0
	mostrecentupdate = 0
	while (loops < maxloops) :
		request = 'https://api.telegram.org/bot' + token + '/getUpdates'
		print('sending request...', end='', flush=True)
		response = requests.get(request + '?offset=' + str(mostrecentupdate + 1))
		response = response.json()
		print('success.')
		if response['ok'] :
			updateList = response['result']
			if len(updateList) > 0 :
				print('updates:', len(updateList))
				for i in range(len(updateList)) :
					#if 'query' in updateList[i] and 'status' in updateList[i]['query'] : # FOR INLINE
					#	get_video_url(updateList[i]['query'])
					if 'message' in updateList[i] and 'text' in updateList[i]['message'] and 'status' in updateList[i]['message']['text'] :
						if 'from' in updateList[i]['message'] :
							if 'username' in updateList[i]['message']['from'] :
								print('(from ', updateList[i]['message']['from']['username'], ')', sep='')
							else :
								print('(from ', updateList[i]['message']['from']['first_name'], ' (', updateList[i]['message']['from']['id'], '))', sep='')

						query = updateList[i]['message']['text'].split(' ')
						if len(query) == 1 and updateList[i]['message']['text'][0] is not '/' :
							command = 'getvideourl'
							url = query[0]
						else :
							command = query[0][1:] # remove the slash
							url = query[1]

						if hasattr(giffer, command) and isURLvalid(url) :
							method = getattr(giffer, command)
							print('retrieving url...', end='', flush=True)
							videourl = method(url)
							if videourl is not None :
								print('success. (', videourl, ')')
								
								print('converting to gif...', end='', flush=True)
								if converturltogif(videourl) :
									print('success.')
									print('sending gif...', end='', flush=True)
									request = 'https://api.telegram.org/bot' + token + '/sendDocument?chat_id=' + str(updateList[i]['message']['from']['id'])
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
							
				# clear update list
				mostrecentupdate = updateList[-1]['update_id']
		else :
			print('response not ok:', response)
			# wait a second before trying again
		loops = loops + 1
		#time.sleep(10)
	
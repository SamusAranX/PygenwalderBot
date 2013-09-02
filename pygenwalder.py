#!/usr/bin/env python
# -- coding: utf-8 --

import os, sys, logging, random, re
import tweetpony
from time import strftime
from terminalsize import get_terminal_size

logging.getLogger("requests").setLevel(logging.WARNING) #Disable Requests' log spam
logging.basicConfig(filename="pygenwalder.log", level=logging.DEBUG)
logger = logging.getLogger()

ts = get_terminal_size()
twidth = ts[0]

#https://dev.twitter.com/discussions/19096 #hooray for unicode

title = "PygenwalderBot"

consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

responses = ["Rügenwalder.", "Teewurst?", "Diese hier?", "Die mit der Mühle.", "Alle."]
keywords = ["teewurst", "rügenwalder", "rugenwalder", "ruegenwalderbot"]
ignoredusers = []

randomresponse = ""
def get_random_response():
	global randomresponse
	ret = random.choice(responses)
	if ret == randomresponse:
		ret = get_random_response()

	randomresponse = ret

	return ret

class StreamProcessor(tweetpony.StreamProcessor):
	def on_limit(self, event):
		print event

	def on_friends(self, friends):
		pass

	def on_unknown_entity(self, entity):
		print entity

	def on_status(self, status):
		global ignoredusers

		screen_name = status.user.screen_name
		screen_name_lower = screen_name.lower()
		tweet = status.text
		ltweet = tweet.lower()
		tweetid = status.id

		isignored = screen_name_lower in ignoredusers
		isretweet = ltweet[:2] == "rt"
		# ismatched = any(r.decode("utf8") in ltweet for r in keywords)
		ismention = ltweet[:16] == "@ruegenwalderbot"
		iscommand = (ismention and screen_name == "SamusAranX") or (ismention and screen_name == "PythonIsWeird")

		print isignored
		print isretweet
		print ismention
		print iscommand

		debug = False

		if debug:
			pass
		else:
			if iscommand and not isretweet:
				print format_tweet(tweet, screen_name)
				if tweet[17:23] == "IGNORE":
					ignore_name = tweet[24:].replace("@", "")
					ignore_name_lower = ignore_name.lower()
					ignoredusers.append(ignore_name_lower)
					write_ignorelist(ignoredusers)
					print "@" + ignore_name + " will be ignored."
				elif tweet[17:25] == "UNIGNORE":
					unignore_name = tweet[26:].replace("@", "")
					unignore_name_lower = unignore_name.lower()
					if unignore_name_lower in ignoredusers:
						ignoredusers.remove(unignore_name_lower)
						write_ignorelist(ignoredusers)
						print "@" + unignore_name + " won't be ignored anymore"
				else:
					print "Unknown command: " + format_tweet(tweet)[17:]
			elif isignored and not isretweet:
				print format_tweet(tweet, screen_name)
				if ismention:
					if tweet[17:25] == "UNIGNORE":
						if screen_name_lower in ignoredusers:
							ignoredusers.remove(screen_name_lower)
							write_ignorelist(ignoredusers)
							print "@" + screen_name + " won't be ignored anymore"
					else:
						print "@" + screen_name + " is being ignored."
				else:
					print "@" + screen_name + " is being ignored."
			elif not isignored and not isretweet:
				print format_tweet(tweet, screen_name)
				if ismention:
					if tweet[17:23] == "IGNORE":
						ignoredusers.append(screen_name_lower)
						write_ignorelist(ignoredusers)
						print "@" + screen_name + " will be ignored."
					else:
						try:
							randomresponse = get_random_response()
							self.api.update_status(status = "@" + screen_name + " " + randomresponse, in_reply_to_status_id = tweetid, lat = 53.174425, long = 8.059600, place_id = "Rügenwalder Mühle")
							print "Responded with " + randomresponse
						except tweetpony.APIError as err:
							print "Couldn't reply to tweet: Twitter returned error #%i: %s" % (err.code, err.description)
				else:
					try:
						self.api.retweet(id = tweetid)
						print "Retweeted."
					except tweetpony.APIError as err:
						print "Couldn't retweet tweet: Twitter returned error #%i: %s" % (err.code, err.description)
			else:
				print format_tweet(tweet, screen_name)
				print "wat do"


	def on_error(self, status):
		print "ERROR"
		print status #how do i error handling
		logging.error(status)

	def on_disconnect(self, event):
		logging.debug("Disconnect: " + str(event))

def format_tweet(twt, scr_name = None):
	if scr_name == None:
		return twt.encode("utf8")
	else:
		return "@" + scr_name.encode("utf8") + ": " + twt.encode("utf8")

def main():
	global ignoredusers
	print "".center(twidth, "-")
	print title.center(twidth, "-")
	print "".center(twidth, "-")

	try:
		try:
			with open(os.path.expanduser("~/Documents/PygenwalderBot/tokens.txt")) as f:
				tokens = f.readlines()
				consumer_key = tokens[0].strip()
				consumer_secret = tokens[1].strip()
				access_token = tokens[2].strip()
				access_token_secret = tokens[3].strip()
		except IOError:
			with open("tokens.txt") as f:
				tokens = f.readlines()
				consumer_key = tokens[0].strip()
				consumer_secret = tokens[1].strip()
				access_token = tokens[2].strip()
				access_token_secret = tokens[3].strip()

		print "Tokens read."
	except IOError:
		print "Couldn't find any tokens. Make sure there's a tokens.txt containing valid tokens."
		logging.error("Couldn't find any tokens. Make sure there's a tokens.txt containing valid tokens.")
		sys.exit(1)

	try:
		try:
			with open(os.path.expanduser("~/Documents/PygenwalderBot/ignoredusers.txt")) as f:
				ignoredusers = [x.strip() for x in f.readlines()]
		except IOError:
			with open("ignoredusers.txt") as f:
				ignoredusers = [x.strip() for x in f.readlines()]
		print "Ignored Users:"
		print ", ".join(ignoredusers)
		print "Keywords:"
		print ", ".join(keywords)
	except IOError:
		print "No ignored users."

	api = tweetpony.API(consumer_key, consumer_secret, access_token, access_token_secret)
	processor = StreamProcessor(api)
	try:
		print "Initiating Stream."
		# api.user_stream(processor = processor, track = ",".join(keywords), replies = "all", language = "de")
		api.user_stream(processor = processor, track = ",".join(keywords), replies = "all")
		print "End of Stream."
		logging.debug("End of Stream.")
		sys.exit(1)
	except KeyboardInterrupt:
		logging.info("KeyboardInterrupt!")
		raise
	except SystemExit:
		pass
	except:
		print "Unexpected error: "
		print sys.exc_info()[0]
		print sys.exc_info()[1]
		logging.error("Unexpected error: " + str(sys.exc_info()[0]) + " - " + str(sys.exc_info()[1]))

def write_ignorelist(list):
	try:
		f = open(os.path.expanduser("~/Documents/PygenwalderBot/ignoredusers.txt", "w"))
	except IOError:
		f = open("ignoredusers.txt", "w")
	for x in list:
		print x
		f.write("\n".join(ignoredusers))
	f.close()
	print "Ignore list overwritten"

if __name__ == "__main__":
	main()
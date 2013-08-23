#!/usr/bin/env python
# -- coding: utf-8 --

# Skript zum Testen der Twitter-API

import os, sys, logging, random
import tweetpony
from time import strftime
from terminalsize import get_terminal_size

logging.getLogger("requests").setLevel(logging.WARNING) #Logspam von Requests unterbinden
logging.basicConfig(filename="streamtest.log", level=logging.DEBUG)
logger = logging.getLogger()

ts = get_terminal_size()
twidth = ts[0]

#https://dev.twitter.com/discussions/19096 #hooray for unicode

title = "StreamTest"

consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

keywords = ["cdu", "csu", "piraten", "fdp", "grüne", "linke", "npd", "spd"]

# print sys.stdout.encoding

class StreamProcessor(tweetpony.StreamProcessor):
	def on_limit(self, event):
		print event

	def on_friends(self, friends):
		pass

	def on_unknown_entity(self, entity):
		print entity

	def on_status(self, status):
		screen_name = status.user.screen_name
		screen_name_lower = screen_name.lower()
		tweet = status.text.lower()

		if tweet.lower()[:2] != "rt":
			print "@" + status.user.screen_name.encode("utf8") + ": " + status.text.encode("utf8")
		# print type(status.user.screen_name) #ist unicode
		# print type(status.text) #ist unicode

	def on_error(self, status):
		print "ERROR"
		print status #how do i error handling
		logging.error(status)

	def on_disconnect(self, event):
		logging.debug("Disconnct: " + str(event))

def main():
	print "".center(twidth, "-")
	print title.center(twidth, "-")
	print "".center(twidth, "-")

	try:
		with open("tokens.txt") as f:
			tokens = f.readlines()
			consumer_key = tokens[0].strip()
			consumer_secret = tokens[1].strip()
			access_token = tokens[2].strip()
			access_token_secret = tokens[3].strip()
		print "Tokens gelesen."
	except IOError:
		print "Konnte keine Tokens finden. Stell sicher, dass es eine tokens.txt mit gültigen Tokens gibt."
		logging.error("Konnte keine Tokens finden. Stell sicher, dass es eine tokens.txt mit gültigen Tokens gibt.")
		sys.exit(1)

	api = tweetpony.API(consumer_key, consumer_secret, access_token, access_token_secret)
	processor = StreamProcessor(api)
	try:
		# api.filter_stream(processor = processor, track = ",".join(keywords), language = "de-de" )
		api.user_stream(processor = processor, track = ",".join(keywords), replies = "all", language = "de") #https://dev.twitter.com/discussions/19096
		print "Fuck."
		logging.debug("Stream beendet.")
		sys.exit(1)
	except KeyboardInterrupt:
		logging.info("KeyboardInterrupt!")
		raise
	except SystemExit:
		pass
	except:
		print "Fuck."
		print "Unexpected error: ", sys.exc_info()[0]
		logging.debug("Unexpected error:" + str(sys.exc_info()[0]))

if __name__ == "__main__":
	main()
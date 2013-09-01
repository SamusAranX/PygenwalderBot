#!/usr/bin/env python
# -- coding: utf-8 --

import os, sys, logging, random, re
import tweetpony
from time import strftime
from terminalsize import get_terminal_size

logging.getLogger("requests").setLevel(logging.WARNING) #Logspam von Requests unterbinden
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
		screen_name = status.user.screen_name
		screen_name_lower = screen_name.lower()
		tweet = status.text
		ltweet = tweet.lower()
		tweetid = status.id

		isignored = screen_name_lower in ignoredusers
		isretweet = ltweet[:2] == "rt"
		# ismatched = any(r.decode("utf8") in ltweet for r in keywords)
		ismention = ltweet[:16] == "@ruegenwalderbot"
		iscommand = ismention and screen_name == "SamusAranX"

		if iscommand and not isretweet:
			if tweet[17:23] == "IGNORE":
				print tweet[24:]
			elif tweet[17:25] == "UNIGNORE":
				print tweet[26:]
			else:
				print "Unknown command: " + tweet
		elif isignored and not isretweet:
			print_tweet(screen_name, tweet)
			if ismention:
				if tweet[17:25] == "UNIGNORE":
					if screen_name_lower in ignoredusers:
						ignoredusers.remove(screen_name_lower)
						write_ignorelist(ignoredusers)
						print "@" + screen_name + " wird nicht mehr ignoriert"
				else:
					print "@" + screen_name + " wird ignoriert."
			else:
				print "@" + screen_name + " wird ignoriert."
		elif not isignored and not isretweet:
			print_tweet(screen_name, tweet)
			if ismention:
				if tweet[17:23] == "IGNORE":
					ignoredusers.append(screen_name_lower)
					write_ignorelist(ignoredusers)
					print "@" + screen_name + " wird jetzt ignoriert"
				else:
					try:
						randomresponse = get_random_response()
						self.api.update_status(status = "@" + screen_name + " " + randomresponse, in_reply_to_status_id = tweetid, lat = 53.174425, long = 8.059600, place_id = "Rügenwalder Mühle")
						print "Antwortete mit " + randomresponse
					except tweetpony.APIError as err:
						print "Konnte nicht auf Tweet antworten: Twitter gab Fehler #%i zurück: %s" % (err.code, err.description)
			else:
				try:
					self.api.retweet(id = tweetid)
					print "Retweetet."
				except tweetpony.APIError as err:
					print "Konnte Tweet nicht retweeten: Twitter gab Fehler #%i zurück: %s" % (err.code, err.description)
		# elif isretweet:
		# 	print "Retweet, don't handle"
		else:
			print_tweet(screen_name, tweet)
			print "Dunno what to do"


	def on_error(self, status):
		print "ERROR"
		print status #how do i error handling
		logging.error(status)

	def on_disconnect(self, event):
		logging.debug("Disconnect: " + str(event))

def print_tweet(screen_name, tweet):
	print "@" + screen_name.encode("utf8") + ": " + tweet.encode("utf8")

def main():
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

		print "Tokens gelesen."
	except IOError:
		print "Konnte keine Tokens finden. Stell sicher, dass es eine tokens.txt mit gültigen Tokens gibt."
		logging.error("Konnte keine Tokens finden. Stell sicher, dass es eine tokens.txt mit gültigen Tokens gibt.")
		sys.exit(1)

	try:
		try:
			with open(os.path.expanduser("~/Documents/PygenwalderBot/ignoredusers.txt")) as f:
				ignoredusers = [x.strip() for x in f.readlines()]
		except IOError:
			with open("ignoredusers.txt") as f:
				ignoredusers = [x.strip() for x in f.readlines()]
		print "Ignorierte User:"
		print ", ".join(ignoredusers)
		print "Keywords:"
		print ", ".join(keywords)
	except IOError:
		print "Keine ignorierten User."

	api = tweetpony.API(consumer_key, consumer_secret, access_token, access_token_secret)
	processor = StreamProcessor(api)
	try:
		# api.filter_stream(processor = processor, track = ",".join(keywords), language = "de-de" )
		print "Initiating Stream."
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
	# logging.debug("Überschrieb die Ignoreliste")
	print "Überschrieb die Ignoreliste"

if __name__ == "__main__":
	main()
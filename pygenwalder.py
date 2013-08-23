#!/usr/bin/env python
# -- coding: utf-8 --
import os, sys, logging, random, signal
import tweetpony
from time import strftime
from terminalsize import get_terminal_size

logging.getLogger("requests").setLevel(logging.WARNING) #Logspam von Requests unterbinden
logging.basicConfig(filename="pygenwalder.log", level=logging.DEBUG)
logger = logging.getLogger()

ts = get_terminal_size() 
twidth = ts[0] #Eig. immer 80

#https://dev.twitter.com/discussions/19096 #hooray for unicode

title = "PygenwalderBot"

consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

responses = ["Rügenwalder.", "Teewurst?", "Diese hier?", "Die mit der Mühle.", "Alle."]
keywords = ["teewurst", "rügenwalder", "rugenwalder"]
ignoredusers = []

def signal_handler(signal, frame):
	print "\nKeyboardInterrupt!"
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) #Unnötigen Traceback bei Ctrl+C verhindern

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

		print strftime("[%d.%m.%y %H:%M:%S] ") + "Neuer Tweet!"
		
		#Nur fortfahren, wenn der User nicht ignoriert wird und der Tweet kein Retweet ist
		if not screen_name_lower in ignoredusers and tweet[:2] != "RT":
			print "@" + screen_name + " wird nicht ignoriert und Tweet ist kein Retweet"
			if ltweet[:16] == "@ruegenwalderbot": #Ist der Tweet ne Mention?
				if ltweet[17:23] == "ignore":
					print "User will ignoriert werden"
					ignoredusers.append(screen_name_lower)
					write_ignorelist(ignoredusers)
				else:
					print "Tweet ist normale Mention"
					try:
						self.api.update_status(status = "@" + screen_name + " " + random.choice(responses), in_reply_to_status_id = status.id, lat = 53.174425, long = 8.059600, place_id = "Rügenwalder Mühle")
						print strftime("[%d.%m.%y %H:%M:%S] ") + "Rügenwalderte @" + screen_name.encode("utf8")
					except tweetpony.APIError as err:
						print strftime("[%d.%m.%y %H:%M:%S] ") + "Konnte nicht auf Tweet antworten: Twitter gab Fehler #%i zurück: %s" % (err.code, err.description)
						logging.error("Konnte nicht auf Tweet antworten: Twitter gab Fehler #%i zurück: %s" % (err.code, err.description))
			else:
				print "Tweet ist normaler Tweet, der ein Keyword enthält"
				try:
					self.api.retweet(id = status.id)
					print strftime("[%d.%m.%y %H:%M:%S] ") + "Retweetete @" + screen_name.encode("utf8")
				except tweetpony.APIError as err:
					print strftime("[%d.%m.%y %H:%M:%S] ") + "Konnte Tweet nicht retweeten: Twitter gab Fehler #%i zurück: %s" % (err.code, err.description)
					logging.error("Konnte Tweet nicht retweeten: Twitter gab Fehler #%i zurück: %s" % (err.code, err.description))
		elif screen_name_lower in ignoredusers and tweet[:2] != "RT" and tweet[:25] == "@ruegenwalderbot unignore":
			print "@" + screen_name + " wird ignoriert, Tweet ist kein Retweet und User will entignoriert werden"
			print "@" + screen_name.encode("utf8") + ": " + tweet.encode("utf8")
			if screen_name_lower in ignoredusers:
				ignoredusers.remove(screen_name_lower)
				write_ignorelist(ignoredusers)
				print strftime("[%d.%m.%y %H:%M:%S] ") + "@" + screen_name.encode("utf8") + " wurde entignoriert."
		else:
			print "Unbekannt, Tweet einfach so printen"
			print "@" + screen_name.encode("utf8") + ": " + tweet.encode("utf8")

	def on_error(self, status):
		print "ERROR"
		print status #how do i error handling
		# logging.error(status)

	def on_disconnect(self, event):
		# logging.debug("Disconnct: " + str(event))
		pass

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
		# logging.error("Konnte keine Tokens finden. Stell sicher, dass es eine tokens.txt mit gültigen Tokens gibt.")
		sys.exit(1)

	try:
		with open("ignoredusers.txt") as f:
			ignoredusers = [x.strip() for x in f.readlines()]
		print "Ignorierte User:"
		print ", ".join(ignoredusers)
		print "Keywords:"
		print ", ".join(keywords)
	except IOError:
		print "Keine ignorierten User."
		# logging.info("Keine ignorierten User.")

	api = tweetpony.API(consumer_key, consumer_secret, access_token, access_token_secret)
	processor = StreamProcessor(api)
	try:
		api.user_stream(processor = processor, track = ",".join(keywords), replies = "all", language = "de-de") #https://dev.twitter.com/discussions/19096
		print "Stream beendet."
		sys.exit(1)
	except KeyboardInterrupt:
		logging.info("KeyboardInterrupt!")
		raise
	except SystemExit:
		pass
	except:
		print "Fuck."
		print "Unexpected error: ", sys.exc_info()[0]
		# logging.debug("Unexpected error:", sys.exc_info()[0])

def write_ignorelist(list):
	f = open("ignoredusers2.txt", "w")
	for x in list:
		print x
		f.write(x.strip() + "\n")
	f.close()
	# logging.debug("Überschrieb die Ignoreliste")
	print "Überschrieb die Ignoreliste"

if __name__ == "__main__":
	main()
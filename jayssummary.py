# -*- coding: utf-8 -*-
from dateutil import parser
import httplib
import json
from pprint import pprint
from datetime import datetime
import datetime
import collections
import feedparser

# create the html file
# and put in the <head> stuff
fo = open("index.html", "w")
fi = open("head.html", "r")
fo.write(fi.read())
fi.close()

print >> fo, "<div class=\"page-header\"><h1><small>The Schedule</small></h1></div>"

# seatgeek API reference
# curl 'http://api.seatgeek.com/2/performers?slug=new-york-mets'

# Use an ordered dict rather than a regular dict
# we want the end results to be output in order of level 
# i.e. Majors > AAA > AA etc
teams = (("Majors","toronto-blue-jays"),
		("AAA","buffalo-bisons"),
		("AA","new-hampshire-fisher-cats"),
		("A-Advanced","dunedin-blue-jays"),
		("A","lansing-lugnuts"),
		("Short Season A","vancouver-canadians"))
ordered_teams = collections.OrderedDict(teams)

root_url = "api.seatgeek.com"
today = datetime.date.today().strftime("%d")

for key in ordered_teams:
	# build the quesy and download the json from seatgeek
	query = "/2/events?performers.slug=" + ordered_teams[key]
	conn = httplib.HTTPConnection(root_url)
	conn.request("GET", query)
	response = conn.getresponse()
	data = response.read()
	json_data = json.loads(data)
	# test_empty checks if any of the teams have no data
	test_empty = json_data.get("events")
	if test_empty == []:
		message = "No Games Today"
	else:
		title = json_data["events"][0]["short_title"]
		venue = json_data["events"][0]["venue"]["name"]
		dt = parser.parse(json_data["events"][0]["datetime_local"])
		time = dt.strftime("%I:%M%p")
		day = dt.strftime("%d")
		if day == today:
			message = "%s at %s at %s (Local)" % (title,venue,time)
		else:
			message = "No Games Today"
			
	print >> fo,"<div class=\"panel panel-default\"><div class=\"panel-heading\"><h3 class=\"panel-title\">%s</h3></div>" % key
	print >> fo,"<div class=\"panel-body\">%s</div></div>" % message
	

# get blog posts using feedparser
# list of blogs to pull from:
feeds = ["http://www.battersbox.ca/backend/geeklog.rdf","http://feeds.feedburner.com/DrunkJaysFans","http://www.humandchuck.com/feeds/posts/default"]

# print posts to the html file
print >> fo, "<div class=\"page-header\"><h1><small>The Blogs</small></h1></div>"

for feed in feeds:
	d = feedparser.parse(feed)
	print >>fo, "<br><h4>%s</h4>" % d['feed']['title']
	for i in range(5):
		post = "<h4> <a href=%s>%s</a> </h4>" % (d.entries[i]['link'],d['entries'][i]['title'])
		post2 = post.encode('utf-8','ignore')
		print >> fo, post2

fi = open("foot.html", "r")
fo.write(fi.read())

fi.close()
fo.close()

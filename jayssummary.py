# -*- coding: utf-8 -*-
from dateutil import parser
import httplib
import json
from pprint import pprint
from datetime import datetime
import collections
#curl 'http://api.seatgeek.com/2/performers?slug=new-york-mets'

teams = (("Majors","toronto-blue-jays"),
		("AAA","buffalo-bisons"),
		("AA","new-hampshire-fisher-cats"),
		("A-Advanced","dunedin-blue-jays"),
		("A","lansing-lugnuts"),
		("Short Season A","vancouver-canadians"))

ordered_teams = collections.OrderedDict(teams)

root_url = "api.seatgeek.com"

for key in ordered_teams:
	query = "/2/events?performers.slug=" + ordered_teams[key]
	#print query
	conn = httplib.HTTPConnection(root_url)
	conn.request("GET", query)
	response = conn.getresponse()
	data = response.read()
	#print data
	#print data
	json_data = json.loads(data)
	#pprint(json_data)
	test_empty = json_data.get("events")
	
	if test_empty == []:
		message = "No Games Today"
	else:
		title = json_data["events"][0]["short_title"]
		venue = json_data["events"][0]["venue"]["name"]
		dt = parser.parse(json_data["events"][0]["datetime_local"])
		time = dt.strftime("%I:%M%p")
		message = "%s at %s at %s (Local)" % (title,venue,time)
	print key
	print message



#print json_data["events"][0]["performers"][1]["name"]

from bs4 import BeautifulSoup
from xml.etree import ElementTree
import requests
import time
import datetime
from datetime import date, timedelta
import urllib2
import os
import pprint
import collections
import httplib
import urllib2
import json
import feedparser

# create the html file
# and put in the <head> stuff
fo = open("index.html", "w")
fi = open("head.html", "r")
fo.write(fi.read())
fi.close()


link_count=0

feeds = ["http://www.battersbox.ca/backend/geeklog.rdf",
		"http://feeds.feedburner.com/DrunkJaysFans",
		"http://www.humandchuck.com/feeds/posts/default",
		"http://www.bluebirdbanter.com/rss"]

teams = (("mlb","tormlb"),
		("aaa","bufaaa"),
		("aax","newaax"),
		("afa","dunafa"),
		("afx", "lanafx"),
		("asx","vanasx"))

levels = {
	'mlb' : 'MLB',
	'aaa' : 'Triple A',
	'aax' : 'Double A',
	'afa' : 'Advanced A',
	'afx' : 'A',
	'asx' : 'Short Season A'
}

# date variables for today and yesterday
def get_today():
	year = datetime.date.today().strftime("%Y")
	month = datetime.date.today().strftime("%m")
	month_word = datetime.date.today().strftime("%B")
	day = datetime.date.today().strftime("%d")
	return (year,month,month_word,day)

def get_yesterday():
	yesterday = datetime.date.today() - timedelta(1)
	year = yesterday.strftime("%Y")
	month = yesterday.strftime("%m")
	month_word = yesterday.strftime("%B")
	day = yesterday.strftime("%d")
	return (year,month,month_word,day)

# schedule values
def get_game_values(teamdir):
	linescore = jaysdir + '/linescore.xml'
	file = urllib2.urlopen(linescore)
	data = file.read()
	file.close()
	tree = ElementTree.ElementTree(ElementTree.fromstring(data))
	root = tree.getroot()

	for name, value in root.attrib.items():
		if name == "time_hm_lg":
			gametime = value
		if name == "time_zone":
			timezone = value
		if name == "venue":
			venue = value
		if name == "away_team_city":
			awayteam = value
		if name == "home_team_city":
			hometeam = value

	homefirstname = tree.find('./home_probable_pitcher').attrib['first_name']
	homesurname = tree.find('./home_probable_pitcher').attrib['last_name']
	awayfirstname = tree.find('./away_probable_pitcher').attrib['first_name']
	awaysurname = tree.find('./away_probable_pitcher').attrib['last_name']

	if not awayfirstname:
		awayfirstname = 'TBD'
	if not homefirstname:
		homefirstname = 'TBD'

	return gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname, awayteam, hometeam

#yesterdays scores
def get_game_scores(teamdir):
	linescore = jaysdir + '/boxscore.json'
	print linescore
	opener = urllib2.build_opener()
	try:
		f = opener.open(linescore)
		json_data = json.loads(f.read())
		hometeam = json_data["data"]["boxscore"]['home_fname']
		awayteam = json_data["data"]["boxscore"]['away_fname']
		homeruns = json_data["data"]["boxscore"]['linescore']['home_team_runs']
		awayruns = json_data["data"]["boxscore"]['linescore']['away_team_runs']
		return hometeam,awayteam,homeruns,awayruns
	except:
		hometeam=''
		awayteam=''
		homeruns=0
		awayruns=0
		print "problem with URL %s" % linescore
		return hometeam,awayteam,homeruns,awayruns

# scores
ordered_teams = collections.OrderedDict(teams)
print >> fo, "<div class=\"page-header\"><h1><small>The Scores</small></h1></div>"
for key in ordered_teams:
	year,month,month_word,day = get_yesterday()
	link_count = 0
	message = ''
	print >> fo,"<div class=\"panel panel-default\"><div class=\"panel-heading\"><h3 class=\"panel-title\">%s</h3></div>" % levels[key]
	league = key
	teamabv = ordered_teams[key]
	url = "http://gd2.mlb.com/components/game/" + key + "/year_" + year + "/month_" + month + "/day_" + day
	r  = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data)
	for link in soup.find_all('a'):
		if "gid" in str(link.get('href')) and str(teamabv) in str(link.get('href')):
			jaysuri = str(link.get('href'))
			link_count = link_count + 1
			jaysuri = jaysuri[:-1]
			jaysdir = url + "/" + jaysuri
			(hometeam,awayteam,homeruns,awayruns) = get_game_scores(jaysdir)
			if hometeam:
				message += "%s %s - %s %s" % (hometeam,homeruns,awayteam,awayruns)
	if link_count == 0:
		message = "No Game Yesterday"
	print >> fo,"<h4><div class=\"panel-body\">%s</div></h4></div>" % message

#schedule
print >> fo, "<div class=\"page-header\"><h1><small>The Schedule</small></h1></div>"
for key in ordered_teams:
	year,month,month_word,day = get_today()
	link_count = 0
	message = ''
	print >> fo,"<div class=\"panel panel-default\"><div class=\"panel-heading\"><h3 class=\"panel-title\">%s</h3></div>" % levels[key]
	league = key
	teamabv = ordered_teams[key]
	url = "http://gd2.mlb.com/components/game/" + key + "/year_" + year + "/month_" + month + "/day_" + day
	r  = requests.get(url)
	data = r.text
	soup = BeautifulSoup(data)
	for link in soup.find_all('a'):
		if "gid" in str(link.get('href')) and str(teamabv) in str(link.get('href')):
			jaysuri = str(link.get('href'))
			link_count = link_count + 1
			jaysuri = jaysuri[:-1]
			jaysdir = url + "/" + jaysuri
			(gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname,awayteam,hometeam) = get_game_values(jaysdir)
			message += "%s against %s at %s %s at %s <br>%s %s against %s %s<br>" % (awayteam, hometeam, gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname)
	if link_count == 0:
		message = "No Game Today"
	print >> fo,"<h4><div class=\"panel-body\">%s</div></h4></div>" % message

# get blog posts using feedparser
# list of blogs to pull from:
# print posts to the html file
print >> fo, "<div class=\"page-header\"><h1><small>The Blogs</small></h1></div>"

for feed in feeds:
	d = feedparser.parse(feed)
	print >>fo, "<br><h4>%s</h4>" % d['feed']['title']
	for i in range(5):
		post = "<h4> <a href=%s>%s</a> </h4>" % (d.entries[i]['link'],d['entries'][i]['title'])
		post2 = post.encode('utf-8','ignore')
		print >> fo, post2

#add the footer
fi = open("foot.html", "r")
fo.write(fi.read())

# close files
fi.close()
fo.close()
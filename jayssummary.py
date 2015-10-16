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
import tinys3

# get the S3 keys and bucket name from the environment
aws_access_key = os.environ.get('AWSAccessKeyId')
aws_secret_key = os.environ.get('AWSSecretKey')
aws_jayssummary_bucket = os.environ.get('AWSJaysSummaryBucket')

# set the working directory
homedir='/opt/code/jayssummary'
os.chdir(homedir)

# create the html file
# and put in the <head> stuff
fo = open("index.html", "w")
fi = open("head.html", "r")
fo.write(fi.read())
fi.close()

# initialise the data we'll need
link_count=0

feeds = ["http://www.battersbox.ca/backend/geeklog.rdf",
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
        # extract the boxscore string from the xml url
	boxdate = linescore[-40:-14]
        # build the box url
	box = "http:///mlb.mlb.com/mlb/gameday/index.jsp?gid=" + boxdate
	#print box
        #open the games xml file and extract the variables we need
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

	return gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname, awayteam, hometeam, box

#yesterdays scores
def get_game_scores(teamdir):
	linescore = jaysdir + '/boxscore.json'
        # url is in this format
	# http://mlb.mlb.com/mlb/gameday/index.jsp?gid=2015_07_26_balmlb_tbamlb_1
	boxdate = linescore[-40:-14]
	print boxdate
	box = "http:///mlb.mlb.com/mlb/gameday/index.jsp?gid=" + boxdate
	print box
	print linescore
	opener = urllib2.build_opener()
	try:
		f = opener.open(linescore)
		json_data = json.loads(f.read())
		hometeam = json_data["data"]["boxscore"]['home_fname']
		awayteam = json_data["data"]["boxscore"]['away_fname']
		homeruns = json_data["data"]["boxscore"]['linescore']['home_team_runs']
		awayruns = json_data["data"]["boxscore"]['linescore']['away_team_runs']
		return hometeam,awayteam,homeruns,awayruns,box
	except:
		hometeam=''
		awayteam=''
		homeruns=0
		awayruns=0
		print "problem with URL %s" % linescore
		return hometeam,awayteam,homeruns,awayruns,box

# scores
ordered_teams = collections.OrderedDict(teams)
print >> fo, "<h5 class=\"header\">The Scores</small></h5> <ul class=\"collection with-header\">"

for key in ordered_teams:
	year,month,month_word,day = get_yesterday()
	link_count = 0
	message = ''
	print >> fo,"<li class=\"collection-header\"><b>%s</b></li>" % levels[key]
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
			(hometeam,awayteam,homeruns,awayruns,box) = get_game_scores(jaysdir)
			if hometeam:
				message += "%s %s - %s %s &nbsp;&nbsp;<a href=%s><i class=\"material-icons\">reorder</i></a><br>" % (hometeam,homeruns,awayteam,awayruns,box)
	if link_count == 0:
		message = "No Game Yesterday"
	print >> fo,"<li class=\"collection-item\">%s</li>" % message

print >> fo, "</ul>"

#schedule
print >> fo, "<h5 class=\"header\">The Schedule</small></h5> <ul class=\"collection with-header\">"
for key in ordered_teams:
	year,month,month_word,day = get_today()
	link_count = 0
	message = ''
	print >> fo,"<li class=\"collection-header\"><b>%s</b></li>" % levels[key]
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
                        print jaysdir
			(gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname,awayteam,hometeam,box) = get_game_values(jaysdir)
			message += "%s at %s at %s %s at %s &nbsp;&nbsp;<a href=%s><i class=\"material-icons\">info_outline</i></a><br>%s %s against %s %s<br>" % (awayteam, hometeam, gametime, timezone, venue, box, awayfirstname, awaysurname,homefirstname, homesurname)
	if link_count == 0:
		message = "No Game Today"
	print >> fo,"<li class=\"collection-item\">%s</li>" % message

print >> fo, "</ul>"

# get blog posts using feedparser
# list of blogs to pull from:
# print posts to the html file
print >> fo, "<div class=\"page-header\"><h5>The Blogs</h5></div>"
print >> fo, "<ul class=\"collapsible\" data-collapsible=\"accordion\">"

for feed in feeds:
        print feed
	d = feedparser.parse(feed)
	print >>fo, "<li><div class=\"collapsible-header\"><h6>%s</h6></div>" % d['feed']['title']
        print >>fo, "<div class=\"collapsible-body\">"
	for i in range(5):
		post = "<h6> <a href=%s>%s</a> </h6>" % (d.entries[i]['link'],d['entries'][i]['title'])
		post2 = post.encode('utf-8','ignore')
		print >> fo, post2
        print >> fo, "</div></li>"
print >> fo, "</ul>"

#add the footer
fi = open("foot.html", "r")
fo.write(fi.read())

# close files
fi.close()
fo.close()

# copy to AWs S3 bucket
print aws_access_key
print aws_secret_key
print aws_jayssummary_bucket
conn = tinys3.Connection(aws_access_key,aws_secret_key,tls=True,endpoint='s3-us-west-2.amazonaws.com')

findex = open('/opt/code/jayssummary/index.html','rb')
conn.upload('index.html',findex,'jayssummary.com')
findex.close()

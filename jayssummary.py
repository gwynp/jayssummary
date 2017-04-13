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
import yaml
import jinja2

# get the S3 keys and bucket name from the environment
aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
aws_jayssummary_bucket = 'jaysummary.com'

# set the working directory
titledate='{dt:%A} {dt:%B} {dt.day}, {dt.year}'.format(dt=datetime.datetime.now())
homedir='/opt/code/jayssummary'
os.chdir(homedir)
link_count=0

feeds = ["http://www.battersbox.ca/backend/geeklog.rdf",
		"http://www.humandchuck.com/?format=rss",
		"http://www.torontosun.com/g00/2_d3d3LnRvcm9udG9zdW4uY29t_/TU9SRVBIRVVTMTAkaHR0cDovL3d3dy50b3JvbnRvc3VuLmNvbS9zcG9ydHMvYmx1ZWpheXMvcnNzLnhtbA%3D%3D_$/$/$/$",
		"https://feeds.thescore.com/baseball/teams/4.rss",
		"https://bunttothegap.com/feed/podcast/",
		"http://www.jaysinthehouse.com/feeds/posts/default",
		"http://www.bluebirdbanter.com/rss"]

#feeds = ["http://www.bluebirdbanter.com/rss"]

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
	try:
		homefirstname = tree.find('./home_probable_pitcher').attrib['first_name']
		homesurname = tree.find('./home_probable_pitcher').attrib['last_name']
		awayfirstname = tree.find('./away_probable_pitcher').attrib['first_name']
		awaysurname = tree.find('./away_probable_pitcher').attrib['last_name']
	except:
		awayfirstname = 'TBD'
		awaysurname=''
		homefirstname = 'TBD'
		homesurname=''

	print "done for %s %s" % (hometeam, awayteam)
	return gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname, awayteam, hometeam, box

#yesterdays scores
def get_game_scores(teamdir):
	linescore = jaysdir + '/boxscore.json'
        # url is in this format
	# http://mlb.mlb.com/mlb/gameday/index.jsp?gid=2015_07_26_balmlb_tbamlb_1
	boxdate = linescore[-40:-14]
	#print "boxdate = " + boxdate
	box = "http:///mlb.mlb.com/mlb/gameday/index.jsp?gid=" + boxdate
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
#scores={}
scores=[]
link_count = 0
for key in ordered_teams:
	year,month,month_word,day = get_yesterday()
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
			#print "hometeam" + hometeam
			if hometeam:
				#print "in here"
				level=levels[key]
				scores.append([level,hometeam,awayteam,homeruns,awayruns,box])
			

#games
game_count = 0
games=[]
for key in ordered_teams:
	year,month,month_word,day = get_today()
	message = ''
	#print >> fo,"<li class=\"collection-header\"><b>%s</b></li>" % levels[key]
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
			#print "jaysdir = " + jaysdir
			game_count = game_count + 1
			level=levels[key]
			(gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname,awayteam,hometeam,box) = get_game_values(jaysdir)
			games.append([level,gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname,awayteam,hometeam,box])

			
# get blog posts using feedparser
allposts={}
for feed in feeds:
	posts={}
	d = feedparser.parse(feed)
	for i in range(5):
		#postlink,posttitle = (d.entries[i]['link'],d['entries'][i]['title'])
		feedname = d['feed']['title']
		postlink = d.entries[i]['link']
		posttitle = d['entries'][i]['title']
		posts[posttitle]=postlink
	allposts[feedname]=posts

env = jinja2.Environment(loader=jinja2.FileSystemLoader(["./"])) 
template = env.get_template( "template.html") 
result = template.render( titledate=titledate, scores=scores, games=games, posts=allposts)
print result.encode('utf-8')
with open("index.html", "wb") as fh:
    fh.write(result.encode('utf-8'))
fh.close()

# copy to AWs S3 bucket
print aws_access_key
print aws_secret_key
print aws_jayssummary_bucket
conn = tinys3.Connection(aws_access_key,aws_secret_key,tls=True,endpoint='s3-us-west-2.amazonaws.com')

findex = open('/opt/code/jayssummary/index.html','rb')
conn.upload('index.html',findex,'jayssummary.com')
findex.close()
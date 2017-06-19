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
homedir=dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(homedir)
link_count=0

feeds = {
		'Battersbox': 'http://www.battersbox.ca/backend/geeklog.rdf',
		'Hum and Chuck': 'http://www.humandchuck.com/wwwhumandchuckcom?format=rss',
		'Toronto Sun': 'http://www.torontosun.com/g00/2_d3d3LnRvcm9udG9zdW4uY29t_/TU9SRVBIRVVTMTAkaHR0cDovL3d3dy50b3JvbnRvc3VuLmNvbS9zcG9ydHMvYmx1ZWpheXMvcnNzLnhtbA%3D%3D_$/$/$/$',
		'The Score': 'https://feeds.thescore.com/baseball/teams/4.rss',
		'Bunt to the Gap': 'https://bunttothegap.com/feed/podcast/',
		'Jays in the House': 'http://www.jaysinthehouse.com/feeds/posts/default',
		'Bluebird Banter': 'http://www.bluebirdbanter.com/rss'
}
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

boxteams = {
		"tor" : "blue-jays",
		"tba" : "rays",
		"atl" : "braves",
		"bal" : "orioles",
		"bos" : "red-sox",
		"chn" : "cubs",
		"cha" : "white-sox",
		"cin" : "reds",
		"cle" : "indians",
		"col" : "rockies",
		"det" : "tigers",
		"hou" : "astros",
		"kca" : "royals",
		"lan" : "dodgers",
		"mia" : "marlins",
		"mil" : "brewers",
		"min" : "twins",
		"nya" : "yankees",
		"nym" : "mets",
		"oak" : "a's",
		"phi" : "phillies",
		"pit" : "pirates",
		"sdn" : "padres",
		"sea" : "mariners",
		"sfn" : "giants",
		"sln" : "cardinals",
		"tex" : "rangers",
		"was" : "nationals",
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
	yyyymmdd = yesterday.strftime("%Y%m%d")
	return (year,month,month_word,day,yyyymmdd)

# schedule values
def get_game_values(teamdir):
	linescore = jaysdir + '/linescore.xml'
	print linescore
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
	return gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname, awayteam, hometeam

#yesterdays scores
def get_game_scores(teamdir,league):
	linescore = jaysdir + '/boxscore.json'
	opener = urllib2.build_opener()
	try:
		print "linescore is" + linescore
		f = opener.open(linescore)
		json_data = json.loads(f.read())
		hometeam = json_data["data"]["boxscore"]['home_fname']
		awayteam = json_data["data"]["boxscore"]['away_fname']
		homeruns = json_data["data"]["boxscore"]['linescore']['home_team_runs']
		awayruns = json_data["data"]["boxscore"]['linescore']['away_team_runs']
		game_pk = json_data["data"]['boxscore']["game_pk"]
		home_team_code = json_data["data"]['boxscore']["home_team_code"]
		away_team_code = json_data["data"]["boxscore"]['away_team_code']

		#pitcher = json_data["data"]["boxscore"]['pitching']
		#print pitcher
	except:
		hometeam=''
		awayteam=''
		homeruns=0
		awayruns=0
		game_pk=0
		home_team_code=0
		print "problem with URL %s" % linescore

	# make the boxscore url
	if league == 'mlb':
		box_start='https://www.mlb.com/gameday/'
		box_end='#game_state=final,lock_state=final,game_tab=box,game='
		box_uri = boxteams[away_team_code] + "-vs-" + boxteams[home_team_code] +"/"
		box = box_start+box_uri+ game_pk+box_end+game_pk
	else:
		box = "http://www.milb.com/scoreboard/index.jsp?cid=&lid=&org=141&sc=&sid=milb&t=affiliate&ymd=%s" % yyyymmdd
	return hometeam,awayteam,homeruns,awayruns,box

# scores
ordered_teams = collections.OrderedDict(teams)
#scores={}
scores=[]
link_count = 0
for key in ordered_teams:
	year,month,month_word,day,yyyymmdd = get_yesterday()
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
			(hometeam,awayteam,homeruns,awayruns,box) = get_game_scores(jaysdir,league)
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
			(gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname,awayteam,hometeam) = get_game_values(jaysdir)
			games.append([level,gametime, timezone, venue, homefirstname, homesurname, awayfirstname, awaysurname,awayteam,hometeam])


# get blog posts using feedparser
# feed names and urls are in feeds dict
# loop through this and pass the urls to feedparser
# and get the most recent 5 posts
# and everything to allposts dict
allposts={}
for feedname, feedurl in feeds.iteritems():
	posts=collections.OrderedDict()
	d = feedparser.parse(feedurl)
	for i in range(5):
		postlink = d.entries[i]['link']
		posttitle = d['entries'][i]['title']
		posts[posttitle]=postlink
		#print i
		#print posttitle
	allposts[feedname]=posts
	#print posts

# use jinja2 and the template.html to produce the index.html file
env = jinja2.Environment(loader=jinja2.FileSystemLoader(["./"]))
template = env.get_template( "template.html")
result = template.render( titledate=titledate, scores=scores, games=games, posts=allposts)
with open("index.html", "wb") as fh:
    fh.write(result.encode('utf-8'))
fh.close()

# copy to AWs S3 bucket
print aws_access_key
print aws_secret_key
print aws_jayssummary_bucket
conn = tinys3.Connection(aws_access_key,aws_secret_key,tls=True,endpoint='s3-us-west-2.amazonaws.com')
current_dir = os.getcwd()
index_file = current_dir + '/index.html'
findex = open(index_file,'rb')
conn.upload('index.html',findex,'jayssummary.com')
findex.close()

import urllib, urllib2, cookielib, sys, re
import simplejson as json
from pymongo import Connection

g_username = 'username'
g_password = 'password'

def getApps(username, password):
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  login_data = urllib.urlencode({'userid' : username, 'pwd' : password})
  opener.open('https://jobmine.ccol.uwaterloo.ca/psp/SS/?cmd=login', login_data)
  resp = opener.open('https://jobmine.ccol.uwaterloo.ca/psp/SS/EMPLOYEE/WORK/c/UW_CO_STUDENTS.UW_CO_APP_SUMMARY.GBL?pslnkid=UW_CO_APP_SUMMARY_LINK&FolderPath=PORTAL_ROOT_OBJECT.UW_CO_APP_SUMMARY_LINK&IsFolder=false&IgnoreParamTempl=FolderPath%2cIsFolder')
  iframe = re.search(r'iframe.*">', resp.read()).group()
  source = re.search(r'src=".*"', iframe)
  source = source.group()[5:-1]
  #1print 'opening ' + source
  resp = opener.open(source)
  return resp.read()

def parseHTML(html):
  intr = False
  apps = []
  app = ''
  #for line in open("response"):
  for line in html:
   if "trUW_CO_APPS_VW2" in line:
    intr = True
   elif intr and '</tr>' in line:
    intr = False
    appsplit = app.split('><')
    app = '{'
    for s in appsplit: #this is gross, fix this later
      if 'a name=\'UW_CO_JB_TITLE2' in s:
        app += '"job_title":"' + re.search(r'>.*</a$', s).group()[1:-3] + '",'
      elif 'id=\'UW_CO_JOBINFOVW_UW_CO_PARENT_NAME' in s:
        app += '"company":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_TERMCALND_UW_CO_DESCR_30' in s:
        app += '"term":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_JOBSTATVW_UW_CO_JOB_STATUS' in s:
        app += '"job_status":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_APPSTATVW_UW_CO_APPL_STATUS' in s:
        app += '"app_status":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_JOBINFOVW_UW_CO_CHAR_DATE' in s:
        app += '"app_date":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_JOBAPP_CT_UW_CO_MAX_RESUME' in s:
        app += '"num_resumes":"' + re.search(r'>.*</span$', s).group()[1:-6] + '"}'

    apps.append(app)
    app = ''
    #break
   elif intr:
    app += line.rstrip('\n')
  return apps

apps = parseHTML(open("response"))
#apps = parseHTML(g_username, g_password)
db = Connection('localhost', 27017).jobmine
collection = db.applications
for app in apps:
  collection.insert(json.loads(app))

#print getApps(g_username, g_password)

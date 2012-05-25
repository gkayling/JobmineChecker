import urllib, urllib2, cookielib, sys, re
import base64
import simplejson as json
from pymongo import Connection
import hashlib
import smtplib
from email.mime.text import MIMEText

def sendEmail(emailAddr, message):
  fromAddr = 'no-reply@jobminechecker.aws'
  email = MIMEText(message)
  email['Subject'] = 'Jobmine Digest'
  email['From'] = fromAddr
  email['To'] = emailAddr
  s = smtplib.SMTP('localhost')
  s.sendmail(fromAddr, [emailAddr], email.as_string())
  s.quit()

def getApps(username, password):
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  login_data = urllib.urlencode({'userid' : username, 'pwd' : password})
  opener.open('https://jobmine.ccol.uwaterloo.ca/psp/SS/?cmd=login', login_data)
  resp = opener.open('https://jobmine.ccol.uwaterloo.ca/psp/SS/EMPLOYEE/WORK/c/UW_CO_STUDENTS.UW_CO_APP_SUMMARY.GBL?pslnkid=UW_CO_APP_SUMMARY_LINK&FolderPath=PORTAL_ROOT_OBJECT.UW_CO_APP_SUMMARY_LINK&IsFolder=false&IgnoreParamTempl=FolderPath%2cIsFolder')
  iframe = re.search(r'iframe.*">', resp.read()).group()
  source = re.search(r'src=".*"', iframe)
  source = source.group()[5:-1]
  resp = opener.open(source)
  return resp.read()

def parseHTML(html, username):
  intr = False
  apps = []
  app = ''
  for line in html:
   prehash = ''
   if "trUW_CO_APPS_VW2" in line:
    intr = True
   elif intr and '</tr>' in line:
    intr = False
    appsplit = app.split('><')
    app = ''
    for s in appsplit: #this is gross, fix this later
      if 'a name=\'UW_CO_JB_TITLE2' in s:
        field = re.search(r'>.*</a$', s).group()[1:-3]
        app += '"job_title":"' + field + '",'
        prehash += field
      elif 'id=\'UW_CO_JOBINFOVW_UW_CO_PARENT_NAME' in s:
        field = re.search(r'>.*</span$', s).group()[1:-6]
        app += '"company":"' + field + '",'
        prehash += field
      elif 'id=\'UW_CO_TERMCALND_UW_CO_DESCR_30' in s:
        field = re.search(r'>.*</span$', s).group()[1:-6]
        app += '"term":"' + field + '",'
        prehash += field
      elif 'id=\'UW_CO_JOBSTATVW_UW_CO_JOB_STATUS' in s:
        app += '"job_status":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_APPSTATVW_UW_CO_APPL_STATUS' in s:
        app += '"app_status":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_JOBINFOVW_UW_CO_CHAR_DATE' in s:
        app += '"app_date":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'
      elif 'id=\'UW_CO_JOBAPP_CT_UW_CO_MAX_RESUME' in s:
        app += '"num_resumes":"' + re.search(r'>.*</span$', s).group()[1:-6] + '",'

    app += '"hash":"' + hash(prehash + username) + '"'
    apps.append(app)
    app = ''
    #break
   elif intr:
    app += line.rstrip('\n')
  return apps

def hash(string):
  sha1 = hashlib.sha1()
  sha1.update(string)
  return sha1.hexdigest()

fields = ['job_status', 'app_status', 'app_date']

db = Connection('localhost', 27017).jobmine
users = db.users
for user in list(users.find({'active':1})):
#for user in list(users.find({'test':1})):
  #apps = parseHTML(open("response"), user['user'])
  #apps = parseHTML(open('response_orig'), g_username)
  apps = parseHTML(getApps(user['user'], base64.b64decode(user['password'])).split('\n'), user['user'])
  #print apps
  collection = db.applications
  message = ''
  for app in apps:
    appjson = json.loads('{"user":"' + user['user'] + '",' + app + '}')
    app = collection.find_one(json.loads('{"hash":"'+appjson['hash'] +'"}'))
    if app == None:
      collection.insert(appjson)
      message += 'New ' + appjson['job_title'] + ' at ' + appjson['company'] + '\n'
    elif app['app_status'] != 'Not Selected':
      changes = '';
      change = False
      for f in fields:
        if app[f] != appjson[f]:
          changes += '\n\t' + f + ": " + app[f] + ' -> ' + appjson[f]
          change = True
          app[f] = appjson[f]
      if change:
        message += '\nModified ' + appjson['job_title'] + ' at ' + appjson['company'] + ': ' + changes + '\n'
        collection.update({ '_id' : app['_id'] }, app, True) 
  #doesn't send an email  
  if message != '':
    sendEmail(user['email'], message)
    #message = 'No changes'
  #print message


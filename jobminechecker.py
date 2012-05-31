import urllib, urllib2, cookielib, sys, re, base64, hashlib, smtplib
import simplejson as json
from pymongo import Connection
from email.mime.text import MIMEText

def sendEmail(emailAddr, message):
  fromAddr = 'no-reply@jobminechecker.aws'
  email = MIMEText(message)
  email['Subject'] = 'Jobmine Digest'
  email['From'] = fromAddr
  email['To'] = emailAddr
  #print email.as_string()
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

def extractField(f, string):
  if f == 'a name=\'UW_CO_JB_TITLE2':
    return re.search(r'>.*</a$', string).group()[1:-3]
  else:
    return re.search(r'>.*</span$', string).group()[1:-6]

def parseHTML(html, username):
  intr = False
  apps = []
  app = ''
  fields = {'a name=\'UW_CO_JB_TITLE2':'job_title', 'id=\'UW_CO_JOBINFOVW_UW_CO_PARENT_NAME':'company', 'id=\'UW_CO_TERMCALND_UW_CO_DESCR_30':'term', 'id=\'UW_CO_JOBSTATVW_UW_CO_JOB_STATUS':'job_status', 'id=\'UW_CO_APPSTATVW_UW_CO_APPL_STATUS':'app_status', 'id=\'UW_CO_JOBINFOVW_UW_CO_CHAR_DATE':'app_date', 'id=\'UW_CO_JOBAPP_CT_UW_CO_MAX_RESUME':'num_resumes'}
  hashfields = ['job_title', 'company', 'term']
  appjson = {}
  prehash = ''
  for line in html:
   if "trUW_CO_APPS_VW2" in line:
    intr = True
   elif intr and '</tr>' in line:
    intr = False
    appsplit = app.split('><')
    app = ''
    for s in appsplit:
      for f in fields:
        if f in s:
          value = extractField(f, s)
          if fields[f] in hashfields:
            prehash += value
          appjson[fields[f]] = value
    appjson['hash'] = hash(prehash + username)
    apps.append(appjson)
    app = ''
    appjson = {}
    #break
   elif intr:
    app += line.rstrip('\n')
  #print str(apps)
  return apps

def hash(string):
  sha1 = hashlib.sha1()
  sha1.update(string)
  return sha1.hexdigest()

fields = ['job_status', 'app_status', 'app_date']

db = Connection('localhost', 27017).jobmine#test
users = db.users
for user in list(users.find({'active':1})):
  #apps = parseHTML(open("response"), user['user'])
  #apps = parseHTML(open('response_orig'), user['user'])
  #apps = parseHTML(open("response3"), user['user'])
  apps = parseHTML(getApps(user['user'], base64.b64decode(user['password'])).split('\n'), user['user'])
  #print apps
  collection = db.applications
  message = ''
  #print str(apps)
  for app in apps:
    appjson = app
    appjson['user'] = user['user']
    app = collection.find_one({'hash':appjson['hash']})
    if app == None:
      collection.insert(appjson)
      message += '\nNew ' + appjson['job_title'] + ' at ' + appjson['company'] + '\n'
    elif 'app_status' in app and (app['app_status'] != 'Not Selected' or app['app_status'] != 'Ranking Completed'):
      changes = '';
      change = False
      for f in fields:
        if f not in appjson:
          changes += '\n\t' + f + ": " + app[f] + ' -> ' + 'N/A'
          change = True  
          del app[f]
        elif app[f] != appjson[f]:
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


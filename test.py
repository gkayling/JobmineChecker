import sys, re, pymongo

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
    break
   elif intr:
    app += line.rstrip('\n')
  return apps 

apps = parseHTML(open("response"))
connection = Connection('localhost', 27017)
db = connection['jobmine']
collection = db['applications']
for app in apps:
  collection.insert(app)


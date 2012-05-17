import urllib, urllib2, cookielib, re

username = 'username'
password = 'password'

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
login_data = urllib.urlencode({'userid' : username, 'pwd' : password})
opener.open('https://jobmine.ccol.uwaterloo.ca/psp/SS/?cmd=login', login_data)
resp = opener.open('https://jobmine.ccol.uwaterloo.ca/psp/SS/EMPLOYEE/WORK/c/UW_CO_STUDENTS.UW_CO_APP_SUMMARY.GBL?pslnkid=UW_CO_APP_SUMMARY_LINK&FolderPath=PORTAL_ROOT_OBJECT.UW_CO_APP_SUMMARY_LINK&IsFolder=false&IgnoreParamTempl=FolderPath%2cIsFolder')
iframe = re.search(r'iframe.*">', resp.read()).group()
source = re.search(r'src=".*"', iframe)
source = source.group()[5:-1]
print 'opening ' + source
resp = opener.open(source)
print resp.read()

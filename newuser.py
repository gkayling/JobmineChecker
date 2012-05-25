#! /usr/bin/env python

import getpass, base64, pymongo

username = raw_input("Enter your Jobmine username: ") 
password = base64.b64encode(getpass.getpass())
email = raw_input("Enter your preferred email address: ")

db = pymongo.Connection('localhost', 27017).jobmine
users = db.users
user = users.find_one({'user':username})
if user == None:
  users.insert({'user':username, 'password':password, 'email':email, 'active':1})
  print username + ' inserted into the database'
else:
  print username + ' already exists in the database!'

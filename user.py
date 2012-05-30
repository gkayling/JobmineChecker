import sys, pymongo, getpass, base64

def newUser():
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
  sys.exit()

if len(sys.argv) < 3:
  if len(sys.argv) == 2 and sys.argv[1] == '-n':
    newUser()
  print 'Expecting two arguments'
  sys.exit()

action = sys.argv[1]
actions = {'-e':1, '-d':0}
if action not in actions:
  print 'Illegal parameter'
  sys.exit()

username = sys.argv[2]

if action == '-n':
  newUser(username)

db = pymongo.Connection('localhost', 27017).jobmine
users = db.users
user = users.find_one({'user':username})

if user != None:
  user['active'] = actions[action]
  users.update({'user':username}, user, True)
  print username + ' enabled: ' + str(actions[action])


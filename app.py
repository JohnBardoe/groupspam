from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import pymongo
import csv
import pprint
import json
import multiprocessing
import bot
from time import sleep
from random import shuffle


app = Flask(__name__)
client = pymongo.MongoClient('mongodb://mongo:27017/', username='root', password='root')
db = client["groupspam"]
run_flag = multiprocessing.Value('i', True)

# name: string
# user_list: string
# added: integer
# failed: integer
def readLog():
    log = []
    with open('botlog.out', 'r') as f:
        log = f.read().split('\n')
    with open('botlog.err', 'r') as f:
        log += f.read().split('\n')
    return log

def checkUserLists(added):
    userlists = db.userlists.find()
    for userlist in userlists:
        for user in userlist['userlist']:
            if user in added:
                userlist['userlist'].remove(user)
        db.userlists.replace_one({'name': userlist['name']}, userlist)
    return False

@app.route('/upload_userlist', methods=['POST'])
def upload_userlist():
    userlist = []
    file = request.files['file']
    if file:
        string = file.read().decode('utf-8')
        lines = string.split('\n')
        lines = [line.replace('\r', '') for line in lines]
        db.userlists.insert_one({'name': secure_filename(file.filename), 'userlist': lines})
        return redirect(url_for('index')) 
    return 'error uploading userlist' 

@app.route('/get_groups', methods=['GET'])
def get_groups():
    groups = []
    for group in db.groups.find():
        groups.append(group)
    return json.dumps(groups)

@app.route('/delete_group', methods=['POST'])
def delete_group():
    group = request.form['group']
    db.groups.delete_one({'name': group})
    return redirect(url_for('index'))

@app.route('/add_group', methods=['POST'])
def add_group():
    group = request.form['groupname']
    db.groups.insert_one({'name': group, 'userlist': ""})
    return redirect(url_for('index'))

@app.route('/update_group', methods=['POST'])
def update_group():
    group_name = request.form['oldname']
    new_name = request.form['groupname']
    userlist = request.form['userlist']
    group = db.groups.find_one({'name': group_name})
    group['name'] = new_name
    group['userlist'] = userlist
    db.groups.replace_one({'name': group_name}, group)
    return redirect(url_for('index'))

@app.route('/set_settings', methods=['POST'])
def set_settings():
    proxy_url = request.form['proxyurl']
    maxreq = request.form['maxreq']
    maxadd = request.form['maxadd']
    db.settings.update_one({}, {'$set': {'proxy_url': proxy_url, 'maxreq': maxreq, 'maxadd': maxadd}}, upsert=True) 

    return redirect(url_for('index'))

@app.route('/start', methods=['POST'])
def start():
    global run_flag
    group_names = db.groups.distinct('name')
    tasks = []
    for group in group_names:
        userlist_name = db.groups.find_one({'name': group})['userlist']
        userlist =  db.userlists.find_one({'name': userlist_name})['userlist']
        for user in userlist:
            tasks.append([user, group])
    
    checkUserLists(db.added.distinct('user'))
    shuffle(tasks)

    proxy = {}
    settings_db = db.settings.find_one()
    proxy_url = settings_db['proxy_url']
    if proxy_url != "":
        proxy_url = proxy_url.split('@')
        proxy['addr'] = proxy_url[0].split(':')[0]
        proxy['port'] = proxy_url[0].split(':')[1]
        proxy['username'] = proxy_url[1].split(':')[0]
        proxy['password'] = proxy_url[1].split(':')[1]
        proxy['proxy_type'] = 'http'
    run_flag.value = False
    sleep(5)
    run_flag.value = True
    #clear progess data
    settings = {"maxadd": int(settings_db['maxadd']), "maxreq": int(settings_db['maxreq']), "proxy": proxy}
    p = multiprocessing.Process(target=bot.entry, args=(run_flag, tasks, group_names, settings))
    p.start()
    return redirect(url_for('index'))

@app.route('/log', methods=['GET'])
def log():
    log = []
    log_string = ""
    try:
        log = readLog()
        for i in range(len(log)):
            log_string += log[i] + '<br>'
    except:
        return "Waiting for you to start me..."

    return log_string 

@app.route('/progress', methods=['GET'])
def progress():
    progress = {}
    log = readLog()
    for group in db.groups.find():
        progress[group['name']] = {"added": 0, "failed": 0}
    for line in log:
        if 'Successfully added' in line:
            group = line.split(' ')[4]
            user = line.split(' ')[2]
            db.added.insert_one({'user': user})
            progress[group]['added'] += 1
        elif 'Failed to add' in line:
            group = line.split(' ')[5]
            progress[group]['failed'] += 1
    return json.dumps(progress)

@app.route('/')
def index():
    groups = db.groups.find()
    userlists = db.userlists.find()
    settings = db.settings.find_one()
    userlist_names = []
    groups_input = []
    for userlist in userlists:
        userlist_names.append(userlist['name'])
    for group in groups:
        groups_input.append({'name' : group['name'], 'userlist': group['userlist'], 'userlist_names': userlist_names})
    return render_template('index.html', groups=groups_input, settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, render_template, request, redirect, url_for
import pymongo
import csv
import pprint
import json
import multiprocessing
import bot


app = Flask(__name__)
client = pymongo.MongoClient('mongodb://mongo:27017/', username='root', password='root')
db = client["groupspam"]
run_flag = multiprocessing.Value('i', True)

### Groups ###
# name: string
# user_list: string
# added: integer
# failed: integer

@app.route('/upload_userlist', methods=['POST'])
def upload_userlist():
    userlist = []
    file = request.files['file']
    if file:
        string = file.read().decode('utf-8')
        lines = string.split('\n')
        lines = [line.replace('\r', '') for line in lines]
        db.userlists.insert_one({'name': file.name, 'userlist': lines})
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
    db.groups.insert_one({'name': group, 'userlist': "", 'added': 0, 'failed': 0})
    return redirect(url_for('index'))

@app.route('/set_settings', methods=['POST'])
def set_settings():
    proxy_url = request.form['proxyurl']
    db.settings.update_one({}, {'$set': {'proxy_url': proxy_url}}, upsert=True)
    maxreq = request.form['maxreq']
    db.settings.update_one({}, {'$set': {'maxreq': maxreq}}, upsert=True)
    maxadd = request.form['maxadd']
    db.settings.update_one({}, {'$set': {'maxadd': maxadd}}, upsert=True)

    return redirect(url_for('index'))

@app.route('/start', methods=['POST'])
def start():
    global run_flag
    db.groups.update_many({}, {'$set': {'added': 0, 'failed': 0}})
    group_names = db.groups.distinct('name')
    tasks = []
    for group in group_names:
        userlist = db.groups.find_one({'name': group})['userlist']
        for user in userlist:
            tasks.append([user, group])

    proxy = {}
    proxy_url = db.settings.find_one({'proxy_url': {'$exists': True}})['proxy_url']
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
    p = multiprocessing.Process(target=bot.entry, args=(run_flag, tasks, group_names, proxy))
    p.start()
    return redirect(url_for('index'))

@app.route('/log', methods=['GET'])
def log():
    log = []
    with open('botlog.out', 'r') as f:
        log = f.read().split('\n')
    return json.dumps(log)

@app.route('/')
def index():
    groups = db.groups.find()
    userlists = db.userlists.find()
    settings = db.settings.find()
    return render_template('index.html', groups=groups, userlists=userlists, settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

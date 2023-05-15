from flask import Flask, render_template, request, redirect, url_for
import pymongo
import csv
import pprint
import json

app = Flask(__name__)
client = pymongo.MongoClient('mongodb://mongo:27017/', username='root', password='root')
db = client["groupspam"]

@app.route('/upload_userlist', methods=['POST'])
def upload_userlist():
    userlist = []
    file = request.files['file']
    if file:
        string = file.read().decode('utf-8')
        lines = string.split('\n')
        lines = [line.replace('\r', '') for line in lines]
        db.insert_one({ 'name' : file.name, 'users': lines})
        return 200, file.name
    return 500, 'Error uploading file'

@app.route('/get_groups', methods=['GET'])
def get_groups():
    groups = []
    for group in db.groups.find():
        groups.append(group)
    return json.dumps(groups)

@app.route('/edit_group', methods=['POST'])
def edit_group():



@app.route('/')
def index():
    groups = db.groups.find()
	return render_template('index.html', groups=groups)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)

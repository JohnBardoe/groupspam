from flask import Flask, render_template, request, redirect, url_for
import pymongo
import csv
import pprint

app = Flask(__name__)
db = pymongo.MongoClient('mongodb://mongo:27017/', username='root', password='root')


@app.route('/upload_userlist')
def upload_userlist():
    #form with file upload
    #get file, parse it and upload to mongo
    userlist = []
    file = request.files['file']
    if file:
        return pprint.pformat(file)


@app.route('/')
def index():
	return render_template('index.html', groups=['Group 1', 'Group 2', 'Group 3', 'Group 4'])

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)

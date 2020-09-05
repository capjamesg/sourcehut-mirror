#!flask/bin/python

import os
import requests
import hmac, hashlib
import logging
import subprocess
from dotenv import load_dotenv 
from flask import Flask, jsonify, request, abort

load_dotenv()

logging.basicConfig(filename="app.log", level=logging.DEBUG)

app = Flask(__name__)

@app.route('/', methods=["POST"])
def index():
	auth = request.headers.get("X-Hub-Signature")
	token = os.environ.get("secret_token")

	key = bytes(token, 'utf-8')
	verify = hmac.new(key=key, msg=request.data, digestmod=hashlib.sha1).hexdigest()

	if hmac.compare_digest(verify, auth.split('=')[1]):
		response = request.json

		repo_name = response["repository"]["full_name"]
		short_name = response["repository"]["name"]

		os.chdir("/Users/James/Repos/")

		if not os.path.exists("/Users/James/Repos/{}".format(short_name)):
			os.system("git clone https://github.com/{}".format(repo_name))

		os.chdir("/Users/James/Repos/{}".format(short_name))
		os.system("git pull")

		validate_repo_on_sourcehut = requests.get("https://git.sr.ht/api/repos/{}".format(short_name))

		if response["repository"]["private"] == True:
			visibility = "private"
		else:
			visibility = "public"

		if validate_repo_on_sourcehut.status_code != 200:
			body = {
				"name": short_name,
				"description": response["repository"]["description"],
				"visibility": visibility
			}

			create_repo = requests.post("https://git.sr.ht/api/repo", data=body)

		os.system("git remote add sourcehut git@git.sr.ht:~jamesg_oca/{}".format(short_name))
		os.system("git push sourcehut master")

		message = { "message": "Mirrored successfully." }

		return jsonify(message)
	else:
		abort(403)

@app.errorhandler(403)
def no_permissions(error):
	message = { "message": "You do not have permission to access this resource."}

	return jsonify(message)

@app.errorhandler(404)
def not_found_error(error):
	message = { "message": "This resource was not found."}

	return jsonify(message)

if __name__ == '__main__':
	app.run(debug=True)

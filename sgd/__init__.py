import os
import json
from flask import Flask
from sgd.gdrive import GoogleDrive

app = Flask(__name__)
token = json.loads(os.environ.get("TOKEN"))
gdrive = GoogleDrive(token)

from sgd import routes

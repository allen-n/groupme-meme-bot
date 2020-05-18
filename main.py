from flask import Flask, request
from memebot import Memebot

# Groupy imports
from groupy.client import Client
from groupy.api.groups import Group
from groupy.api.bots import Bot
from groupy.api.messages import Message
from groupy import attachments
import groupy.exceptions

# Fuzzy matching
from fuzzywuzzy import process
import re

# other imports
import os
import logging
import sys
import json
import time
import requests

# Env setup
is_debug = True
logging_level = logging.DEBUG
api_token = None
memebot_token = None
testbot_token = None

if(os.path.exists("./apitoken.json")):  # Only true locally
    with open('./apitoken.json') as f:
        tokens = json.load(f)
        api_token = tokens["api_token"]
        memebot_token = tokens["memebot_token"]
        testbot_token = tokens["testbot_token"]
else:
    # For deployment on Heroku
    api_token = os.environ.get("API_TOKEN")
    memebot_token = os.environ.get("MEMEBOT_TOKEN")
    is_debug = False
    logging_level = logging.INFO

# Constants
GROUP_ID = "59823729"  # Testgroup
GROUP_IDS = {"TESTGROUP": "59823729", "STEAK_PHILLY": "14970560"}

logging.basicConfig(stream=sys.stderr, level=logging_level)
client = Client.from_token(api_token)
memebot = Memebot(GROUP_ID, client, memebot_token, api_token)
app = Flask(__name__)





@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    data_str = "Message Text={}, Sender ID={}, Sender Name={}".format(
        data['text'], data['sender_id'], data['name'])
    logging.info(data_str)
    if data["sender_type"] != "bot":  # Bots cannot reply to bots
        memebot.handle_bot_response(data['text'])

    return "ok", 200

if __name__ == "__main__":
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=is_debug, host="0.0.0.0", port=port)

    # memebot.handle_bot_response("Memebot meme")  # Testing

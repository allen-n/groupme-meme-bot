import json
import logging

# other imports
import os
import sys

import groupy.exceptions
from dotenv import load_dotenv
from flask import Flask, request

# Groupy imports
from groupy.client import Client

from memebot import Memebot

load_dotenv()

# Env setup
is_debug = True
logging_level = logging.DEBUG
api_token = os.environ.get("API_TOKEN")
memebot_token = os.environ.get("MEMEBOT_TOKEN")
testbot_token = None
GROUP_IDS = {"TESTGROUP": "59823729", "STEAK_PHILLY": "14970560"}
GROUP_ID = GROUP_IDS["TESTGROUP"]

if not memebot_token or not api_token:
    raise Exception("API_TOKEN or MEMEBOT_TOKEN not found in environment variables")


logging.basicConfig(stream=sys.stderr, level=logging_level)
client = Client.from_token(api_token)
memebot = Memebot(GROUP_ID, client, memebot_token, api_token)
app = Flask(__name__)


@app.route("/health")
def health():
    return "ok", 200


@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    data_str = "Message Text={}, Sender ID={}, Sender Name={}".format(
        data["text"], data["sender_id"], data["name"]
    )
    logging.info(data_str)
    if data["sender_type"] != "bot":  # Bots cannot reply to bots
        memebot.handle_bot_response(data["text"])

    return "ok", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=is_debug, host="0.0.0.0", port=port)

    # memebot.handle_bot_response("Memebot year")  # Testing

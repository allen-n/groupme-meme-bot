from flask import Flask, request

# Groupy imports
from groupy.client import Client
from groupy.api.groups import Group
import groupy.exceptions

# other imports
import os
import logging
import sys
import json
import time
import datetime

# Env setup
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
token = None
if(os.path.exists("./apitoken.json")):
    with open('./apitoken.json') as f:
        token = json.load(f)["token"]
else:
    token = os.environ.get("API_TOKEN")  # For deployment on Heroku

client = Client.from_token(token)
app = Flask(__name__)

# Constants
GROUP_ID = "59823729"
DELTAS = {
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7,
    "month": 60 * 60 * 24 * 7 * 4,
    "year": 60 * 60 * 24 * 365
}


@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    logging.info("Got Request :: {}".format(data))
    return "ok", 200


def name_to_grp(client: Client, name: str) -> Group:
    groups = client.groups.list_all()
    my_group = None
    for group in groups:
        if group.name == name:
            my_group = group
            break
    return my_group


def rejoin_if_out(client: Client, id: str) -> None:
    group = client.groups.get(id)
    try:
        member = group.get_membership()
        logging.debug("Already in group {}. Member ID: {}".format(
            group.name, member.id))
    except groupy.exceptions.MissingMembershipError as e:
        logging.debug("Not a member of {}, rejoining.".format(group.name))
        group.rejoin()


if __name__ == "__main__":
    # group = client.groups.get("14970560")  # Steak Philly ID
    group = client.groups.get("59823729")  # Testgroup ID

    now = time.time()
    best_msg = None
    for message in group.messages.list_all():
        delta = now - message.created_at.timestamp()
        if delta > 12 * DELTAS["month"]:
            break
        if not best_msg or len(message.favorited_by) > len(best_msg.favorited_by):
            best_msg = message

    new_message = "MEME AWARDS:\nMSG: {}, POSTER: {}, LIKES: {}".format(
        best_msg.text, best_msg.name, len(best_msg.favorited_by))
    group.post(text=new_message, attachments=best_msg.attachments)
    # app.run(debug=True)

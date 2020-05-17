from flask import Flask, request

# Groupy imports
from groupy.client import Client
from groupy.api.groups import Group
from groupy.api.bots import Bot
from groupy import attachments
import groupy.exceptions

# other imports
import os
import logging
import sys
import json
import time
import datetime

# Env setup
is_debug = True
logging_level = logging.DEBUG
api_token = None
memebot_token = None

if(os.path.exists("./apitoken.json")):  # Only true locally
    with open('./apitoken.json') as f:
        tokens = json.load(f)
        api_token = tokens["api_token"]
        memebot_token = tokens["memebot_token"]
else:
    # For deployment on Heroku
    api_token = os.environ.get("API_TOKEN")
    memebot_token = os.environ.get("MEMEBOT_TOKEN")
    is_debug = False
    logging_level = logging.INFO


logging.basicConfig(stream=sys.stderr, level=logging_level)
client = Client.from_token(api_token)
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
    logging.info("Message Text={}, Sender ID={}, Sender Name={}".format(
        data['text'], data['sender_id'], data['name']))
    if data["sender_type"] == "bot":  # Bots cannot reply to bots
        bot = get_bot(GROUP_ID, memebot_token)
        bot.post("HI! I heard: {}".format(data))
    return "ok", 200


def name_to_grp(client: Client, name: str) -> Group:
    '''
    @args:
    * client: The current Groupme Client
    * name: The name of the group to return
    @return:
    * Group: The group in client with .name attribute name
    '''
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


def get_bot(group_id: str, bot_id: str) -> Bot:
    group = client.groups.get(group_id)
    bots = group._bots.list()
    ret_bot = None
    for bot in bots:
        if bot.bot_id == bot_id:
            ret_bot = bot
            break
    return ret_bot


if __name__ == "__main__":
    # group = client.groups.get("14970560")  # Steak Philly ID
    group = client.groups.get("59823729")  # Testgroup ID

    # now = time.time()
    # best_msg = None
    # for message in group.messages.list_all():
    #     delta = now - message.created_at.timestamp()
    #     if delta > 12 * DELTAS["month"]:
    #         break
    #     if not best_msg or len(message.favorited_by) > len(best_msg.favorited_by):
    #         best_msg = message

    # new_message = "MEME AWARDS:\nMSG: {}, POSTER: {}, LIKES: {}".format(
    #     best_msg.text, best_msg.name, len(best_msg.favorited_by))
    # bots = group._bots.list()
    # memebot = None
    # for bot in bots:
    #     if bot.bot_id == memebot_token:
    #         memebot = bot
    #         break
    # if memebot:
    #     memebot.post(text=new_message, attachments=best_msg.attachments)

    port = int(os.environ.get('PORT', 5000))
    # TODO: Turn off for deploy
    app.run(debug=is_debug, host="0.0.0.0", port=port)

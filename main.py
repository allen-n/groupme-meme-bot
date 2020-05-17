from flask import Flask, request

# Groupy imports
from groupy.client import Client
from groupy.api.groups import Group
from groupy.api.bots import Bot
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
GROUP_ID = "59823729"  # Testgroup
GROUP_IDS = {"TESTGROUP": "59823729", "STEAK_PHILLY": "14970560"}

# group = client.groups.get("")  # Steak Philly ID
# group = client.groups.get("59823729")  # Testgroup ID
DELTAS = {  # all in seconds
    "day": 86400,
    "week": 604800,
    "month": 2628000,
    "year": 31540000
}

# Create the command strings for the bot
COMMAND_KEY = "memebot"
COMMANDS = ["meme", "help"]
for k in DELTAS:
    COMMANDS.append(k)

# TODO: Refactor into memebot class!


@app.route("/", methods=["POST"])
def home():
    data = request.get_json()
    data_str = "Message Text={}, Sender ID={}, Sender Name={}".format(
        data['text'], data['sender_id'], data['name'])
    logging.info(data_str)
    if data["sender_type"] != "bot":  # Bots cannot reply to bots
        handle_bot_response(data['text'])

    return "ok", 200


def get_meme() -> str:
    # memes from here: https://github.com/R3l3ntl3ss/Meme_Api
    r = requests.get("https://meme-api.herokuapp.com/gimme")
    return json.loads(r.text)


def handle_bot_response(txt: str) -> None:
    bot = get_bot(GROUP_ID, memebot_token)
    bot_string = ''
    txt = txt.lower()
    if re.search(COMMAND_KEY, txt):  # command key can be capitalized
        cmd = re.sub(COMMAND_KEY, '', txt)
        logging.info(cmd)
        word, score = process.extractOne(cmd, COMMANDS)
        if score >= 70:
            bot_string = "I think you said {}, is that right? Confidence: {}%".format(
                word, score)
            bot.post(text=bot_string)
            handle_command(word, bot)
        else:
            bot_string = "I'm not sure what you said (confidence is only {}%). Try saying '{} help'".format(
                score, COMMAND_KEY)
            bot.post(text=bot_string)


def send_meme(bot: Bot) -> None:
    meme_json = get_meme()
    meme_url = meme_json.get('url', '')
    meme_source = meme_json.get('postLink', '')
    meme_title = meme_json.get('title', '')
    img = attachments.Image(
        meme_url, source_url=meme_source)
    bot.post(text=meme_title, attachments=[img])


def send_help(bot: Bot) -> None:
    message = "Tell me what to do by sending the message {} <command>, where <command> can be:\n".format(COMMAND_KEY)
    message += "* meme: I'll send a meme\n* help: I'll say this message again\n"
    message += "* day/month/year: I'll return the most liked post over that time interval.\n* More stuff tbd"
    bot.post(text=message)


def handle_command(cmd_word: str, bot: Bot) -> None:
    switcher = {
        "meme": send_meme,
        "help": send_help
    }
    func = switcher.get(cmd_word, None)
    if func is not None:
        func(bot)
    return None


def name_to_grp(new_client: Client, name: str) -> Group:
    '''
    @args:
    * client: The current Groupme Client
    * name: The name of the group to return
    @return:
    * Group: The group in client with .name attribute name
    '''
    groups = new_client.groups.list_all()
    my_group = None
    for group in groups:
        if group.name == name:
            my_group = group
            break
    return my_group


def rejoin_if_out(new_client: Client, group_id: str) -> None:
    group = new_client.groups.get(group_id)
    try:
        member = group.get_membership()
        logging.debug("Already in group {}. Member ID: {}".format(
            group.name, member.id))
    except groupy.exceptions.MissingMembershipError as e:
        logging.debug(
            "Not a member of {}, rejoining. Error: {}".format(group.name, e))
        group.rejoin()


def get_bot(group_id: str, bot_id: str) -> Bot:
    group = client.groups.get(group_id)
    # Intentional private member access, no other way to access bots in group via api
    bots = group._bots.list()  # skipcq: PYL-W0212
    ret_bot = None
    for bot in bots:
        if bot.bot_id == bot_id:
            ret_bot = bot
            break
    return ret_bot


def find_best_post(group: Group, deltas: {str: int}) -> str:
    '''
    Return info about the most liked message

    :param Group group: a group object
    :param deltas {str:int}: a dict mapping time period 
    strings (i.e. week) to time in seconds
    :return: String containing info about the most liked post
    :rtype: str
    '''
    now = time.time()
    best_msg = None
    for message in group.messages.list_all():
        delta = now - message.created_at.timestamp()
        if delta > 12 * deltas["month"]:
            break
        if not best_msg or len(message.favorited_by) > len(best_msg.favorited_by):
            best_msg = message

    new_message = "MEME AWARDS:\nMSG: {}, POSTER: {}, LIKES: {}".format(
        best_msg.text, best_msg.name, len(best_msg.favorited_by))
    return new_message


if __name__ == "__main__":

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=is_debug, host="0.0.0.0", port=port)

    # handle_bot_response("Memebot halp")  # Testing

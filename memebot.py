
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


class Memebot:
    """A Groupy wrapper for a memebot."""

    def __init__(self, group_id: str, client: groupy.Client,
                 bot_token: str, api_token: str):
        # time deltas in seconds
        self._deltas = {
            "day": 86400,
            "week": 604800,
            "month": 2628000,
            "year": 31540000
        }
        self._command_key = "memebot"
        self._commands = ["meme", "help"]
        for k in self._deltas:
            self._commands.append(k)

        self._group_id = group_id
        self._bot_token = bot_token
        self._api_token = api_token
        self._client = client
        self._bot = None

    @property
    def command_key(self):
        return self._command_key

    @property
    def commands(self):
        return self._commands

    @property
    def deltas(self):
        return self._deltas

    @property
    def group_id(self):
        return self._group_id

    @group_id.setter
    def group_id(self, value):
        self._group_id = value

    def get_meme(self) -> str:
        '''
        Return a Json with meme data in the format: 
        {
            "postLink": "https://redd.it/9vqgv2",
            "subreddit": "memes",
            "title": "Good mor-ning Reddit!...",
            "url": "https://i.redd.it/yykt3r9zsex11.png"
        }
        '''
        # memes from here: https://github.com/R3l3ntl3ss/Meme_Api
        r = requests.get("https://meme-api.herokuapp.com/gimme")
        return json.loads(r.text)

    def handle_bot_response(self, txt: str) -> None:
        '''
        Entrypoint for memebot to handle incoming requests.
        :param str text: incoming text portion of data object
        '''
        bot = self.get_bot(self._bot_token)
        bot_string = ''
        txt = txt.lower()
        if re.search(self._command_key, txt):  # command key can be capitalized
            cmd = re.sub(self.command_key, '', txt)
            word, score = process.extractOne(cmd, self._commands)
            if score >= 70:
                # bot_string = "I think you said {}, is that right? Confidence: {}%".format(
                #     word, score)
                # bot.post(text=bot_string)
                self.handle_command(word, bot)
            else:
                bot_string = "I'm not sure what you said (confidence is only {}%). Try saying '{} help'".format(
                    score, self._command_key)
                bot.post(text=bot_string)


    def send_meme(self, bot: Bot) -> None:
        meme_json = self.get_meme()
        meme_url = meme_json.get('url', '')
        meme_source = meme_json.get('postLink', '')
        meme_title = meme_json.get('title', '')
        img = attachments.Image(
            meme_url, source_url=meme_source)
        bot.post(text=meme_title, attachments=[img])


    def send_help(self, bot: Bot) -> None:
        message = "Tell me what to do by sending the message {} <command>, where <command> can be:\n".format(
            self._command_key)
        message += "* meme: I'll send a meme\n* help: I'll say this message again\n"
        message += "* day/month/year: I'll return the most liked post over that time interval.\n* More stuff tbd"
        bot.post(text=message)


    def handle_command(self, cmd_word: str, bot: Bot) -> None:
        switcher = {
            "meme": self.send_meme,
            "help": self.send_help
        }
        func = switcher.get(cmd_word, None)
        if func is not None:
            func(bot)
        else:
            # Hitting this else, the command must be a command word not in the switcher
            group = self._client.groups.get(self._group_id)
            text, attachment = self.find_best_post(group, cmd_word)
            bot.post(text=text, attachments=attachment)
        return None


    def name_to_grp(self, name: str) -> Group:
        '''
        @args:
        * client: The current Groupme Client
        * name: The name of the group to return
        @return:
        * Group: The group in client with .name attribute name
        '''
        groups = self._client.groups.list_all()
        my_group = None
        for group in groups:
            if group.name == name:
                my_group = group
                break
        return my_group


    def get_bot(self, bot_id: str) -> Bot:
        ret_bot = None
        if self._bot is None:
            group = self._client.groups.get(self._group_id)
            # Intentional private member access, no other way to access bots in group via api
            bots = group._bots.list()  # skipcq: PYL-W0212

            for bot in bots:
                if bot.bot_id == bot_id:
                    ret_bot = bot
                    break
            self._bot = ret_bot
        else:
            ret_bot = self._bot

        return ret_bot


    def find_best_post(self, group: Group, time_str: str) -> (str, attachments):
        '''
        Return info about the most liked message

        :param Group group: a group object
        :param deltas {str:int}: a dict mapping time period 
        strings (i.e. week) to time in seconds
        :return: String containing info about the most liked post, and the posts attachments
        :rtype: (str, attachments)
        '''
        now = time.time()
        best_msg = None
        for message in group.messages.list_all():
            delta = now - message.created_at.timestamp()
            if delta > self._deltas[time_str]:
                break
            if not best_msg or len(message.favorited_by) > len(best_msg.favorited_by):
                best_msg = message

        # new_message = "MEME AWARDS:\nMSG: {}, POSTER: {}, LIKES: {}".format(
        #     best_msg.text, best_msg.name, len(best_msg.favorited_by))
        text = "Best post of the last {} by {} with {} likes:\n".format(
            time_str, best_msg.name, len(best_msg.favorited_by)) + best_msg.text
        return (text, best_msg.attachments)

"""
A Groupy wrapper for a memebot.

This module provides the Memebot class which utilizes the Groupy API, processes commands,
and responds with memes and other data as appropriate.
"""

from typing import Any, Dict, Tuple, List, Optional, Callable
import json
import re
import time
import requests

from groupy.api.groups import Group
from groupy.api.bots import Bot
from groupy import attachments
import groupy.exceptions

# Fuzzy matching
from fuzzywuzzy import process


class Memebot:
    """
    A class to handle meme commands using Groupy client.

    :ivar _deltas: Dictionary mapping time periods to seconds.
    :ivar _command_key: Key to trigger commands.
    :ivar _commands: List of available commands.
    :ivar _group_id: ID of the group.
    :ivar _bot_token: Bot token.
    :ivar _api_token: API token.
    :ivar _client: Groupy client instance.
    :ivar _bot: The cached bot instance.
    """

    def __init__(
        self, group_id: str, client: Any, bot_token: str, api_token: str
    ) -> None:
        """
        Initialize the Memebot.

        :param group_id: The identifier for the group.
        :param client: The Groupy client object.
        :param bot_token: The bot token.
        :param api_token: The API token.
        """
        self._deltas: Dict[str, int] = {
            "day": 86400,
            "week": 604800,
            "month": 2628000,
            "year": 31540000,
        }
        self._command_key: str = "memebot"
        self._commands: List[str] = ["meme", "help"]
        for k in self._deltas:
            self._commands.append(k)

        self._group_id: str = group_id
        self._bot_token: str = bot_token
        self._api_token: str = api_token
        self._client: Any = client
        self._bot: Optional[Bot] = None

    @property
    def command_key(self) -> str:
        """
        Get the command key.

        :return: The command key.
        """
        return self._command_key

    @property
    def commands(self) -> List[str]:
        """
        Get the list of available commands.

        :return: List of command strings.
        """
        return self._commands

    @property
    def deltas(self) -> Dict[str, int]:
        """
        Get the dictionary of time delta mappings.

        :return: A dictionary mapping time period names to seconds.
        """
        return self._deltas

    @property
    def group_id(self) -> str:
        """
        Get the group ID.

        :return: The group ID.
        """
        return self._group_id

    @group_id.setter
    def group_id(self, value: str) -> None:
        """
        Set a new group ID.

        :param value: The new group ID.
        """
        self._group_id = value

    def get_meme(self) -> Dict[str, Any]:
        """
        Get meme data from the meme API.

        :return: A dictionary with meme data in the format:
                 {
                     "postLink": "...",
                     "subreddit": "...",
                     "title": "...",
                     "url": "..."
                 }
        :raises requests.exceptions.RequestException: If the API request fails.
        """
        response = requests.get("https://meme-api.herokuapp.com/gimme")
        response.raise_for_status()
        return json.loads(response.text)

    def handle_bot_response(self, txt: str) -> None:
        """
        Handle an incoming text message and respond with a bot message if appropriate.

        :param txt: The incoming text message.
        """
        bot = self.get_bot(self._bot_token)
        if not bot:
            return

        txt_lower = txt.lower()
        if re.search(self._command_key, txt_lower):
            cmd = re.sub(self._command_key, "", txt_lower).strip()
            # Use fuzzy matching to determine the best command
            word, score = process.extractOne(cmd, self._commands)  # type: ignore
            if score >= 70:
                self.handle_command(word, bot)
            else:
                bot_string = (
                    f"I'm not sure what you said (confidence is only {score}%). "
                    f"Try saying '{self._command_key} help'"
                )
                bot.post(text=bot_string)

    def send_meme(self, bot: Bot) -> None:
        """
        Retrieve a meme and send it using the provided bot.

        :param bot: The bot instance used to post the meme.
        :raises requests.exceptions.RequestException: If the meme API request fails.
        """
        meme_json = self.get_meme()
        meme_url = meme_json.get("url", "")
        meme_source = meme_json.get("postLink", "")
        meme_title = meme_json.get("title", "")
        img = attachments.Image(meme_url, source_url=meme_source)
        bot.post(text=meme_title, attachments=[img])

    def send_help(self, bot: Bot) -> None:
        """
        Send a help message outlining available commands.

        :param bot: The bot instance used to post the help message.
        """
        message = (
            f"Tell me what to do by sending the message {self._command_key} <command>, "
            "where <command> can be:\n"
            "* meme: I'll send a meme\n"
            "* help: I'll say this message again\n"
            "* day/month/year: I'll return the most liked post over that time interval.\n"
            "* More stuff tbd"
        )
        bot.post(text=message)

    def handle_command(self, cmd_word: str, bot: Bot) -> None:
        """
        Execute the command identified by cmd_word.

        :param cmd_word: The command word to handle.
        :param bot: The bot instance to use for posting.
        """
        switcher: Dict[str, Callable[[Bot], None]] = {
            "meme": self.send_meme,
            "help": self.send_help,
        }
        func = switcher.get(cmd_word)
        if func is not None:
            func(bot)
        else:
            group: Group = self._client.groups.get(self._group_id)
            text, attachment = self.find_best_post(group, cmd_word)
            bot.post(text=text, attachments=attachment)

    def name_to_grp(self, name: str) -> Optional[Group]:
        """
        Retrieve a group by its name.

        :param name: The name of the group.
        :return: The group with the specified name or None if not found.
        """
        groups = self._client.groups.list_all()
        for group in groups:
            if group.name == name:
                return group
        return None

    def get_bot(self, bot_id: str) -> Optional[Bot]:
        """
        Retrieve the bot object corresponding to the given bot ID.

        :param bot_id: The bot identifier.
        :return: The Bot object if found, else None.
        """
        if self._bot is None:
            group: Group = self._client.groups.get(self._group_id)
            # Intentional private member access, as no public API is available for bots
            bots = group._bots.list()  # skipcq: PYL-W0212
            for bot in bots:
                if bot.bot_id == bot_id:
                    self._bot = bot
                    break
        return self._bot

    def find_best_post(self, group: Group, time_str: str) -> Tuple[str, List[Any]]:
        """
        Find the best post (with highest likes) within a specified time interval.

        :param group: The group from which to search messages.
        :param time_str: The key to select a time interval from _deltas.
        :return: A tuple containing a string summary of the best post and its attachments.
        :raises KeyError: If time_str is not a valid key in _deltas.
        """
        now = time.time()
        best_msg = None
        for message in group.messages.list_all():
            delta = now - message.created_at.timestamp()
            if delta > self._deltas[time_str]:
                break
            if best_msg is None or len(message.favorited_by) > len(
                best_msg.favorited_by
            ):
                best_msg = message

        if best_msg is None:
            return ("No posts found in the given period.", [])

        text = (
            f"Best post of the last {time_str} by {best_msg.name} with "
            f"{len(best_msg.favorited_by)} likes:\n" + (best_msg.text or "")
        )
        return (text, best_msg.attachments)

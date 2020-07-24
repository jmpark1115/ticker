#!/usr/bin/env python
# coding: utf-8
import requests

API_URL = "https://api.telegram.org/bot"

class Telegram:    

    def __init__(self, key) :
        self.key = key

    def get_me(self):
        url = API_URL + self.key + "/getMe"
        resp = requests.get(url)
        return resp.json()

    def get_updates(self):
        url = API_URL + self.key + "/getUpdates"
        resp = requests.get(url)
        return resp.json()

    def message(self, message, chat_id):
        url = API_URL + self.key + "/sendMessage"
        params = {
                  "chat_id": chat_id,
                  "text": message
        }
        resp = requests.post(url, params=params)
        content = resp.json()
        return content

if __name__ == "__main__":
    # Load Config File
    from configparser import ConfigParser, NoSectionError
    # Load Config File
    config = ConfigParser()
    config.read('trading.conf')
    chat_id    = config.get('ChatBot', 'chatId')
    chat_token = config.get('ChatBot', 'chatToken')

    tg = Telegram(chat_token)
    result = tg.message("welcome to my telegram message service", chat_id)
    print(result)
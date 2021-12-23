import json
import random
import os
import sys


class _AppConfig():

    def __init__(self):
        self.cfg = {}
        self.__load_config_file()


    def __load_config_file(self):
        try:
            with open('config.json') as f:
                self.cfg = json.load(f)
        except FileNotFoundError:
            cfg = { 
                'id'      : random.randint(100, 1000000),
                'osu_dir' : '' 
            }

            with open('config.json', 'w') as f:
                json.dump(cfg, f, indent=4)

            with open('config.json') as f:
                self.cfg = json.load(f)


    def update_value(self, key, value):
        self.cfg[key] = value

        with open('config.json', 'w') as f:
            json.dump(self.cfg, f, indent=4)


AppConfig = _AppConfig()
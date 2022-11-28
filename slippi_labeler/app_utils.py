import os
import glob
from datetime import datetime
import json

from dateutil import parser
from slippi import Game
import dearpygui.dearpygui as dpg

def extract_metadata(slp_fp: str):
    game = Game(slp_fp)
    def _character_name(p):
        return p if not p else p.character.name
    return {
        'path': os.path.basename(slp_fp),
        'characters': list(map(_character_name, game.start.players)),
        'stage': game.start.stage.name,
        'date': game.metadata.date
    }


def game_summary(game: Game):
    summary = ''
    for player in game.start.players:
        if player != None:
            summary += player.character.name + ' '
    summary += 'on ' + game.start.stage.name
    return summary

def format_date(date: str, date_format = "%m/%d/%Y, %H:%M:%S") -> str:
    return parser.parse(date).strftime(date_format)


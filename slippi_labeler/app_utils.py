import os
import time
from dateutil import parser

from slippi import Game
from slugify import slugify


def extract_metadata(slp_fp: str):
    game = Game(slp_fp)

    def _character_name(p):
        return p if not p else p.character.name

    return {
        "path": slp_fp,
        "characters": list(map(_character_name, game.start.players)),
        "stage": game.start.stage.name,
        "date": game.metadata.date,
    }


def game_summary(metadata):
    summary = [character for character in metadata["characters"] if character]
    return ", ".join(summary) + " on " + metadata["stage"]


def format_date(date: str, date_format="%m/%d/%Y, %H:%M:%S") -> str:
    return parser.parse(date).strftime(date_format)


def initialize_empty_array_file(path, base_name):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    newfile_path = os.path.join(path, f"{timestamp}-{base_name}.json")
    with open(newfile_path, "w+") as f:
        f.write("[]")
    return newfile_path


def unique_participants(annotations_fp):
    with open(annotations_fp, "r") as f:
        # TODO: Parse the annotations file and get all the unique players
        return ["foo", "bar", "baz"]


def generate_tournament_annotations(path, tournament_name):
    return initialize_empty_array_file(path, f"annotations_{slugify(tournament_name)}")

import sys
import time
import logging
from functools import partial
from pathlib import Path
import os 
import json
import threading
import glob 

from slippi import Game

from watchdog.observers import Observer
from watchdog.events import (
    LoggingEventHandler, 
    FileSystemEventHandler, 
)

FILE_CREATED_EVENT = 'created'
FILE_DELETED_EVENT = 'deleted'

from app_utils import extract_metadata

class MyHandler(FileSystemEventHandler):
    def __init__(self, metadata_filepath: str, modified_callback):
        self.metadata_filepath = metadata_filepath
        self.modified_callback = modified_callback
    
    def on_any_event(self, event):
        all_games = []
        with open(self.metadata_filepath, 'r') as f:
            all_games = json.load(f)
        with open(self.metadata_filepath, 'w') as output_file:
            if event.event_type == FILE_DELETED_EVENT:
                all_games = [d for d in all_games if d['file_path'] != event.src_path]
            if event.event_type == FILE_CREATED_EVENT:
                all_games.append(extract_metadata(event.src_path))
            json.dump(all_games, output_file, indent=4, default=str)
            self.modified_callback(all_games)


class MyWatcher:
    def __init__(self, metadata_path, cb):
        self.metadata_path = metadata_path
        self.event_handler = MyHandler(metadata_path, cb)
        self.observer = Observer()

    def run(self, slippi_dir, sleep_interval=5):
        self.observer.schedule(self.event_handler, slippi_dir, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(sleep_interval)
        except:
            self.observer.stop()
        self.observer.join()


    def preprocess_games(slippi_dir, metadata_path, cb):
        all_games = []
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                all_games = json.load(f)
        slippi_file_paths = glob.glob(slippi_dir + '/**/*.slp', recursive=True)
        for idx, slp_fp in enumerate(slippi_file_paths):
            if all(g['path'] != os.path.basename(slp_fp) for g in all_games):
                all_games.append(extract_metadata(slp_fp))
                cb(idx / len(slippi_file_paths))
        with open(metadata_path, 'w+') as f:
            json.dump(all_games, f, indent=4, default=str)
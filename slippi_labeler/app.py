from datetime import datetime
import glob
import os
import json
import threading

from slippi import Game
import dearpygui.dearpygui as dpg

import app_utils as utils
from watch import MyWatcher
# TODO REMOVE CONSTANTS
metadata_path = '/home/coy/code/slippi-website/slippi_labeler/metadata.json'

class SlippiLabeler:

    metadata_path = '/home/coy/code/slippi-website/slippi_labeler/metadata.json'
    slippi_dir = '/home/coy/code/slippi-website/slippi_files'

    def run(self):
        dpg.create_context()
        dpg.create_viewport(title='Custom Title', width=600, height=600)
        dpg.add_file_dialog(
            directory_selector=True,
            show=False,
            callback=self.todo,  
            tag="slippi_dir_dialog_id"
        )
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.todo,
            tag="annotations_file_dialog_id"):
            dpg.add_file_extension(".json")
        with dpg.window(tag="Config Window"):
            dpg.add_button(label="Slippi Directory", callback=lambda: dpg.show_item("slippi_dir_dialog_id"))
            dpg.add_button(label="Annotations File", callback=lambda: dpg.show_item("annotations_file_dialog_id"))
            dpg.add_button(label="Submit", callback=lambda _: [self.display_loading_view(), self.start_watcher()])
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Config Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def display_loading_view(self):
        dpg.delete_item("Config Window")
        with dpg.window(tag="Loading Window"):
            dpg.add_slider_float(
                label="Reading Slippi Files",
                tag="Progress Bar",
                min_value=0,
                max_value=1
            )
        dpg.set_primary_window("Loading Window", True)
        

    def display_annotation_view(self):
        dpg.delete_item("Loading Window")
        self.set_main_window()
        self.draw_games_table(self.metadata_path)
        dpg.set_primary_window("Main Window", True)

    

    def set_main_window(self):
        with dpg.window(tag="Main Window"):
            with dpg.menu_bar():
                with dpg.menu(label="Settings"):
                    dpg.add_input_text(label="Default Tournament Name", callback=self.todo)
                    dpg.add_button(label="Slippi Directory", callback=lambda: dpg.show_item("slippi_dir_dialog_id"))
                    dpg.add_button(label="Annotations File", callback=lambda: dpg.show_item("annotations_file_dialog_id"))
                dpg.add_menu_item(label="Help", callback=self.todo)

            dpg.add_group(horizontal=True, tag='Main Content')
    

    def draw_games_table(self, metadata_path):
        dpg.delete_item('Games Table')
        with dpg.table(header_row=True,
            resizable=True, 
            policy=dpg.mvTable_SizingStretchProp,
            borders_outerH=True,
            borders_innerV=True, 
            borders_innerH=True, 
            borders_outerV=True,
            tag='Games Table',
            parent='Main Content'
        ):
            dpg.add_table_column(label="Group")
            dpg.add_table_column(label="Stage")
            dpg.add_table_column(label="P1")
            dpg.add_table_column(label="P2")
            dpg.add_table_column(label="P3")
            dpg.add_table_column(label="P4")
            dpg.add_table_column(label="Date")
            
            metadata = json.load(open(metadata_path, 'r'))
            for m in metadata:
                self.draw_game_row(m)
        

    def draw_game_row(self, metadata):
        with dpg.table_row():
            with dpg.table_cell():
                dpg.add_checkbox()
            with dpg.table_cell():
                dpg.add_text(metadata['stage'])
            for character in metadata['characters']:
                with dpg.table_cell():
                    if not character:
                        dpg.add_text("-")
                    else:
                        dpg.add_text(character)
            with dpg.table_cell():
                dpg.add_text(utils.format_date(metadata['date']))

    def todo():
        print(f"To Be Made")

    def start_watcher(self, preprocess = True):
        w = MyWatcher(self.metadata_path, print)
        if preprocess:
            MyWatcher.preprocess_games(self.slippi_dir, self.metadata_path, self.update_progress_bar)
            self.display_annotation_view()
        x = threading.Thread(target=w.run, args=(self.slippi_dir,), daemon=True)
        x.start()

    def update_progress_bar(self, progress):
        print("Hello")
        dpg.set_value("Progress Bar", progress)


if __name__ == "__main__":
    s = SlippiLabeler()
    s.run()
from datetime import datetime
import glob
import os
import json
import threading

from slippi import Game
import dearpygui.dearpygui as dpg

import app_utils as utils
from watch import MyWatcher
from query_startgg import StartClient 

class SlippiLabeler:

    def __init__(self, width=600, height=600):
        self.width = width
        self.height = height
    
    def run(self):
        dpg.create_context()
        dpg.create_viewport(title='Slippi Annotator', width=600, height=600)
        dpg.setup_dearpygui()
        self.display_configuration_view()
        dpg.show_viewport()
        dpg.set_primary_window("Config Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()



    def set_tournament(self):
        self.tournament_name = dpg.get_value('tournament_input')
        self.participants = utils.unique_participants(self.annotations_path)
        client = StartClient(dpg.get_value('token_input'))
        results = client.get_participants(self.tournament_name)
        if results:
            self.participants = results['participants']
            self.tournament_name = results['tournament_name']
    
    def developer_override(self):
        # TODO: Remove, this is a spoof of submit_configuration

        self.metadata_path = '/home/coy/code/slippi-website/slippi_labeler/metadata.json'
        self.annotations_path = '/home/coy/code/slippi-website/slippi_labeler/annotations.json'
        self.slippi_dir = '/home/coy/code/slippi-website/slippi_files'
        self.tournament_name = 'ludwig-smash-invitational'
        self.display_loading_view()
        self.start_watcher(preprocess=True)
        client = StartClient(dpg.get_value('token_input'))
        results = client.get_participants(self.tournament_name)
        if results:
            self.participants = results['participants']
            self.tournament_name = results['tournament_name']


    def submit_configuration(self):
        if not self.slippi_dir:
            dpg.add_text("You need to provide a slippi directory")
            return
        
        if not self.tournament_name:
            dpg.add_text("You need to provide a tournament name")
            return

        if not self.metadata_path:
            self.metadata_path = utils.initialize_empty_array_file(
                self.slippi_dir,
                'metadata'
            )
        
        if not self.annotations_path:
            self.annotations_path = utils.generate_tournament_annotations(
                self.slippi_dir,
                self.tournament_name
            )
        self.display_loading_view()
        self.start_watcher(preprocess=True)
        self.set_tournament()


    def setter_generator(self, attr_name: str):
        def setter(_, app_data):
            setattr(self, attr_name, app_data['file_path_name'])
        return setter


    def display_configuration_view(self):
            dpg.add_file_dialog(
                directory_selector=True,
                show=False,
                callback=self.setter_generator('slippi_dir'),  
                tag="slippi_dir_dialog_id"
            )

            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=self.setter_generator('annotations_path'),  
                tag="annotations_file_dialog_id"):
                dpg.add_file_extension(".json")
        
            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=self.setter_generator('metadata_path'),  
                tag="metadata_file_dialog_id"):
                dpg.add_file_extension(".json")


            with dpg.window(tag="Config Window"):
                dpg.add_button(label="Developer Override", callback=self.developer_override)
                dpg.add_button(label="Slippi Directory", callback=lambda: dpg.show_item("slippi_dir_dialog_id"))
                dpg.add_button(label="Annotations File", callback=lambda: dpg.show_item("annotations_file_dialog_id"))
                dpg.add_button(label="Annotations File", callback=lambda: dpg.show_item("metadata_file_dialog_id"))
                dpg.add_input_text(label="Start.gg API Token", tag="token_input", password=True)
                dpg.add_input_text(label="Tournament", tag="tournament_input")

                dpg.add_button(label="Submit", callback=self.submit_configuration)
        

    def display_loading_view(self):
        dpg.delete_item("Config Window")
        with dpg.window(tag="Loading Window"):
            dpg.add_slider_float(
                label="Reading Slippi Files",
                tag="Progress Bar",
                min_value=0,
                max_value=1,
                no_input=True
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
                dpg.add_menu_item(label="Annotate", callback=self.handle_annotate)
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
            self.checkbox_ids = []
            for m in metadata:
                self.draw_game_row(m)
        

    def draw_game_row(self, metadata):
        with dpg.table_row():
            with dpg.table_cell():
                self.checkbox_ids.append(
                    dpg.add_checkbox(label=f"{metadata['path']}"))
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


    def start_watcher(self, preprocess = False):
        w = MyWatcher(self.metadata_path, print)
        if preprocess:
            MyWatcher.preprocess_games(self.slippi_dir, self.metadata_path, self.update_progress_bar)
            self.display_annotation_view()
        x = threading.Thread(target=w.run, args=(self.slippi_dir,), daemon=True)
        x.start()


    def update_progress_bar(self, progress):
        dpg.set_value("Progress Bar", progress)


    def handle_annotate(self):
        self.launch_annotation_dialog(self.combine_game_checked())


    def launch_annotation_dialog(self, items):
        with dpg.window(label="Annotations",
            width=self.width,
            height=self.height,
            modal=True):
            with dpg.table(header_row=True,
                resizable=True, 
                policy=dpg.mvTable_SizingStretchProp,
                borders_outerH=True,
                borders_innerV=True, 
                borders_innerH=True, 
                borders_outerV=True,
                tag='Annotations Table',
            ):
                dpg.add_table_column(label="Description")
                dpg.add_table_column(label="P1")
                dpg.add_table_column(label="P2")
                dpg.add_table_column(label="P3")
                dpg.add_table_column(label="P4")
                for item in items:
                    metadata = utils.extract_metadata(item[0])
                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_text(utils.game_summary(metadata))
                        for port, char in enumerate(metadata['characters']):
                            with dpg.table_cell():
                                if not char:
                                    dpg.add_text("")
                                else:
                                    dpg.add_text(char)
                                    dpg.add_input_text(label="##Participant", tag=f'{item[0]}-{port}')
                                    dpg.add_combo(items=self.participants, source=f'{item[0]}-{port}')


    def combine_game_checked(self, filter=True):
        zipped_vals = list(zip(
            [dpg.get_item_configuration(cid)['label'] for cid in self.checkbox_ids],
            dpg.get_values(self.checkbox_ids)
        ))
        if filter:
            zipped_vals = [v for v in zipped_vals if v[1]]
        return zipped_vals


    
if __name__ == "__main__":
    s = SlippiLabeler()
    s.run()
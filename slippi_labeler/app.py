import json
import threading
from typing import List, Union

import dearpygui.dearpygui as dpg

import app_utils as utils
from watch import MyWatcher
from query_startgg import StartClient
from schemas import SlippiLabelerGame, GlobalViewUI as gbv


class SlippiLabeler:
    def __init__(self, width=600, height=600):
        """Slippi Labeler Instance, when called with run, displays a Slippi Labeler UI

        Args:
            width (int, optional): Width of the viewport. Defaults to 600.
            height (int, optional): Height of the viewport. Defaults to 600.
        """
        self.width = width
        self.height = height

    def run(self):
        """Displays the Slippi Labeler GUI"""
        dpg.create_context()
        dpg.create_viewport(
            title="Slippi Annotator", 
            width=gbv.window_width, 
            height=gbv.window_height,
            resizable=True,
                
        )
        dpg.setup_dearpygui()
        self.set_font()
        
        self.display_configuration_view()
        
        dpg.show_viewport()
        dpg.set_primary_window("Config Window", True)
        self.set_theme()
        dpg.start_dearpygui()
        dpg.destroy_context()
        

    def set_font(self):
        with dpg.font_registry():
            default_font = dpg.add_font("fonts/SpaceGrotesk-Regular.ttf", 20)
            dpg.bind_font(default_font)
    
    def set_theme(self, item=None):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0,0,0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (242, 213, 86), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (228, 225, 219), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (228, 225, 219), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (242, 213, 86), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (0,0,0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (228, 225, 219), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (0,0,0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (228, 225, 219), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (0,0,0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (0,0,0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (228, 225, 219), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, (228, 225, 219), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
        if not item:
            dpg.bind_theme(theme)
        else:
            dpg.bind_item_theme(item, theme)
        

    def set_tournament(self):
        """Set the tournament name from the tournament field,
        prefetch the participants list from Start GG API"""

        client = StartClient(dpg.get_value("token_input"))
        results = client.get_participants(self.tournament_name)
        if results:
            self.participants = results["participants"]
            self.tournament_name = results["tournament_name"]
        else:
            self.participants = utils.unique_participants(self.annotations_path)

    def developer_override(self):
        """Overwrite inputting the tournament information, for debugging purposes"""
        # TODO: Remove, this is a spoof of submit_configuration
        self.metadata_path = (
            "/home/coy/code/slippi-website/slippi_labeler/metadata.json"
        )
        self.annotations_path = (
            "/home/coy/code/slippi-website/slippi_labeler/annotations.json"
        )
        self.slippi_dir = "/home/coy/code/slippi-website/slippi_files"
        self.tournament_name = "ludwig-smash-invitational"

        client = StartClient(dpg.get_value("token_input"))
        results = client.get_participants(self.tournament_name)
        if results:
            self.participants = results["participants"]
            self.tournament_name = results["tournament_name"]

        self.display_loading_view()
        self.start_watcher(preprocess=True)

    def submit_configuration(self):
        """
        Submit the configuration, listen to changes in the Slippi Directory,
        and prefetch tournament participants
        """
        if not hasattr(self, "slippi_dir"):
            dpg.add_text(
                "You need to provide a slippi directory",
                parent="Form Validation Errors",
                color=gbv.failure_text_color,
            )
            return

        if not dpg.get_value("tournament_input"):
            dpg.add_text(
                "You need to provide a tournament name",
                parent="Form Validation Errors",
                color=gbv.failure_text_color,
            )
            return
        self.tournament_name = dpg.get_value("tournament_input")

        if not hasattr(self, "metadata_path"):
            self.metadata_path = utils.initialize_empty_array_file(
                self.slippi_dir, "metadata"
            )

        if not hasattr(self, "annotations_path"):
            self.annotations_path = utils.generate_tournament_annotations(
                self.slippi_dir, self.tournament_name
            )
        self.display_loading_view()
        self.start_watcher(preprocess=True)
        self.set_tournament()

    def setter_generator(self, attr_name: str):
        """Return a function that sets a local field

        Args:
            attr_name (str): class name of Slippi Labeler to set
        """

        def set_and_update_label(_, app_data):
            setattr(self, attr_name, app_data["file_path_name"])
            dpg.configure_item(
                f"{attr_name}_label",
                default_value=app_data["file_path_name"],
                color=gbv.success_text_color,
            )

        return set_and_update_label

    def display_configuration_view(self):
        """Display the Welcome/Configuration screen, display the various configuration fields"""
        dpg.add_file_dialog(
            directory_selector=True,
            show=False,
            callback=self.setter_generator("slippi_dir"),
            tag="slippi_dir_dialog_id",
            height=gbv.file_selector_height,
        )

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.setter_generator("annotations_path"),
            tag="annotations_file_dialog_id",
            height=gbv.file_selector_height,
        ):
            dpg.add_file_extension(".json")

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.setter_generator("metadata_path"),
            tag="metadata_file_dialog_id",
            height=gbv.file_selector_height,
        ):
            dpg.add_file_extension(".json")

        with dpg.window(tag="Config Window") as config_window:
            dpg.add_button(label="Developer Override", callback=self.developer_override)
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Slippi Folder",
                    callback=lambda: dpg.show_item("slippi_dir_dialog_id"),
                    width=gbv.medium_button_width,
                    height=gbv.medium_button_height,
                )
                dpg.add_text(
                    "Required. Update based on Slippi Files in this folder and subfolders",
                    tag="slippi_dir_label",
                    color=gbv.info_text_color,
                )

            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Annotations File (Optional)",
                    callback=lambda: dpg.show_item("annotations_file_dialog_id"),
                    width=gbv.medium_button_width,
                    height=gbv.medium_button_height,
                )
                
                dpg.add_text(
                    "Optional. Where to write the completed annotations. One will be created for you if left blank",
                    tag="annotations_path_label",
                    color=gbv.info_text_color,
                )

            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Metadata File (Optional)",
                    callback=lambda: dpg.show_item("metadata_file_dialog_id"),
                    width=gbv.medium_button_width,
                    height=gbv.medium_button_height,
                )
                dpg.add_text(
                    "Optional. Where to store the Slippi games metadata. Leave empty if unsure",
                    tag="metadata_path_label",
                    color=gbv.info_text_color,
                )

            dpg.add_input_text(
                label="Start.gg API Token (Optional)", tag="token_input", password=True
            )

            dpg.add_input_text(
                label="Tournament Slug or Tournament", tag="tournament_input"
            )
            dpg.add_group(tag="Form Validation Errors")
            dpg.add_button(
                label="Submit",
                callback=self.submit_configuration,
                height=gbv.large_button_height,
                width=gbv.large_button_width,
            )
        

    def display_loading_view(self):
        """Display Loading Bar view while Slippi Files are parsed"""
        dpg.delete_item("Config Window")
        with dpg.window(tag="Loading Window"):
            dpg.add_slider_float(
                label="Reading Slippi Files",
                tag="Progress Bar",
                min_value=0,
                max_value=1,
                no_input=True,
            )
        dpg.set_primary_window("Loading Window", True)

    def draw_menu_bar(self):
        with dpg.menu_bar(parent="Main Window"):
            with dpg.menu(label="Settings"):
                dpg.add_input_text(label="Default Tournament Name", callback=self.todo)
                dpg.add_button(
                    label="Slippi Directory",
                    callback=lambda: dpg.show_item("slippi_dir_dialog_id"),
                )
                dpg.add_button(
                    label="Annotations File",
                    callback=lambda: dpg.show_item("annotations_file_dialog_id"),
                )
            dpg.add_menu_item(label="Help", callback=self.todo)
            dpg.add_menu_item(label="Annotate", callback=self.launch_annotation_dialog)
            dpg.add_menu_item(label="Export", callback=self.export_annotations)

    def display_annotation_view(self):
        """
        Display game index view
        """
        dpg.delete_item("Loading Window")
        with dpg.window(tag="Main Window"):
            self.draw_menu_bar()
            with dpg.group(horizontal=True, tag="Main Content"):
                dpg.add_child_window(
                    tag="Left Window",
                    width=1200,
                    horizontal_scrollbar=True,
                    autosize_y=True,
                )
                dpg.add_child_window(
                    tag="Right Window",
                    horizontal_scrollbar=True,
                    autosize_y=True,
                )
        self.redraw_games_table()
        self.redraw_participants_list()
        self.redraw_history_view()
        dpg.set_primary_window("Main Window", True)

    def redraw_history_view(self):
        dpg.delete_item("History View")
        with dpg.group(tag="History View", parent="Right Window"):
            groups = utils.group_by_set([slg for slg in self.slg if slg.is_annotated])
            for uuid in groups:
                with dpg.child_window(border=True, height=200):
                    dpg.add_text(
                        f"Set: {uuid}", color=utils.convert_uuid_to_rgb(uuid), indent=1
                    )
                    for idx, game in enumerate(groups[uuid]):
                        dpg.add_text(f"Game {idx+1} on {game.stage}.")
                        if game_details := utils.format_port_display(game):
                            dpg.add_text(game_details, bullet=True)

    def redraw_participants_list(self):
        dpg.delete_item("Participants List")
        with dpg.child_window(
            border=True, height=500, parent="Right Window", tag="Participants List"
        ):
            dpg.add_text("Participants List")
            for participant in self.participants:
                dpg.add_text(participant, bullet=True)

    def redraw_games_table(self):
        """Generate the game index table from a metadata file"""
        dpg.delete_item("Games Table")
        with dpg.table(
            header_row=True,
            policy=dpg.mvTable_SizingFixedFit,
            borders_outerH=True,
            borders_innerV=True,
            borders_innerH=True,
            borders_outerV=True,
            tag="Games Table",
            parent="Left Window",
        ):
            dpg.add_table_column(label="Group")
            dpg.add_table_column(label="Stage")
            dpg.add_table_column(label="P1")
            dpg.add_table_column(label="P2")
            dpg.add_table_column(label="P3")
            dpg.add_table_column(label="P4")
            dpg.add_table_column(label="Date")
            metadata = json.load(open(self.metadata_path, "r"))
            self.slg: List[SlippiLabelerGame] = []
            for m in metadata:
                self.draw_game_row(m)

    def highlight_rows(self):
        """Highlight any rows that are annotated"""
        for s in self.slg:
            if s.is_annotated:
                dpg.highlight_table_row(
                    "Games Table", s.table_row, utils.convert_uuid_to_rgb(s.group_id)
                )

    def handle_checkbox(self, sender):
        """Handle when the game index checkbox is clicked"""
        slg = next(filter(lambda x: x.checkbox_id == sender, self.slg), None)
        assert slg is not NotImplemented
        slg.is_selected = True

    def draw_game_row(self, metadata):
        """Draw a single row from the metadata file"""
        with dpg.table_row(tag=f"table-row-{metadata['path']}"):
            with dpg.table_cell():
                checkbox = dpg.add_checkbox(
                    label=f"##checkbox-{metadata['path']}",
                    callback=self.handle_checkbox,
                )
                self.slg.append(
                    SlippiLabelerGame(
                        len(self.slg),
                        checkbox,
                        f"{metadata['path']}",
                        metadata["stage"],
                        metadata["characters"],
                        [None] * 4,
                    )
                )
            with dpg.table_cell():
                dpg.add_text(metadata["stage"])
            for character in metadata["characters"]:
                with dpg.table_cell():
                    if not character:
                        dpg.add_text("-")
                    else:
                        dpg.add_text(character)
            with dpg.table_cell():
                dpg.add_text(utils.format_date(metadata["date"]))

    def todo():
        print(f"To Be Made")

    def start_watcher(self, preprocess=False):
        """Start a watchdog background process that observes a directory for slippi deleted and added,

        Args:
            preprocess (bool, optional): Preprocess all the files in the slippi directory,
            write the changes to the metadata_path. Defaults to False.
        """
        w = MyWatcher(self.metadata_path, self.todo)
        if preprocess:
            MyWatcher.preprocess_games(
                self.slippi_dir, self.metadata_path, self.update_progress_bar
            )
            self.display_annotation_view()
        x = threading.Thread(target=w.run, args=(self.slippi_dir,), daemon=True)
        x.start()

    def update_progress_bar(self, progress: float):
        """Callback to update the progress bar in the Loading view

        Args:
            progress (float): A value from 0 to 1 representing the progress in preprocessing slippi files
        """
        dpg.set_value("Progress Bar", progress)

    def handle_submit_annotations(
        self, _sender, _app_data, slgs: List[SlippiLabelerGame]
    ):
        """Update the gamer tags of the completed annotation form
        Highlight the rows of annotated games and reset the checkboxes

        Args:
            slgs (List[SlippiLabelerGame]): List of games that have been annotated
        """
        del _sender, _app_data
        uuid = utils.generate_uuid()
        for slg in slgs:
            slg.group_id = uuid
            slg.is_annotated = True
            slg.gamer_tags = [None] * 4
            for port, character in enumerate(slg.characters):
                if character:
                    slg.gamer_tags[port] = dpg.get_value(
                        self.generate_input_tag(slg.game_path, port)
                    )
        self.highlight_rows()
        dpg.delete_item("Annotations Window")
        self.reset_checkboxes()
        self.redraw_history_view()
        self.redraw_participants_list()

    def reset_checkboxes(self):
        """Reset all the checkboxes in the UI"""
        for slg in self.slg:
            dpg.set_value(slg.checkbox_id, False)
            slg.is_selected = False

    def launch_annotation_dialog(self):
        """Display the annotations dialog for the selected games"""
        dpg.delete_item("Annotations Window")
        with dpg.window(
            label="Annotations",
            tag="Annotations Window",
            width=gbv.annotations_window_width,
            height=gbv.annotations_window_height,
            modal=True,
        ):
            with dpg.table(
                header_row=True,
                resizable=True,
                policy=dpg.mvTable_SizingStretchSame,
                borders_outerH=True,
                borders_innerV=True,
                borders_innerH=True,
                borders_outerV=True,
                tag="Annotations Table",
            ):
                dpg.add_table_column(label="Stage")
                dpg.add_table_column(label="P1")
                dpg.add_table_column(label="P2")
                dpg.add_table_column(label="P3")
                dpg.add_table_column(label="P4")
                selected_items = [s for s in self.slg if s.is_selected]
                for item in selected_items:
                    if item.is_selected:
                        with dpg.table_row():
                            with dpg.table_cell():
                                dpg.add_text(item.stage)
                            for port, char in enumerate(item.characters):
                                with dpg.table_cell():
                                    if not char:
                                        dpg.add_text("-")
                                    else:
                                        input_tag = self.generate_input_tag(
                                            item.game_path, port
                                        )
                                        dpg.add_text(char)
                                        dpg.add_input_text(
                                            label="##Participant", tag=input_tag
                                        )
                                        dpg.add_combo(
                                            items=self.participants, source=input_tag
                                        )
            dpg.add_button(
                label="Submit",
                callback=self.handle_submit_annotations,
                user_data=selected_items,
                height=gbv.large_button_height,
                width=gbv.large_button_width,
            )

    def generate_input_tag(self, game_path: str, port: int) -> str:
        """Generate a unique input tag for a game and a port number

        Args:
            game_path (str): Path of the slippi file
            port (int): Port Number

        Returns:
            str: unique input tag
        """
        return f"{game_path}//{port}"

    def export_annotations(self):
        """Export the annotations to the user defined annotations file"""
        with open(self.annotations_path, "w+") as f:
            json.dump(
                utils.group_by_set(self.slg),
                f,
                cls=utils.DataClassJSONEncoder,
                indent=4,
            )


if __name__ == "__main__":
    s = SlippiLabeler()
    s.run()

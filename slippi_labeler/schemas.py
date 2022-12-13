from dataclasses import dataclass
from typing import Union
import uuid

@dataclass
class SlippiLabelerGame:
    """Representation of a game in the UI"""

    table_row: int
    checkbox_id: int
    game_path: str
    stage: str
    characters: list
    gamer_tags: str
    is_annotated: bool = False
    is_selected: bool = False
    group_id: Union[uuid.UUID, None] = None


class GlobalViewUI:
    text_color = (255,255,255)
    warning_text_color = (255, 165, 0)
    success_text_color = (0, 255, 0)
    failure_text_color = (255, 0, 0)
    info_text_color = (170, 255, 170)
    window_width = 1000
    window_height = 800
    file_selector_width = 500
    file_selector_height = 800
    small_button_height = 100
    small_button_width = 100
    medium_button_height = 100
    medium_button_width = 200
    large_button_height = 300
    large_button_width = 300
    
    annotations_window_width = 1000
    annotations_window_height = 800
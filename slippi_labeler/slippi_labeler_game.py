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

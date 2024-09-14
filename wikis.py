import json
import rich

from pydantic import BaseModel, Field
from enum import Enum
import dataclasses


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    not_given = "not_given"


class Alias(BaseModel):
    name: str
    alias_summary: str = Field(
        description="Markdown Formatted: A short summary on the Alias"
    )


class Character(BaseModel):
    name: str = Field(description="Name")
    gender: Gender = Field(default=Gender.not_given, description="Gender")
    overview: str = Field(default="", description="A short summary")
    appearance: str = Field(
        default="",
        description=(
            "Markdown Formatted: This section contains information about"
            " all the different visual appearances of the character in the story,"
            " describe the looks of the character."
        ),
    )
    personality: str = Field(
        default="",
        description=(
            "Markdown Formatted: This section contains information about"
            " the personality of the character and how it changes throughout"
            " the story"
        ),
    )
    aliases: list[Alias] = Field(
        default=[],
        description=(
            "A list of all known aliases of the character,"
            " and a short summary on each alias."
        ),
    )
    trivia: list[str] = Field(
        default=[],
        description=("A list of various interesting trivia related to the character."),
    )
    current_state: str = Field(
        default="",
        description=("A short sentence describing the current state of the character"),
    )

    add_to_appearance: list[str] = []
    add_to_personality: list[str] = []
    add_to_aliases: list[Alias] = []
    add_to_trivia: list[str] = []


class Setting(BaseModel):
    name: str = Field(description="Name")
    overview: str = Field(default="", description="A short summary")
    appearance: str = Field(
        default="",
        description=(
            "Markdown Formatted: This section contains information about"
            " all the different visual appearances of the setting in the story,"
            " how it evolved."
        ),
    )
    aliases: list[Alias] = Field(
        default=[],
        description=(
            "A list of all known aliases of the setting,"
            " and a short summary on each alias."
        ),
    )
    characters_involved: list[Character] = Field(
        default=[],
        description=("A list of all characters who appeared at the setting."),
    )
    current_state: str = Field(
        default="",
        description=("A short sentence describing the current state of the setting"),
    )
    trivia: list[str] = Field(
        default=[],
        description=("A list of various interesting trivia related to the setting."),
    )

    add_to_appearance: list[str] = []
    add_to_aliases: list[Alias] = []
    add_to_characters_involved: list[Character] = []
    add_to_trivia: list[str] = []


@dataclasses.dataclass
class Wiki:
    name: str

    def __post_init__(self):

        self.characters: dict[str, Character] = {}
        self.settings: dict[str, Setting] = {}
        self.functions = {
            "create_new_character": self.add_character,
            "create_new_setting": self.add_setting,
            "add_character_appearance": self.add_character_appearance,
            "add_setting_appearance": self.add_setting_appearance,
            "add_character_trivia": self.add_character_trivia,
            "add_setting_trivia": self.add_setting_trivia,
            "update_character_current_state": self.update_character_current_state,
            "add_alias_to_character": self.add_alias_to_character,
            "do nothing": self.do_nothing,
        }

    def add_character(self, name: str):
        """Call this function with every character mentioned in current chunk.
        Some characters might not have named but might be called with their aliases like thier social standing or thier titles. Call this function with those aliases instead.

        Args:
            name (str): The name or any alias of the character.
        """
        character_exists = False
        for character in self.characters.values():
            aliases = [a.name for a in character.aliases]
            if name == character.name or name in aliases:
                print(f"Character {character.name} already exists")
                character_exists = True
        if not character_exists:
            self.characters[name] = Character(name=name)
            rich.print(f"Added Character {name}")

    def add_setting(self, name: str):
        """Call this function with every setting in current chunk. A setting is
        any location characters find themselves in.

        Args:
            name (str): The name of the setting.
        """
        setting_exists = False
        for setting in self.settings.values():
            aliases = [a.name for a in setting.aliases]
            if name == setting.name or name in aliases:
                print(f"Setting {setting.name} already exists")
                setting_exists = True
        if not setting_exists:
            self.settings[name] = Setting(name=name)
            rich.print(f"Added Setting {name}")

    def add_character_appearance(self, character_name: str, new_appearance: str):
        """Create a new character in the wiki database.

        Args:
            character_name (str)
            new_appearance (str): The appearance of the character
        """
        character = self.characters[character_name]
        character.add_to_appearance.append(new_appearance)

    def add_setting_appearance(self, setting_name: str, new_appearance: str):
        """Create a new character in the wiki database.

        Args:
            character_name (str)
            new_appearance (str): The appearance of the character
        """
        setting = self.settings[setting_name]
        setting.add_to_appearance.append(new_appearance)

    def add_character_trivia(self, character_name: str, new_trivia: str):
        """Create a new character in the wiki database.

        Args:
            character_name (str)
            new_appearance (str): The appearance of the character
        """
        character = self.characters[character_name]
        character.add_to_trivia.append(new_trivia)

    def add_setting_trivia(self, setting_name: str, new_trivia: str):
        """Create a new character in the wiki database.

        Args:
            character_name (str)
            new_appearance (str): The appearance of the character
        """
        setting = self.settings[setting_name]
        setting.add_to_trivia.append(new_trivia)

    def update_character_current_state(self, character_name: str, new_state: str):
        """Create a new character in the wiki database.

        Args:
            character_name (str)
            new_state (str): A short sentence describing the current state of the character
        """
        character = self.characters[character_name]
        character.current_state = new_state

    def add_alias_to_character(self, name: str, alias: Alias):
        """If any character is mentioned with an alias, use this function to add the alias to the character's information.

        Args:
            name (str): The name of the character.
            alias (str): The alias of said character.
        """

        alias_is_an_existing_character = False

        for character in self.characters.values():
            aliases = [a.name for a in character.aliases]
            if alias == character.name or name in aliases:
                print(f"Character {character.name} already exists")
                alias_is_an_existing_character = True
                break

        if alias_is_an_existing_character:
            # TODO: add all data from alias_characters attributes to the
            # named_character attributes, and delete the alias_character.

            # named_character = self.characters[name]
            # alias_character = character
            pass

        named_character = self.characters[name]
        named_character.add_to_aliases.append(alias)
        rich.print(f"Added alias: {alias.name} to Character {named_character.name}")

    def do_nothing(self):
        """If the current chunk contains no relavant information,  use this function."""
        pass


if __name__ == "__main__":

    import dotenv
    import os

    dotenv.load_dotenv()

    import google.generativeai as genai
    from db import DocStore
    import prompt_templates

    docstore = DocStore(
        "./input_docs",
        chunk_size=1024,
        chunk_overlap=0,
    )

    GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)

    wiki = Wiki("LotmWiki")

    prev_chunks = [node.text for node in docstore.nodes[5:6]]
    curr_chunk = docstore.nodes[6].text

    prev_chunks = prompt_templates.apply_prev_chunks_template(prev_chunks)

    user_msg = prompt_templates.DEFAULT_PROMPT_TEMPLATE.format(
        prev_chunks=prev_chunks,
        curr_chunk=curr_chunk,
    )
    rich.print(user_msg)

    model = genai.GenerativeModel(
        "models/gemini-1.5-flash",
        tools=wiki.functions.values(),
        system_instruction=prompt_templates.DEFAULT_SYSTEM_MSG,
    )

    response = model.generate_content(user_msg)
    rich.print(response)

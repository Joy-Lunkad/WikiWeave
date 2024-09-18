import json
import rich

from pydantic import BaseModel, Field
import dataclasses
from abc import ABC, abstractmethod

from typing import Any, Callable, Type

import google.generativeai as genai
import prompt_templates
import wiki
from section_examples import characters


class Description(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Detailed description of the setting."

    @classmethod
    def name(cls):
        return "description"

    def add_to_buffer(self, content: str):
        super().add_to_buffer(content=content)

    def update_data(
        self,
        model: genai.GenerativeModel,
        section_name: str,
        section_entity_name: str,
        **kwargs,
    ):
        update_prompt = (
            "Provide a comprehensive and detailed description of the setting."
            " Include significant features, landmarks, climate, and general atmosphere."
            " Use the new data provided to enrich the existing description."
        )

        prompt = prompt_templates.UPDATE_FUNCTION_PROMPT_TEMPLATE.format(
            section_name=section_name,
            section_entity_name=section_entity_name,
            attribute_name=self.name,
            attribute_description=self.description,
            update_prompt=update_prompt,
            existing_data=self.data,
            new_data="\n".join(self.buffer),
        )

        return super().update_data(
            prompt=prompt,
            model=model,
            **kwargs,
        )

    def to_markdown(self) -> str:
        return self.data

    def from_markdown(self, content: str):
        self.data = content.strip()


class CharactersInvolved(wiki.Attribute):

    @classmethod
    def description(cls):
        return "A list of all known characters who have appeared at the Setting."

    @classmethod
    def name(cls):
        return "characters_involved"

    def add_to_buffer(self, character_name: str):
        super().add_to_buffer(content=character_name)

    def update_data(self, characters_section: characters.Characters, **kwargs) -> None:
        aliases = []
        for character_name in self.buffer:
            character = characters_section.entities.get(character_name)
            if character is not None:
                aliases_attr: characters.Aliases = character.attributes["aliases"]  # type: ignore
                aliases = aliases_attr.data
                
            if character_name not in self.data and all(
                a not in self.data for a in aliases
            ):
                self.data.append(character_name)
        super().update_data()

    def to_markdown(self) -> str:
        return "\n".join(f"- {item}" for item in self.data)

    def from_markdown(self, content: str):
        lines = content.strip().splitlines()
        self.data = [
            line.lstrip("- ").strip() for line in lines if line.startswith("- ")
        ]


class Trivia(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Various interesting trivia related to the setting."

    @classmethod
    def name(cls):
        return "trivia"

    def add_to_buffer(self, content: str):
        super().add_to_buffer(content=content)

    def update_data(
        self,
        model: genai.GenerativeModel,
        section_name: str,
        section_entity_name: str,
        **kwargs,
    ):
        update_prompt = (
            "This should be a list of the setting's various trivia."
            " Try to make this list as interesting as possible."
        )

        prompt = prompt_templates.UPDATE_FUNCTION_PROMPT_TEMPLATE.format(
            section_name=section_name,
            section_entity_name=section_entity_name,
            attribute_name=self.name,
            attribute_description=self.description,
            update_prompt=update_prompt,
            existing_data=self.data,
            new_data="\n".join(self.buffer),
        )

        return super().update_data(
            prompt=prompt,
            model=model,
            **kwargs,
        )

    def to_markdown(self) -> str:
        return self.data

    def from_markdown(self, content: str):
        self.data = content.strip()


@dataclasses.dataclass
class SettingAttributes(wiki.EntityAttributes):

    description = Description(
        name=Description.name(),
        type=str,
        default="",
        description=Description.description(),
        update_every_n_insertions=3,
    )

    characters_involved = CharactersInvolved(
        name=CharactersInvolved.name(),
        type=list[str],
        description=CharactersInvolved.description(),
        update_every_n_insertions=1,
        default=[],
    )

    trivia = Trivia(
        name=Trivia.name(),
        type=str,
        description=Trivia.description(),
        update_every_n_insertions=3,
        default="",
    )

    def get_attributes(self) -> dict[str, wiki.Attribute]:
        return dict(
            description=self.description,
            characters_involved=self.characters_involved,
            trivia=self.trivia,
        )


class Setting(wiki.SectionEntity):
    name: str
    attributes: dict[str, wiki.Attribute] = SettingAttributes().get_attributes()


class Settings(wiki.Section):

    name: str
    entities: dict[str, Setting] = {}

    def add_setting(self, name: str):
        """Call this function with every setting mentioned in the current chunk.
        Settings are places or locations within the narrative. 
        Call this function every time a setting's name is mentioned.
        Deduplication is handled by the function. Remember, objects present
        aren't their own setting but should be a part of a setting's `description`.
        For example: A setting 'Study' can have pen, table, etc in its `description`.

        Args:
            name (str): The name of the setting.
        """
        if name not in self.entities:
            self.entities[name] = Setting(name=name)
            rich.print(f"Added Setting {name}")

    def add_to_setting_description(self, name: str, content: str):
        """Call this function to add relevant content that can help understand the
        setting's description. This content will be used to build a comprehensive
        and detailed description of the setting. Information extracted from 
        the current chunk should be rephrased concisely before being
        passed to this function.

        This function adds the `content` to the named setting's `description` in
        the wiki. Call this function if any relevant content is mentioned.
        Deduplication is handled by the function.

        Args:
            name (str): Name of the setting.
            content (str): The content to be added.
        """
        setting = self.entities.get(name)
        if not setting:
            raise ValueError(f"Setting {name} does not exist.")
        description: Description = setting.attributes["description"]  # type: ignore
        description.add_to_buffer(content=content)
        rich.print(f"To {name}'s description added -> {content}")

    def add_to_characters_involved_with_setting(self, name: str, character_name: str):
        """
        Call this function with every character at the named setting in current chunk.
        Some characters might not have named but might be called with their aliases
        like thier social standing or thier titles. Call this function with those
        aliases instead. Call this function every time a character is mentioned
        to be present at a setting. Deduplication is handled by the function.

        Args:
            name (str): Name of the setting.
            character_name (str): The character's name or alias who is present
                at the setting or is mentioned to have been to the setting
                at any time in the past.
        """
        setting = self.entities.get(name)
        if not setting:
            raise ValueError(f"Setting {name} does not exist.")
        char_involved: CharactersInvolved = setting.attributes["characters_involved"]  # type: ignore
        char_involved.add_to_buffer(character_name=character_name)
        rich.print(f"To {name}'s characters involved added -> {character_name}")

    def add_to_setting_trivia(
        self,
        name: str,
        content: str,
    ):
        """Call this function to add any interesting trivia about the setting
        to the wiki. Information extracted from the current chunk should be
        rephrased concisely before being passed to this function.
        Call this function every time any relavent content is mentioned.
        Deduplication is handled by the function.

        Args:
            name (str): Name of the setting
            content (str): The content to be added.
        """
        setting = self.entities.get(name)
        if not setting:
            raise ValueError(f"Setting {name} does not exist.")

        trivia: Trivia = setting.attributes["trivia"]  # type: ignore
        trivia.add_to_buffer(content=content)
        rich.print(f"To {name}'s trivia added -> {content}")

    @property
    def section_functions(self) -> dict[str, Callable]:
        return {
            "add_setting": self.add_setting,
            "add_to_setting_description": self.add_to_setting_description,
            "add_to_characters_involved_with_setting": self.add_to_characters_involved_with_setting,
            "add_to_setting_trivia": self.add_to_setting_trivia,
        }

import json
import rich

from pydantic import BaseModel, Field
import dataclasses
from abc import ABC, abstractmethod

from enum import Enum
from typing import Any, Callable, Literal, Type


import google.generativeai as genai
import prompt_templates
import wiki


class Personality(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Analysis of the character's personality"

    @classmethod
    def name(cls):
        return "personality"

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
            "This should be a small essay of the character's personality."
            " Analyze the character's personality from a psychological"
            " and sociological perspective using the information from"
            " new data and the previous analysis stored as existing data."
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


class Aliases(wiki.Attribute):

    @classmethod
    def description(cls):
        return "A list of all known aliases of the character."

    @classmethod
    def name(cls):
        return "aliases"

    def add_to_buffer(self, alias: str):
        super().add_to_buffer(content=alias)

    def update_data(self, **kwargs) -> None:

        for alias in self.buffer:
            if alias not in self.data:
                self.data.append(alias)  # type: ignore
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
        return (
            "Markdown Formatted: Various interesting trivia related to the character."
        )

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
            "This should be a list of the character's various trivia."
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


class Appearance(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Detailed physical description of the character's appearance."

    @classmethod
    def name(cls):
        return "appearance"

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
            "Provide a detailed physical description of the character's appearance."
            "Use the new data provided to enrich the existing description."
            "Keep track of how the character's appearance chances throughout the story."
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
class CharacterAttributes(wiki.EntityAttributes):

    personality = Personality(
        name=Personality.name(),
        type=str,
        default="",
        description=Personality.description(),
        update_every_n_insertions=3,
    )

    aliases = Aliases(
        name=Aliases.name(),
        type=list[str],
        description=Aliases.description(),
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

    appearance = Appearance(
        name=Appearance.name(),
        type=str,
        description=Appearance.description(),
        update_every_n_insertions=2,
        default="",
    )

    def get_attributes(self) -> dict[str, wiki.Attribute]:
        return dict(
            personality=self.personality,
            trivia=self.trivia,
            aliases=self.aliases,
            appearance=self.appearance,
        )


class Character(wiki.SectionEntity):
    name: str
    attributes: dict[str, wiki.Attribute] = CharacterAttributes().get_attributes()


class Characters(wiki.Section):

    name: str
    entities: dict[str, Character] = {}

    def add_character(self, name: str):
        """Call this function with every character mentioned in current chunk.
        Some characters might not have named but might be called with their aliases
        like thier social standing or thier titles. Call this function with those
        aliases instead. Call this function every time a character's name or alias
        is mentioned. Deduplication is handled by the function.

        Args:
            name (str): The Full name or any alias of the character.
        """

        if name not in self.entities:
            self.entities[name] = Character(name=name)
            rich.print(f"Added Character {name}")

    def add_to_character_personality(
        self,
        name: str,
        content: str,
    ):
        """Call this function to add relevant content that can help understand the
        character's personality. This content will be used to deeply analyze the
        character's personality from a psychological and sociological prespective.

        This function adds the `content` to the named character's `personality` in
        the wiki. Call this function if any relavent content is mentioned. Deduplication is handled by the function.

        Args:
            name (str): Name of the character
            content (str): The content to be added.
        """
        character = self.entities.get(name)
        if not character:
            raise ValueError(f"Character {name} does not exist.")

        personality: Personality = character.attributes["personality"]  # type: ignore
        personality.add_to_buffer(content=content)

    def add_to_character_trivia(
        self,
        name: str,
        content: str,
    ):
        """Call this function to add any interesting trivia about the character to the wiki. Information extracted from the current chunk should be
        rephrased concisely before being passed to this function.
        Call this function every time any relavent content is mentioned.
        Deduplication is handled by the function.

        Args:
            name (str): Name of the character
            content (str): The content to be added.
        """
        character = self.entities.get(name)
        if not character:
            raise ValueError(f"Character {name} does not exist.")

        trivia: Trivia = character.attributes["trivia"]  # type: ignore
        trivia.add_to_buffer(content=content)

    def add_to_character_aliases(
        self,
        name: str,
        alias: str,
    ):
        """If any character is mentioned with an alias in the current chunk, call
        this function to add the alias to the character's information in the wiki.
        The character's full name is also an alias. Some character's also have a
        `honorific name` consisting of 3-4 lines. This should also be added to
        their aliases. Call this function every time a character's name or alias
        is mentioned. Deduplication is handled by the function.

        Args:
            name (str): Name of the character
            alias (str): An alias of the character.
        """
        character = self.entities.get(name)
        if not character:
            raise ValueError(f"Character {name} does not exist.")

        aliases: Aliases = character.attributes["aliases"]  # type: ignore
        aliases.add_to_buffer(alias=alias)

        if alias not in self.entities:
            self.entities[alias] = character
            # TODO: Merge Aliases function.

    def add_to_character_appearance(
        self,
        name: str,
        content: str,
    ):
        """If the appearance of any character is mentioned in the current chunk, 
        call this function to add the content related to the character's
        appearance to the wiki. This content will be used to build a detailed description of the character's looks. 
        Call this function whenever any content about the character's
        appearance is mentioned. Deduplication is handled by the function.

        Args:
            name (str): Name of the character.
            content (str): The content to be added.
        """
        character = self.entities.get(name)
        if not character:
            raise ValueError(f"Character {name} does not exist.")

        appearance: Appearance = character.attributes["appearance"]  # type: ignore
        appearance.add_to_buffer(content=content)

    @property
    def section_functions(self) -> dict[str, Callable]:
        return {
            "add_character": self.add_character,
            "add_to_character_personality": self.add_to_character_personality,
            "add_to_character_aliases": self.add_to_character_aliases,
            "add_to_character_appearance": self.add_to_character_appearance,
            "add_to_character_trivia": self.add_to_character_trivia,
        }
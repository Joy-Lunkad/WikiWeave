import json
import rich

from pydantic import BaseModel, Field
import dataclasses
from abc import ABC, abstractmethod

from typing import Any, Callable, Type

import google.generativeai as genai
import prompt_templates
import wiki


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


class Geography(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Geographical features of the setting."

    @classmethod
    def name(cls):
        return "geography"

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
            "Provide detailed information on the geographical features of the setting, "
            "including terrain, climate, natural resources, and significant landmarks."
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


class History(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Historical background of the setting."

    @classmethod
    def name(cls):
        return "history"

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
            "Provide a detailed historical background of the setting, "
            "including major events, changes over time, and influential figures."
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


class Culture(wiki.Attribute):

    @classmethod
    def description(cls):
        return "Markdown Formatted: Cultural aspects of the setting."

    @classmethod
    def name(cls):
        return "culture"

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
            "Provide detailed information on the cultural aspects of the setting, "
            "including traditions, customs, social norms, and other relevant details."
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

    history = History(
        name=History.name(),
        type=str,
        description=History.description(),
        update_every_n_insertions=1,
        default="",
    )

    geography = Geography(
        name=Geography.name(),
        type=str,
        description=Geography.description(),
        update_every_n_insertions=1,
        default="",
    )

    culture = Culture(
        name=Culture.name(),
        type=str,
        description=Culture.description(),
        update_every_n_insertions=1,
        default="",
    )

    def get_attributes(self) -> dict[str, wiki.Attribute]:
        return dict(
            description=self.description,
            history=self.history,
            geography=self.geography,
            culture=self.culture,
        )


class Setting(wiki.SectionEntity):
    name: str
    attributes: dict[str, wiki.Attribute] = SettingAttributes().get_attributes()


class Settings(wiki.Section):

    name: str
    entities: dict[str, Setting] = {}

    def add_setting(self, name: str):
        """Call this function with every setting mentioned in the current chunk.
        Settings can be places, locations, or significant landmarks within the narrative.
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
        and detailed description of the setting.

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

    def add_to_setting_geography(self, name: str, content: str):
        """Call this function to add information about the geographical features
        of the setting. This content will be used to describe the terrain, climate,
        natural resources, and significant landmarks of the setting.

        This function adds the `content` to the named setting's `geography` in
        the wiki. Call this function if any relevant content is mentioned.
        Deduplication is handled by the function.

        Args:
            name (str): Name of the setting.
            content (str): The content to be added.
        """
        setting = self.entities.get(name)
        if not setting:
            raise ValueError(f"Setting {name} does not exist.")
        geography: Geography = setting.attributes["geography"]  # type: ignore
        geography.add_to_buffer(content=content)

    def add_to_setting_history(self, name: str, content: str):
        """Call this function to add historical background information about the setting.
        This content will be used to build a detailed history of the setting, including
        major events, changes over time, and influential figures.

        This function adds the `content` to the named setting's `history` in
        the wiki. Call this function if any relevant content is mentioned.
        Deduplication is handled by the function.

        Args:
            name (str): Name of the setting.
            content (str): The content to be added.
        """
        setting = self.entities.get(name)
        if not setting:
            raise ValueError(f"Setting {name} does not exist.")
        history: History = setting.attributes["history"]  # type: ignore
        history.add_to_buffer(content=content)

    def add_to_setting_culture(self, name: str, content: str):
        """Call this function to add information about the cultural aspects of the setting.
        This content will be used to describe the traditions, customs, social norms,
        and other relevant cultural details.

        This function adds the `content` to the named setting's `culture` in
        the wiki. Call this function if any relevant content is mentioned.
        Deduplication is handled by the function.

        Args:
            name (str): Name of the setting.
            content (str): The content to be added.
        """
        setting = self.entities.get(name)
        if not setting:
            raise ValueError(f"Setting {name} does not exist.")
        culture: Culture = setting.attributes["culture"]  # type: ignore
        culture.add_to_buffer(content=content)

    @property
    def section_functions(self) -> dict[str, Callable]:
        return {
            "add_setting": self.add_setting,
            "add_to_setting_description": self.add_to_setting_description,
            "add_to_setting_geography": self.add_to_setting_geography,
            "add_to_setting_history": self.add_to_setting_history,
            "add_to_setting_culture": self.add_to_setting_culture,
        }

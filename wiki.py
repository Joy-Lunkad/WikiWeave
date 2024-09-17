import json
import rich
import os
from pydantic import BaseModel, Field
import dataclasses
from abc import ABC, abstractmethod
import db
from enum import Enum
from typing import Any, Callable, Optional, Type, Generic, TypeVar
import google.generativeai as genai
from google.generativeai.types.generation_types import GenerateContentResponse

T = TypeVar("T")


@dataclasses.dataclass
class Attribute(ABC, Generic[T]):
    name: str
    type: Type[T]
    description: str
    update_every_n_insertions: int
    default: T

    def __post_init__(self):
        self.buffer: list = []
        self.data = self.default

    def add_to_buffer(self, content) -> Any:
        """Method for adding information to the attribute's buffer"""
        self.buffer.append(content)

    def update_data(
        self,
        prompt: str | None = None,
        model: None | genai.GenerativeModel = None,
        **kwargs,
    ) -> Any:
        """Method for updating `attribute.data` from data in `attribute.buffer`"""

        if model is not None and prompt is not None:
            response = model.generate_content(prompt)
            rich.print(response)
            self.data = response.text

        self.buffer = []
        rich.print(f"New data -> {self.data}")

    @abstractmethod
    def to_markdown(self) -> str:
        """Convert the attribute data to a markdown string."""

    @abstractmethod
    def from_markdown(self, content: str) -> None:
        """Load the attribute data from a markdown string."""


@dataclasses.dataclass
class EntityAttributes(ABC):
    """Abstract dataclass that defines attributes for a SectionEntity."""

    @abstractmethod
    def get_attributes(self) -> dict[str, Attribute]:
        """Return a list of all attributes."""
        pass


class SectionEntity(ABC, BaseModel):

    name: str
    attributes: dict[str, Attribute] = {}


class Section(ABC, BaseModel):

    name: str
    entities: dict[str, SectionEntity] = {}

    @property
    @abstractmethod
    def section_functions(self) -> dict[str, Callable]:
        """This property contains a dict with all the functions/tools of a section."""


@dataclasses.dataclass
class Wiki:
    name: str
    sections: dict[str, Section]
    input_dir: str = "./input_docs"
    use_n_prev_chunks: int = 5
    which_model: str = "models/gemini-1.5-pro"

    def __post_init__(self):

        print("......  Loading Data  .....")
        self.docstore = DocStore(
            "./input_docs",
            chunk_size=2048,
            chunk_overlap=0,
        )
        self.running_summary = []

        print("....  Initializing LLM  ....")
        self.functions = {}
        for section in self.sections.values():
            self.functions.update(section.section_functions)
        self.functions["generate_chunk_summary"] = self.generate_chunk_summary

        rich.print(self.functions)

        self.add_model = genai.GenerativeModel(
            self.which_model,
            tools=self.functions.values(),  # type: ignore
            system_instruction=prompt_templates.DEFAULT_ADD_SYSTEM_MSG,
            # TODO: set generation config
        )

        self.update_model = genai.GenerativeModel(
            self.which_model,
            system_instruction=prompt_templates.DEFAULT_UPDATE_SYSTEM_MSG,
            # TODO: set generation config
        )

    def call_function(self, function_call):
        function_name = function_call.name
        function_kwargs = function_call.args

        fn = self.functions[function_name]
        return fn(**function_kwargs)

    def generate_chunk_summary(self, summary: str):
        """Generate a summary of the current chunk. Calling this function is
        complusory. This summary is used to keep track of the general plot,
        ongoing events, etc. The model will get a running summary from a
        few previous chunks to help it understand the current chunk better,
        thus aiding it to build the wiki.
        Try to keep this summary about 500 words long.
        Additionally, the summary should try to keep track of the characters present, 
        current setting, and other important details for future reference. 

        Args:
            summary (str): Markdown Formated summary of the current chunk.
        """
        self.running_summary.append(summary)
        self.running_summary = self.running_summary[-self.use_n_prev_chunks :]

    def read_chunks(self):

        for curr_node in self.docstore.nodes[3:8]:
            curr_chunk_text = curr_node.text

            prev_chunks_text = prompt_templates.apply_prev_chunks_template(
                self.running_summary
            )
            user_msg = prompt_templates.DEFAULT_PROMPT_TEMPLATE.format(
                prev_chunks=prev_chunks_text,
                curr_chunk=curr_chunk_text,
            )

            print("-" * 100)
            rich.print(user_msg)

            response = None
            tries = 0
            max_retries = 10
            while response is None and tries <= max_retries:
                try:
                    response = self.add_model.generate_content(user_msg)
                except Exception as e:
                    tries += 1
                    rich.print(f"Retrying: {tries}/{max_retries}")

            if tries > max_retries:
                raise Exception("Error calling Gemini API")        
            
            if response is not None:
                print("-" * 100)
                rich.print(response)
                self.process_response(response)
                self.update_sections()

    def process_response(self, response: GenerateContentResponse):

        for part in response.parts:
            if fn := part.function_call:
                args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
                rich.print(f"Calling {fn.name}({args})")
                try:
                    self.call_function(part.function_call)
                except Exception as e:
                    print(e)

    def update_sections(self, force=False):
        for section_name, section in self.sections.items():
            for entity_name, entity in section.entities.items():
                for attr_name, attr in entity.attributes.items():
                    update_due = attr.update_every_n_insertions <= len(attr.buffer)

                    if update_due or force:
                        rich.print(
                            f"... Updating {section_name}: {entity_name} -> {attr_name} ..."
                        )
                        rich.print(f"Old data: {attr.data}")
                        attr.update_data(
                            section_name=section_name,
                            section_entity_name=entity_name,
                            model=self.update_model,
                        )

                    else:
                        rich.print(
                            f"{section_name}: {entity_name} -> {attr_name} = buffer_size = {len(attr.buffer)}"
                        )

    def save_wiki(self, root_dir: str = "./wiki_data"):
        """Save wiki into hierarchical .md files.

        Args:
            root_dir (str, optional): Defaults to './wiki_data'.
        """
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)

        sections_dir = os.path.join(root_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)

        for section_name, section in self.sections.items():
            section_dir = os.path.join(sections_dir, section_name)
            entities_dir = os.path.join(section_dir, "entities")
            os.makedirs(entities_dir, exist_ok=True)

            for entity_name, entity in section.entities.items():
                entity_fname = sanitize_filename(entity_name)
                entity_dir = os.path.join(entities_dir, entity_fname)
                os.makedirs(entity_dir, exist_ok=True)

                attributes = entity.attributes
                for attr_name, attr in attributes.items():
                    attr_fname = sanitize_filename(attr_name)
                    attr_file = os.path.join(entity_dir, f"{attr_fname}.md")

                    data_to_save = attr.to_markdown()

                    with open(attr_file, "w", encoding="utf-8") as f:
                        f.write(data_to_save)

    def load_wiki(self, root_dir: str = "./wiki_data"):
        """Load wiki from .md files.

        Args:
            root_dir (str, optional): _description_. Defaults to './wiki_data'.
        """
        sections_dir = os.path.join(root_dir, "sections")
        if not os.path.exists(sections_dir):
            raise FileNotFoundError(f"No data found in {sections_dir}")

        self.sections = {}
        for section_name in os.listdir(sections_dir):
            section_dir = os.path.join(sections_dir, section_name)
            entities_dir = os.path.join(section_dir, "entities")

            # Instantiate the section class based on the section name
            if section_name.lower() == "characters":
                section = characters.Characters(name=section_name, entities={})
            else:
                continue  # Handle other sections as needed

            for entity_name in os.listdir(entities_dir):
                entity_dir = os.path.join(entities_dir, entity_name)

                # Instantiate the entity class
                if section_name.lower() == "characters":
                    entity = characters.Character(name=entity_name)
                else:
                    continue  # Handle other entity types as needed

                attributes = entity.attributes
                for attr_name, attr in attributes.items():
                    attr_file = os.path.join(entity_dir, f"{attr_name}.md")
                    if os.path.exists(attr_file):
                        with open(attr_file, "r", encoding="utf-8") as f:
                            content = f.read()
                            attr.from_markdown(content)
                    else:
                        attr.data = attr.default  # Handle missing files

                section.entities[entity_name] = entity

            self.sections[section_name] = section


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    import re

    return re.sub(r"[^a-zA-Z0-9_\- ]", "", name).strip().replace(" ", "_")


if __name__ == "__main__":

    import dotenv
    import os

    dotenv.load_dotenv()

    import google.generativeai as genai
    from db import DocStore
    import prompt_templates
    from section_examples import characters, settings

    GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)

    wiki = Wiki(
        name="LotmWiki",
        sections={
            "Characters": characters.Characters(
                name="characters",
                entities={},
            ),
            "Settings": settings.Settings(
                name="settings",
                entities={},
            ),
        },
    )

    wiki.read_chunks()
    wiki.update_sections(force=False)
    wiki.save_wiki()

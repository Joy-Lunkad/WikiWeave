import time
import dotenv
import os

dotenv.load_dotenv()

import numpy as np
from tqdm import tqdm


from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.storage.index_store.types import DEFAULT_PERSIST_DIR

from dataclasses import dataclass
import rich


@dataclass
class DocStore:
    data_dir: str
    chunk_size: int
    chunk_overlap: int

    def __post_init__(self):
        documents = SimpleDirectoryReader(self.data_dir).load_data()
        parser = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        self.nodes: list[TextNode] = parser.get_nodes_from_documents(documents)  # type:ignore


def load_test(chunk_size=1024, chunk_overlap=0):
    docstore = DocStore(
        "./input_docs",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return docstore

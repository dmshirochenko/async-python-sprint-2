import os
import shutil
import requests
import logging.config
from functools import wraps
from html.parser import HTMLParser
from typing import Generator, Any, Callable

from config.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


def coroutine(f: Callable) -> Callable:
    @wraps(f)
    def wrap(*args: Any, **kwargs: Any) -> Generator:
        gen = f(*args, **kwargs)
        next(gen)  # start the generator
        return gen

    return wrap


def func_resolver(func_name: str) -> Any:
    operations_mapping = {
        "create_directory": FileSystemOperations.create_directory,
        "delete_directory": FileSystemOperations.delete_directory,
        "create_file": FileSystemOperations.create_file,
        "delete_file": FileSystemOperations.delete_file,
        "write_to_file": FileOperations.write_to_file,
        "read_from_file": FileOperations.read_from_file,
        "html_to_txt_pipeline": NetworkOperationsPipe.html_to_txt_pipeline,
        "write_to_file_pipeline": NetworkOperationsPipe.write_to_file,
        "clean_html_chunks": NetworkOperationsPipe.clean_html_chunks,
    }
    return operations_mapping.get(func_name)


class FileSystemOperations:
    @staticmethod
    @coroutine
    def create_directory(path: str) -> Generator:
        try:
            os.makedirs(path)
            yield f"Directory created at {path}"
        except FileExistsError:
            yield f"Directory exists at {path}"

    @staticmethod
    @coroutine
    def delete_directory(path: str) -> Generator:
        try:
            shutil.rmtree(path)
            yield f"Directory deleted at {path}"
        except FileNotFoundError:
            yield "Directory not found"

    @staticmethod
    @coroutine
    def create_file(path: str) -> Generator:
        try:
            with open(path, "w") as file:
                file.write("")
            yield f"File created at {path}"
        except Exception as e:
            yield f"Error creating file at {path}: {e}"

    @staticmethod
    @coroutine
    def delete_file(path: str) -> Generator:
        try:
            os.remove(path)
            yield f"File deleted at {path}"
        except FileNotFoundError:
            yield "File not found"


class FileOperations:
    @staticmethod
    @coroutine
    def write_to_file(path: str, content: str) -> Generator:
        try:
            with open(path, "w") as file:
                file.write(content)
            yield f"Content written to {path}"
        except IOError as e:
            logger.error("IOError while writing to file %s: %s", path, e)
            raise e

    @staticmethod
    @coroutine
    def read_from_file(path: str) -> Generator:
        try:
            with open(path, "r") as file:
                for line in file:
                    yield line
        except FileNotFoundError:
            yield "File not found"


class ChunkHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_data = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignore_data = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignore_data = False

    def handle_data(self, data):
        if not self.ignore_data:
            self.text_parts.append(data)

    def handle_entityref(self, name):
        self.text_parts.append(self.unescape("&" + name + ";"))

    def handle_charref(self, name):
        self.text_parts.append(self.unescape("&#" + name + ";"))

    def get_data(self):
        return " ".join(part.strip() for part in self.text_parts if part.strip())


class NetworkOperationsPipe:
    @staticmethod
    @coroutine
    def html_to_txt_pipeline(url: str, path: str) -> Generator:
        output = NetworkOperationsPipe().clean_html_chunks()
        output.send(path)
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    yield output.send(chunk.decode("utf-8"))
        except requests.exceptions.RequestException as e:
            logger.error("RequestException while fetching %s: %s", url, e)
            raise e

    @staticmethod
    @coroutine
    def write_to_file() -> Generator:
        path = yield
        try:
            with open(path, "w") as file:
                while True:
                    chunk = yield
                    file.write(chunk)
                    file.flush()
        except IOError as e:
            logger.error("IOError while writing to file %s: %s", path, e)
            raise e
        except GeneratorExit:
            logger.info("Finished writing to %s", path)

    @staticmethod
    @coroutine
    def clean_html_chunks() -> Generator:
        output = NetworkOperationsPipe.write_to_file()
        parser = ChunkHTMLParser()
        path = yield
        output.send(path)
        try:
            while True:
                chunk = yield
                parser.feed(chunk)
                parsed_text = parser.get_data()
                output.send(parsed_text)
        except UnicodeDecodeError as e:
            logger.error("UnicodeDecodeError while parsing HTML: %s", e)
            raise e
        except GeneratorExit:
            logger.info("Html document has been parsed correctly")
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise e

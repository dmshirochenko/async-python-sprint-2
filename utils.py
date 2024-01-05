import os
import shutil
import requests
import logging.config
from html.parser import HTMLParser

from config.logger import LOGGING
from job import coroutine

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class FileSystemOperations:
    @staticmethod
    @coroutine
    def create_directory(path):
        try:
            os.makedirs(path)
            yield f"Directory created at {path}"
        except FileExistsError:
            yield f"Directory exists at {path}"

    @staticmethod
    @coroutine
    def delete_directory(path):
        try:
            shutil.rmtree(path)
            yield f"Directory deleted at {path}"
        except FileNotFoundError:
            yield "Directory not found"

    @staticmethod
    @coroutine
    def create_file(path):
        try:
            with open(path, "w") as file:
                file.write("")
            yield f"File created at {path}"
        except Exception as e:
            yield f"Error creating file at {path}: {e}"

    @staticmethod
    @coroutine
    def delete_file(path):
        try:
            os.remove(path)
            yield f"File deleted at {path}"
        except FileNotFoundError:
            yield "File not found"


class FileOperations:
    @staticmethod
    @coroutine
    def write_to_file(path, content):
        with open(path, "w") as file:
            file.write(content)
        yield f"Content written to {path}"

    @staticmethod
    @coroutine
    def read_from_file(path):
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
    def html_to_txt_pipeline(url, path):
        output = NetworkOperationsPipe().clean_html_chunks()
        output.send(path)
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    yield output.send(chunk.decode("utf-8"))
        except requests.exceptions.RequestException as e:
            raise e

    @staticmethod
    @coroutine
    def write_to_file():
        path = yield
        try:
            with open(path, "w") as file:
                while True:
                    chunk = yield
                    file.write(chunk)
                    file.flush()
        except IOError as e:
            logger.error(f"IOError while writing to file {path}: {e}")
            raise e
        except GeneratorExit:
            logger.info(f"Finished writing to {path}")

    @staticmethod
    @coroutine
    def clean_html_chunks():
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
            logger.error(f"UnicodeDecodeError while parsing HTML: {e}")
            raise e
        except GeneratorExit:
            logger.info("Html document has been parsed correctly")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise e

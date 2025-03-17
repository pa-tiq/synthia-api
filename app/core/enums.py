from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"

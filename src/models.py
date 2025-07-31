#!/usr/bin/env python3
from enum import Enum
from pydantic import BaseModel, HttpUrl

class MediaType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    PICTURE = "picture"

class DownloadRequest(BaseModel):
    url: HttpUrl

class VideoDownloadRequest(BaseModel):
    url: HttpUrl

class AudioDownloadRequest(BaseModel):
    url: HttpUrl

class PictureDownloadRequest(BaseModel):
    url: HttpUrl

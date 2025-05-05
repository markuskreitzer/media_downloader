#!/usr/bin/env python3
from pydantic import BaseModel, HttpUrl

class DownloadRequest(BaseModel):
    url: HttpUrl

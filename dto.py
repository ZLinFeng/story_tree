# coding=utf-8
"""
@file    dto
@date    2023/8/8 11:28
@author  zlf
"""
from pydantic import BaseModel
from typing import List


class News(BaseModel):
    title: str
    content: str


class ClusterRequest(BaseModel):
    news: List[News]

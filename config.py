# coding=utf-8
"""
@file    config
@date    2023/8/8 11:42
@author  zlf
"""
import os
from loguru import logger

__HOME__ = os.path.dirname(__file__)

__DATABASE__ = os.path.join(__HOME__, "data/database.db")

logger.add(os.path.join(__HOME__, "data/logs/main.log"), rotation="1 day")

__keywords_url__ = os.environ.get(
    "KEYWORDS", "http://10.11.203.190:18111/bert_g4")
__keywords_process_num__ = 3

__similarity_process_num__ = 30

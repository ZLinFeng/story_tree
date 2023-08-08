# coding=utf-8
"""
@file    main.py
@date    2023/8/8 11:20
@author  zlf
"""
import threading
from story_cluster import schedule_run

import uvicorn

from web import create_app

if __name__ == '__main__':
    t = threading.Thread(target=schedule_run)
    t.start()
    app = create_app()
    uvicorn.run(app, port=18113, host="0.0.0.0", workers=10)

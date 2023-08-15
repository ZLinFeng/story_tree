# coding=utf-8
"""
@file    story_cluster
@date    2023/8/8 13:47
@author  zlf
"""
import json
import threading
import time
from multiprocessing import Queue, Process, Manager

import networkx as nx
import requests
import schedule
from networkx import Graph
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import __keywords_url__, __keywords_process_num__, __similarity_process_num__
from typing import Optional
from loguru import logger

from database import add_cluster_news_list, finish_job_by_id, get_request_job, list_news_by_job_id, add_cluster_news, add_cluster, running_job_by_id
from story_tree import StoryTreeNode
from do import ClusterNews


def request_keywords(text: str) -> Optional[list]:
    res = requests.post(__keywords_url__, json={
                        "content": text, "lang": "zh-CN"})
    try:
        obj = json.loads(res.text)
        res = obj["new_answer"]
        return [word["word"] for word in res]
    except Exception as e:
        logger.error("Keywords Exception.", e)
        return None


def keywords_thread(request_queue, collect):
    while True:
        item = request_queue.get()
        if item is None:
            break
        content = item["content"]
        if len(content) <= 100:
            continue
        content = clean_news(content)
        keywords_res = request_keywords(content)
        item["keywords"] = keywords_res
        collect.append(item)


def keywords(news: list) -> list:
    with Manager() as manager:
        collect = manager.list()
        request_queue = Queue(maxsize=5)

        processes = []

        # 创建并启动关键词抽取进程
        for number in range(__keywords_process_num__):
            process = Process(target=keywords_thread,
                              args=(request_queue, collect))
            process.start()
            processes.append(process)

        for item in news:
            request_queue.put(item)

        for _ in range(__keywords_process_num__):
            request_queue.put(None)

        # 等待所有进程完成
        for process in processes:
            process.join()
        return list(collect)


def request_producer(news, request_queue):
    for item in news:
        request_queue.put(item)
    for _ in range(__similarity_process_num__):
        request_queue.put(None)


def request_consumer(request_queue, response_queue, topic_keywords_list):
    while True:
        item = request_queue.get()
        if item is None:
            response_queue.put(None)
            break
        logger.info(f"{threading.current_thread().getName()}:{item}")
        words = item["keywords"]
        if len(words) == 0:
            continue
        max_topic = 0
        max_similarities = 0.0
        for topic_index, topic_words in enumerate(topic_keywords_list):
            try:
                vectorizer = TfidfVectorizer()
                features = vectorizer.fit_transform(
                    [" ".join(words), " ".join(topic_words)])
                cosine_similarities = cosine_similarity(
                    features[0], features[1])
                if cosine_similarities[0][0] > max_similarities:
                    max_topic = topic_index
                    max_similarities = cosine_similarities[0][0]
            except Exception as e:
                logger.error("Similarity exception.", e)
        topic_name = str(max_topic)
        item["topic"] = topic_name
        item["cos"] = max_similarities
        item["keywords"] = ",".join(words)
        response_queue.put(item)


def response_consumer(response_queue, topic_keywords_list, job_id):
    res = {}
    total = 0
    receiver_none = 0
    batch = []
    while True:
        item = response_queue.get()
        if item is None:
            receiver_none += 1
            if receiver_none == __similarity_process_num__:
                break
            else:
                logger.info(f"Final consumer received {receiver_none}")
                continue
        total += 1
        logger.info(f"Finish: {total}")
        batch.append({"uid": item["uid"], "cluster_id": int(
            item["topic"]), "cos": item["cos"], "keywords": item["keywords"]})
        if len(batch) >= 1000:
            add_cluster_news_list(batch, job_id)
            batch = []
        topic_name = item["topic"]
        if not res.__contains__(topic_name):
            res[topic_name] = topic_keywords_list[int(topic_name)]

    if len(batch) > 0:
        add_cluster_news_list(batch, job_id)

    for key, value in res.items():
        add_cluster(job_id=job_id, cluster_id=int(
            key), keywords=",".join(value))


def graph_cluster(news: list, job_id: int):
    G: Graph = nx.Graph()
    news_keywords = [one["keywords"] for one in news]
    tree = StoryTreeNode(g=G, keywords=news_keywords)
    tree.keywords_edge_filter()
    topic_keywords_list = tree.community_detect(0.0005)
    # 创建两个队列
    request_queue = Queue(maxsize=100)
    response_queue = Queue(maxsize=100)

    producer_thread = Process(target=request_producer,
                              args=(news, request_queue))

    response_consumer_thread = Process(target=response_consumer, args=(
        response_queue, topic_keywords_list, job_id))

    # 启动
    consumer_threads = []
    for i in range(__similarity_process_num__):
        consumer_threads.append(
            Process(target=request_consumer, args=(request_queue, response_queue, topic_keywords_list)))

    producer_thread.start()
    for t in consumer_threads:
        t.start()

    response_consumer_thread.start()

    # 等待停止
    producer_thread.join()
    for t in consumer_threads:
        t.join()
    response_consumer_thread.join()


def clean_news(news: str) -> str:
    lines = news.split("\n")
    lines = [line for line in lines if len(line) > 30]
    return "\n".join(lines)


def story_tree_cluster():
    job_id = get_request_job()
    if job_id == 0:
        return
    news_list = list_news_by_job_id(job_id)
    if news_list is None:
        return
    logger.info("Start Cluster...")
    running_job_by_id(job_id)
    news_list_with_keywords = keywords(news_list)
    graph_cluster(news_list_with_keywords, job_id)
    finish_job_by_id(job_id)
    logger.info("End Cluster...")


def schedule_run():
    schedule.every(5).seconds.do(story_tree_cluster)

    while True:
        schedule.run_pending()
        time.sleep(1)

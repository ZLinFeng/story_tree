# coding=utf-8
"""
@file    database
@date    2023/8/8 11:53
@author  zlf
"""
import datetime
import uuid
from typing import Optional

from sqlalchemy import create_engine, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from do import Base, Job, Cluster, Corpus, JobType, ClusterNews
from loguru import logger

from config import __DATABASE__

from dto import ClusterRequest

# engine = create_engine(f"sqlite:///{__DATABASE__}")
engine = create_engine(
    "mysql+pymysql://root:123456@10.11.203.201:4000/giraffe")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def create_job(body: ClusterRequest) -> int:
    session = Session()
    try:
        now = datetime.datetime.now()
        # 创建job
        job = Job(status=JobType.READY, create_time=now, update_time=now)
        session.add(job)
        session.commit()
        # 写入语料
        for item in body.news:
            time_based_uuid = uuid.uuid1()
            one_corpus = Corpus(
                job_id=job.id,
                uid=time_based_uuid,
                title=item.title,
                content=item.content
            )
            session.add(one_corpus)
        session.commit()
        return job.id
    except SQLAlchemyError as e:
        logger.error(e)
        session.rollback()
        return -1
    finally:
        session.close()


def get_request_job() -> int:
    session = Session()
    try:
        users = session.query(Job).filter(
            Job.status == JobType.READY).order_by(asc(Job.id)).limit(1).all()
        if users is None or len(users) == 0:
            return 0
        return users[0].id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Search request job exception.", e)
        return -1
    finally:
        session.close()


def finish_job_by_id(job_id: int) -> int:
    session = Session()
    try:
        jobs = session.query(Job).filter(Job.id == job_id).all()
        if jobs is None or len(jobs) == 0:
            return -1

        job = jobs[0]
        job.status = JobType.FINISH
        job.update_time = datetime.datetime.now()
        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Finish job exception.", e)
        return -1
    finally:
        session.close()


def running_job_by_id(job_id: int) -> int:
    session = Session()
    try:
        jobs = session.query(Job).filter(Job.id == job_id).all()
        if jobs is None or len(jobs) == 0:
            return -1

        job = jobs[0]
        job.status = JobType.RUNNING
        job.update_time = datetime.datetime.now()
        session.commit()
        return 1
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Running job exception.", e)
        return -1
    finally:
        session.close()


def list_news_by_job_id(job_id: int) -> Optional[list]:
    session = Session()
    try:
        corpus_list = session.query(Corpus).filter(
            Corpus.job_id == job_id).all()
        if corpus_list is None or len(corpus_list) == 0:
            return None
        news_list = []
        for item in corpus_list:
            news_list.append(
                {"title": item.title, "content": item.content, "uid": item.uid})
        return news_list
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("List news exception.", e)
        return None
    finally:
        session.close()


def add_cluster_news(news_uid: str, job_id: int, cluster_id: int, cos: float, keywords: str) -> bool:
    session = Session()
    try:
        cluster_news = ClusterNews(uid=news_uid,
                                   job_id=job_id,
                                   cluster_id=cluster_id,
                                   cos=cos,
                                   keywords=keywords)
        session.add(cluster_news)
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Add cluster news exception.", e)
        return False
    finally:
        session.close()


def add_cluster_news_list(news: list, job_id: int) -> bool:
    session = Session()
    try:
        for one in news:
            cluster_news = ClusterNews(uid=one["uid"],
                                       job_id=job_id,
                                       cluster_id=one["cluster_id"],
                                       cos=one["cos"],
                                       keywords=one["keywords"])
            session.add(cluster_news)
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Add cluster news exception.", e)
        return False
    finally:
        session.close()


def add_cluster(job_id: int, cluster_id: int, keywords: str) -> bool:
    session = Session()
    try:
        cluster = Cluster(
            job_id=job_id, cluster_id=cluster_id, keywords=keywords)
        session.add(cluster)
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Add cluster exception.", e)
        return False
    finally:
        session.close()

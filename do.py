# coding=utf-8
"""
@file    do
@date    2023/8/8 13:16
@author  zlf
"""
from sqlalchemy import Column, Integer, DateTime, String, Enum, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum

Base = declarative_base()


class JobType(PyEnum):
    READY = "ready"
    RUNNING = "running"
    FINISH = "finsh"


class Job(Base):
    __tablename__ = "tb_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(JobType))
    create_time = Column(DateTime)
    update_time = Column(DateTime)


class Corpus(Base):
    __tablename__ = "tb_corpus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(50))
    job_id = Column(Integer)
    title = Column(Text)
    content = Column(Text)


class ClusterNews(Base):
    """
    聚类的每个新闻结果表
    """
    __tablename__ = "tb_cluster_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(50))
    job_id = Column(Integer)
    cluster_id = Column(Integer)
    cos = Column(Float)
    keywords = Column(Text)


class Cluster(Base):
    """
    聚类的类别表
    """
    __tablename__ = "tb_cluster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer)
    cluster_id = Column(Integer)
    keywords = Column(Text)

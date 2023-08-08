# coding=utf-8
"""
@file    story_tree
@date    2023/8/8 15:45
@author  zlf
"""
import itertools
import time
from typing import Optional

import networkx as nx
from loguru import logger
from networkx import Graph


class StoryTreeNode:
    def __init__(self, g: Graph, keywords: list):
        self._g = g
        self._words = set()
        self._keywords_list = keywords
        self._build()

    @property
    def keywords(self):
        return self._words

    def _build(self):
        start_time = time.time()
        for index, keywords in enumerate(self._keywords_list):
            for word in keywords:
                self._words.add(word)
            if len(keywords) == 0:
                continue
            keywords_tuples = list(itertools.combinations(keywords, 2))
            for one_tuple in keywords_tuples:
                if self._g.has_edge(one_tuple[0], one_tuple[1]):
                    weight = self._g.get_edge_data(one_tuple[0], one_tuple[1])["weight"]
                    self._g.add_edge(one_tuple[0], one_tuple[1], weight=weight + 1)
                else:
                    self._g.add_edge(one_tuple[0], one_tuple[1], weight=1)
        end_time = time.time()
        logger.info(f"{end_time - start_time}s used by building graph.")

    def keywords_edge_filter(self):
        start_time = time.time()
        # 删除权重小于3的边
        for u, v, data in list(self._g.edges(data=True)):
            if data["weight"] < 3:
                self._g.remove_edge(u, v)

        # 验证条件概率
        words_list = list(self._words)
        for i in range(len(words_list) - 1):
            for j in range(i + 1, len(words_list)):
                word_a = words_list[i]
                word_b = words_list[j]
                if not self._g.has_edge(word_a, word_b):
                    continue
                # a 和 b 相连的权重
                weight = self._g.get_edge_data(word_a, word_b)["weight"]

                # a 所有边权重
                a_weights = [data['weight'] for v, data in self._g[word_a].items()]
                a_total = sum(a_weights)

                # b 所有边权重
                b_weights = [data['weight'] for v, data in self._g[word_b].items()]
                b_total = sum(b_weights)

                if (weight * 1.0 / a_total < 0.15) or (weight * 1.0 / b_total < 0.15):
                    self._g.remove_edge(word_a, word_b)
        end_time = time.time()
        logger.info(f"{end_time - start_time}s used by filtering edges.")

    def community_detect(self, threshold: float) -> Optional[list]:
        # 找到所有的孤立节点
        isolates = list(nx.isolates(self._g))
        # 删除这些孤立节点
        self._g.remove_nodes_from(isolates)

        # 计算边的 betweenness centrality
        edge_betweenness = nx.edge_betweenness_centrality(self._g)
        for edge in edge_betweenness:
            if edge_betweenness[edge] > threshold:
                print(f"Edge {edge}: betweenness centrality {edge_betweenness[edge]}")
                self._g.remove_edge(edge[0], edge[1])

        communities = list(nx.algorithms.community.label_propagation_communities(self._g))

        topic_keywords_list = []
        for i, community in enumerate(communities):
            # 排除长度是1的, 一个关键词比较模糊
            if len(list(community)) == 1:
                logger.info(f"Community {i + 1}: {list(community)}")
                continue
            topic_keywords_list.append(list(community))
        return topic_keywords_list

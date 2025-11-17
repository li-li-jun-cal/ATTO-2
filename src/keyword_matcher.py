#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键字匹配模块
用于匹配评论中的关键字
"""

import re
import json
from pathlib import Path
from typing import List, Dict


class KeywordMatcher:
    """关键字匹配器"""

    def __init__(self, keywords=None, keywords_file=None):
        """
        初始化关键字匹配器

        Args:
            keywords: 关键字列表
            keywords_file: 关键字配置文件路径
        """
        self.keywords = []
        self.reply_templates = {}

        # 从文件加载
        if keywords_file and Path(keywords_file).exists():
            self._load_from_file(keywords_file)
        # 使用传入的关键字
        elif keywords:
            self.keywords = keywords
        # 使用默认关键字
        else:
            self._load_default_keywords()

    def _load_from_file(self, keywords_file):
        """从 JSON 文件加载关键字配置"""
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.keywords = data.get('keywords', [])
                self.reply_templates = data.get('reply_templates', {})
            print(f"✓ 已加载关键字文件: {keywords_file}")
        except Exception as e:
            print(f"✗ 加载关键字文件失败: {e}，使用默认关键字")
            self._load_default_keywords()

    def _load_default_keywords(self):
        """加载默认关键字"""
        self.keywords = [
            '点赞',
            '支持',
            '棒',
            '👍',
            '顶',
            '很有意思',
            '非常好',
            '推荐',
            '赞',
            '加油',
        ]
        self.reply_templates = {
            '点赞': '感谢点赞！🙏',
            '支持': '感谢支持，继续加油！💪',
            '棒': '感谢评价！😊',
            '👍': '谢谢！💕',
            '顶': '感谢支持！🎉',
            '很有意思': '哈哈，感谢喜欢！😄',
            '非常好': '感谢评论！✨',
            '推荐': '感谢推荐！🙏',
            '赞': '感谢点赞！',
            '加油': '谢谢鼓励，继续加油！💪',
        }

    def match_comments(self, comments):
        """
        对评论列表进行关键字匹配

        Args:
            comments: 评论列表

        Returns:
            list: 匹配的评论列表
        """
        matched = []

        # 如果没有关键词（随机模式），返回所有评论
        if not self.keywords:
            for comment in comments:
                # 获取评论文本
                text = self._extract_comment_text(comment)
                matched.append({
                    'comment_id': comment.get('id'),
                    'comment_text': text,
                    'comment_content': comment.get('comment_content', ''),
                    'keyword': None,  # 随机模式没有关键词
                    'reply_text': '感谢评论！',  # 默认回复
                    'position': comment.get('position'),
                    'bounds_str': comment.get('bounds_str'),
                    'scroll_index': comment.get('scroll_index'),  # 添加scroll_index
                    'scroll_offset': comment.get('scroll_offset'),  # 添加scroll_offset
                    'full_comment': comment,
                })
            return matched

        # 关键词模式
        for comment in comments:
            # 获取评论文本
            text = self._extract_comment_text(comment)

            # 对每个关键字进行检查
            for keyword in self.keywords:
                if keyword in text:
                    matched.append({
                        'comment_id': comment.get('id'),
                        'comment_text': text,
                        'comment_content': comment.get('comment_content', ''),
                        'keyword': keyword,
                        'reply_text': self._get_reply_text(keyword),
                        'position': comment.get('position'),
                        'bounds_str': comment.get('bounds_str'),
                        'scroll_index': comment.get('scroll_index'),  # 添加scroll_index
                        'scroll_offset': comment.get('scroll_offset'),  # 添加scroll_offset
                        'full_comment': comment,  # 保存完整评论数据
                    })
                    break  # 每条评论只匹配一次

        return matched

    def match_comment(self, comment_text):
        """
        匹配单条评论

        Args:
            comment_text: 评论文本

        Returns:
            dict: 匹配结果 (keyword, reply_text) 或 None
        """
        for keyword in self.keywords:
            if keyword in comment_text:
                return {
                    'keyword': keyword,
                    'reply_text': self._get_reply_text(keyword),
                }

        return None

    def _extract_comment_text(self, comment):
        """
        从评论数据中提取纯文本

        优先级: text > comment_content > content_desc (解析后)

        content_desc 格式: "用户名,评论内容,时间, · 地点,回复 按钮,"
        需要提取中间的评论内容部分
        """
        # 优先使用 text 或 comment_content
        text = comment.get('text', '') or comment.get('comment_content', '')
        if text:
            return text

        # 从 content_desc 中提取
        content_desc = comment.get('content_desc', '')
        if content_desc:
            # 按逗号分割: ["用户名", "评论内容", "时间", " · 地点", "回复 按钮", ""]
            parts = content_desc.split(',')
            if len(parts) >= 2:
                # 第二部分是评论内容
                return parts[1].strip()

        return ''

    def _get_reply_text(self, keyword):
        """根据关键字获取回复文本"""
        return self.reply_templates.get(keyword, f'感谢提到"{keyword}"！')

    def add_keyword(self, keyword, reply_text=None):
        """添加新的关键字"""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            if reply_text:
                self.reply_templates[keyword] = reply_text
            else:
                self.reply_templates[keyword] = f'感谢提到"{keyword}"！'

    def remove_keyword(self, keyword):
        """移除关键字"""
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            if keyword in self.reply_templates:
                del self.reply_templates[keyword]

    def get_keywords(self):
        """获取所有关键字"""
        return self.keywords

    def set_reply_template(self, keyword, reply_text):
        """设置回复模板"""
        self.reply_templates[keyword] = reply_text

    def save_config(self, output_file='keywords.json'):
        """保存配置到文件"""
        config = {
            'keywords': self.keywords,
            'reply_templates': self.reply_templates,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"✓ 配置已保存: {output_file}")

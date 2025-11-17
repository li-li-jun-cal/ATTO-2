#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试关键词匹配功能
"""

import sys
import json
sys.path.insert(0, 'src')

from keyword_matcher import KeywordMatcher

# 加载评论文件
with open('outputs/comments_collected_20251117_120442.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    comments = data['comments']

print(f"\n总评论数: {len(comments)}")

# 加载配置
with open('outputs/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    keywords_dict = config['keywords']

print(f"关键词: {keywords_dict}")

# 创建关键词匹配器
matcher = KeywordMatcher()
matcher.keywords = list(keywords_dict.keys())
matcher.reply_templates = keywords_dict

# 测试匹配
matched = matcher.match_comments(comments)

print(f"\n匹配结果: {len(matched)} 条评论")

# 显示匹配的评论
for idx, match in enumerate(matched[:10], 1):
    text = match['comment_text']
    keyword = match['keyword']
    # 只显示前100个字符
    display_text = text[:100] if len(text) > 100 else text
    print(f"\n{idx}. 关键词: {keyword}")
    print(f"   评论: {display_text}")
    print(f"   回复: {match['reply_text']}")

if len(matched) > 10:
    print(f"\n... 还有 {len(matched) - 10} 条匹配的评论 ...")

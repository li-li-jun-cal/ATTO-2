#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试脚本 - 查看当前屏幕评论元素的实际结构
"""

import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, 'src')

from device_interaction import DeviceInteraction
from element_ids import DouyinElementIds

print("\n连接设备...")
device = DeviceInteraction(timeout=10)
print("✓ 设备已连接\n")

print("获取当前 UI 层级...")
xml_str = device.device.dump_hierarchy()
root = ET.fromstring(xml_str)

print(f"✓ UI 层级已获取\n")

# 查找所有评论元素
comment_elements = []
for element in root.iter():
    resource_id = element.get('resource-id', '')
    if DouyinElementIds.COMMENT_ITEM in resource_id or 'e7w' in resource_id:
        comment_elements.append(element)

print(f"找到 {len(comment_elements)} 个评论元素 (resource-id 包含 'e7w')\n")

# 显示前 3 个评论元素的详细信息
for idx, elem in enumerate(comment_elements[:3], 1):
    print(f"=" * 80)
    print(f"评论 #{idx}")
    print(f"=" * 80)
    print(f"resource-id: {elem.get('resource-id', '')}")
    print(f"class: {elem.get('class', '')}")
    print(f"text: {elem.get('text', '')}")
    print(f"content-desc: {elem.get('content-desc', '')[:150]}...")
    print(f"bounds: {elem.get('bounds', '')}")
    print()

# 也查找其他可能的评论元素
print("\n" + "=" * 80)
print("查找其他可能的评论相关元素:")
print("=" * 80)

other_ids = [
    DouyinElementIds.COMMENT_LIST_CONTAINER,
    'com.ss.android.ugc.aweme:id/em=',  # 评论文本
]

for search_id in other_ids:
    elements = []
    for element in root.iter():
        if element.get('resource-id') == search_id:
            elements.append(element)

    print(f"\n{search_id}: 找到 {len(elements)} 个")

    if elements:
        elem = elements[0]
        print(f"  text: {elem.get('text', '')[:100]}")
        print(f"  content-desc: {elem.get('content-desc', '')[:100]}")

device.close()
print("\n✓ 完成")

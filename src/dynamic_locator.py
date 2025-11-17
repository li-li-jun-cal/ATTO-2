#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态定位模块 - 核心！
实时查询 UI 元素，获取最新的屏幕位置
这是自动回复系统的关键模块
"""

import time
import re
import xml.etree.ElementTree as ET
from element_ids import DouyinElementIds


class DynamicLocator:
    """动态定位器 - 实时查询 UI 获取最新位置"""

    def __init__(self, device, logger=None):
        """
        初始化动态定位器

        Args:
            device: DeviceInteraction 实例
            logger: 日志对象
        """
        self.device = device
        self.logger = logger

        # 滑动位置跟踪（核心！）
        self.current_scroll_offset = 0  # 当前滑动偏移

    def find_comment_by_text(self, target_text, timeout=5):
        """
        在当前屏幕上查找评论

        关键特点:
        - 直接从 UI 查询，不使用缓存坐标
        - 获取最新的元素位置
        - 非常稳定和可靠

        Args:
            target_text: 目标评论文本（可以是部分文本）
            timeout: 超时时间（秒）

        Returns:
            dict: 找到的评论信息，包含位置坐标
        """
        if self.logger:
            self.logger.info(f"🔍 查找评论: {target_text[:40]}...")
        else:
            print(f"🔍 查找评论: {target_text[:40]}...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 获取当前的 UI 层级树
                xml_str = self.device.device.dump_hierarchy()
                root = ET.fromstring(xml_str)

                # 在所有评论元素中搜索
                for element in root.iter():
                    if element.get('resource-id') == DouyinElementIds.COMMENT_ITEM:
                        # 获取文本 - 优先 text,其次从 content-desc 提取
                        text = element.get('text', '')
                        if not text:
                            content_desc = element.get('content-desc', '')
                            if content_desc:
                                # 从 content_desc 提取纯评论: "用户名,评论内容,时间,..."
                                parts = content_desc.split(',')
                                if len(parts) >= 2:
                                    text = parts[1].strip()

                        # 检查是否包含目标文本
                        if text and target_text in text:
                            # 解析坐标
                            bounds = self._parse_bounds(element.get('bounds', ''))

                            if bounds:
                                result = {
                                    'found': True,
                                    'text': text,
                                    'bounds': bounds,
                                    'center_x': (bounds[0] + bounds[2]) // 2,
                                    'center_y': (bounds[1] + bounds[3]) // 2,
                                    'width': bounds[2] - bounds[0],
                                    'height': bounds[3] - bounds[1],
                                }

                                if self.logger:
                                    self.logger.info(f"✓ 找到评论，坐标: ({result['center_x']}, {result['center_y']})")
                                else:
                                    print(f"✓ 找到评论，坐标: ({result['center_x']}, {result['center_y']})")

                                return result

                # 没找到，等待后重试
                time.sleep(0.5)

            except Exception as e:
                if self.logger:
                    self.logger.debug(f"查询异常: {e}")
                time.sleep(0.5)

        # 超时，未找到
        if self.logger:
            self.logger.warning(f"⚠️  未找到评论: {target_text[:40]}...")
        else:
            print(f"⚠️  未找到评论: {target_text[:40]}...")

        return {'found': False}

    def scroll_to_find_comment(self, target_text, comment_scroll_offset=None,
                              current_list_offset=None, max_scrolls=10):
        """
        智能滑动寻找评论（核心修复！）

        Args:
            target_text: 目标评论文本
            comment_scroll_offset: 评论获取时的滑动偏移（重要！）
            current_list_offset: 当前评论列表的滑动偏移（重要！）
            max_scrolls: 最多滑动次数

        Returns:
            dict: 找到的评论信息或空字典

        工作原理：
        1. 如果知道评论的滑动偏移，先回滚到评论位置附近
        2. 在当前位置尝试查找
        3. 如果没找到，进行双向搜索（先向下，再向上）
        """
        if self.logger:
            self.logger.info(f"🎯 智能定位评论: {target_text[:40]}...")
        else:
            print(f"🎯 智能定位评论: {target_text[:40]}...")

        # 第1步：智能回滚到评论位置附近
        if comment_scroll_offset is not None and current_list_offset is not None:
            # 计算需要回滚的距离
            scroll_delta = current_list_offset - comment_scroll_offset

            if self.logger:
                self.logger.info(f"  评论在偏移 {comment_scroll_offset}，当前偏移 {current_list_offset}，需要调整 {scroll_delta}")
            else:
                print(f"  评论在偏移 {comment_scroll_offset}，当前偏移 {current_list_offset}，需要调整 {scroll_delta}")

            if scroll_delta > 0:
                # 需要向下滚动
                if self.logger:
                    self.logger.info(f"  ↓ 向下滚动 {scroll_delta} 次，回到评论位置...")
                else:
                    print(f"  ↓ 向下滚动 {scroll_delta} 次，回到评论位置...")

                for i in range(scroll_delta):
                    self.device.drag_comment_list(direction='down', steps=3)
                    time.sleep(0.5)
                    self.current_scroll_offset -= 1

            elif scroll_delta < 0:
                # 需要向上滚动
                scroll_up_count = abs(scroll_delta)
                if self.logger:
                    self.logger.info(f"  ↑ 向上滚动 {scroll_up_count} 次，回到评论位置...")
                else:
                    print(f"  ↑ 向上滚动 {scroll_up_count} 次，回到评论位置...")

                for i in range(scroll_up_count):
                    self.device.drag_comment_list(direction='up', steps=3)
                    time.sleep(0.5)
                    self.current_scroll_offset += 1

        # 第2步：在当前位置尝试查找
        result = self.find_comment_by_text(target_text, timeout=2)
        if result['found']:
            if self.logger:
                self.logger.info(f"✓ 在当前位置找到评论")
            else:
                print(f"✓ 在当前位置找到评论")
            return result

        # 第3步：双向搜索（先向下，再向上）
        if self.logger:
            self.logger.info(f"  当前位置未找到，开始双向搜索...")
        else:
            print(f"  当前位置未找到，开始双向搜索...")

        # 先向下搜索
        for scroll_idx in range(max_scrolls // 2):
            if self.logger:
                self.logger.debug(f"  ↓ 向下搜索 {scroll_idx + 1}...")
            else:
                print(f"  ↓ 向下搜索 {scroll_idx + 1}...")

            self.device.drag_comment_list(direction='down', steps=3)
            self.current_scroll_offset -= 1
            time.sleep(0.8)

            result = self.find_comment_by_text(target_text, timeout=2)
            if result['found']:
                if self.logger:
                    self.logger.info(f"✓ 向下搜索第 {scroll_idx + 1} 次找到")
                else:
                    print(f"✓ 向下搜索第 {scroll_idx + 1} 次找到")
                return result

        # 再向上搜索（需要先回到起点再向上）
        # 回到起点
        for i in range(max_scrolls // 2):
            self.device.drag_comment_list(direction='up', steps=3)
            self.current_scroll_offset += 1
            time.sleep(0.3)

        # 向上搜索
        for scroll_idx in range(max_scrolls // 2):
            if self.logger:
                self.logger.debug(f"  ↑ 向上搜索 {scroll_idx + 1}...")
            else:
                print(f"  ↑ 向上搜索 {scroll_idx + 1}...")

            self.device.drag_comment_list(direction='up', steps=3)
            self.current_scroll_offset += 1
            time.sleep(0.8)

            result = self.find_comment_by_text(target_text, timeout=2)
            if result['found']:
                if self.logger:
                    self.logger.info(f"✓ 向上搜索第 {scroll_idx + 1} 次找到")
                else:
                    print(f"✓ 向上搜索第 {scroll_idx + 1} 次找到")
                return result

        # 所有搜索都失败了
        if self.logger:
            self.logger.warning(f"✗ 双向搜索 {max_scrolls} 次后仍未找到: {target_text[:40]}...")
        else:
            print(f"✗ 双向搜索 {max_scrolls} 次后仍未找到: {target_text[:40]}...")

        return {'found': False}

    def find_reply_button(self, comment_bounds, timeout=3):
        """
        查找评论下的回复按钮

        Args:
            comment_bounds: 评论的 bounds [left, top, right, bottom]
            timeout: 超时时间

        Returns:
            dict: 回复按钮的位置或空字典
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 回复按钮通常在评论的右下角
                # 估计位置在评论右边，靠下
                reply_x = comment_bounds[2] - 50  # 右边 50px
                reply_y = comment_bounds[3] - 20  # 下边 20px

                return {
                    'found': True,
                    'x': reply_x,
                    'y': reply_y,
                }

            except Exception as e:
                time.sleep(0.5)

        return {'found': False}

    def _parse_bounds(self, bounds_str):
        """
        解析 bounds 字符串

        示例: "[0,1800][1080,2088]" -> (0, 1800, 1080, 2088)
        """
        try:
            match = re.findall(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match[0])
                return (x1, y1, x2, y2)
        except:
            pass
        return None

    def verify_element_exists(self, resource_id, timeout=2):
        """
        验证元素是否存在

        Args:
            resource_id: 元素的 resource ID
            timeout: 超时时间

        Returns:
            bool: 元素是否存在
        """
        try:
            element = self.device.device(resourceId=resource_id)
            start_time = time.time()

            while time.time() - start_time < timeout:
                if element.exists:
                    return True
                time.sleep(0.2)

            return False

        except:
            return False

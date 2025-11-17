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

        # 滚动位置追踪
        self.current_scroll_index = 0  # 当前滚动索引（从收集评论结束时的位置开始）
        self.scroll_distance = 260  # 每次滚动的像素距离

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

    def scroll_to_comment_precise(self, target_text, target_scroll_index):
        """
        精确滚动到评论位置（新方法 - 使用scroll_index精确计算）

        工作原理：
        1. 根据目标评论的scroll_index和当前scroll_index，计算需要滚动的次数
        2. 一次性滚动到目标位置附近
        3. 在当前屏幕查找评论

        示例：
        - 评论在scroll_index=0（未滑动），当前在scroll_index=10
          需要向下滑动10次回到位置0
        - 评论在scroll_index=4，当前在scroll_index=0
          需要向上滑动4次到达位置4

        Args:
            target_text: 目标评论文本
            target_scroll_index: 目标评论的scroll_index（从评论数据中获取）

        Returns:
            dict: 找到的评论信息或空字典
        """
        if self.logger:
            self.logger.info(f"📍 精确滚动定位评论: {target_text[:40]}...")
            self.logger.info(f"   目标位置: scroll_index={target_scroll_index}, 当前位置: scroll_index={self.current_scroll_index}")
        else:
            print(f"📍 精确滚动定位评论: {target_text[:40]}...")
            print(f"   目标位置: scroll_index={target_scroll_index}, 当前位置: scroll_index={self.current_scroll_index}")

        # 计算需要滚动的次数和方向
        scroll_delta = target_scroll_index - self.current_scroll_index

        if scroll_delta != 0:
            # 确定滚动方向
            direction = 'up' if scroll_delta > 0 else 'down'
            scroll_times = abs(scroll_delta)

            if self.logger:
                self.logger.info(f"   需要向{direction}滚动 {scroll_times} 次 ({scroll_times * self.scroll_distance} 像素)")
            else:
                print(f"   需要向{direction}滚动 {scroll_times} 次 ({scroll_times * self.scroll_distance} 像素)")

            # 执行滚动 - 一次性滚动到目标位置
            for i in range(scroll_times):
                self.device.drag_comment_list(direction=direction, steps=3)
                time.sleep(0.5)  # 短暂等待，让UI稳定

            # 更新当前位置
            self.current_scroll_index = target_scroll_index

            # 等待UI稳定
            time.sleep(1)
        else:
            if self.logger:
                self.logger.info("   已在目标位置，无需滚动")
            else:
                print("   已在目标位置，无需滚动")

        # 在当前屏幕查找评论
        result = self.find_comment_by_text(target_text, timeout=3)

        if result['found']:
            if self.logger:
                self.logger.info(f"✓ 精确定位成功！")
            else:
                print(f"✓ 精确定位成功！")
            return result
        else:
            # 精确滚动失败，尝试微调（向上和向下各尝试1次）
            if self.logger:
                self.logger.warning(f"⚠️  精确位置未找到，尝试微调...")
            else:
                print(f"⚠️  精确位置未找到，尝试微调...")

            # 向上微调1次
            self.device.drag_comment_list(direction='up', steps=3)
            time.sleep(1)
            result = self.find_comment_by_text(target_text, timeout=2)
            if result['found']:
                self.current_scroll_index += 1
                return result

            # 向下微调2次（回到原位再向下1次）
            self.device.drag_comment_list(direction='down', steps=3)
            time.sleep(0.5)
            self.device.drag_comment_list(direction='down', steps=3)
            time.sleep(1)
            result = self.find_comment_by_text(target_text, timeout=2)
            if result['found']:
                self.current_scroll_index -= 1
                return result

            # 回到原位
            self.device.drag_comment_list(direction='up', steps=3)
            time.sleep(0.5)

            if self.logger:
                self.logger.warning(f"✗ 精确定位失败: {target_text[:40]}...")
            else:
                print(f"✗ 精确定位失败: {target_text[:40]}...")

            return {'found': False}

    def scroll_to_find_comment(self, target_text, max_scrolls=5, scroll_distance=100):
        """
        如果当前屏幕找不到，滑动寻找（旧方法 - 逐次滑动查找，作为备选方案）

        Args:
            target_text: 目标评论文本
            max_scrolls: 最多滑动次数
            scroll_distance: 每次滑动距离

        Returns:
            dict: 找到的评论信息或空字典
        """
        if self.logger:
            self.logger.info(f"📍 滑动寻找评论: {target_text[:40]}... (最多滑动 {max_scrolls} 次)")
        else:
            print(f"📍 滑动寻找评论: {target_text[:40]}... (最多滑动 {max_scrolls} 次)")

        # 获取容器
        container = self.device.device(
            resourceId=DouyinElementIds.COMMENT_LIST_CONTAINER
        )

        for scroll_idx in range(max_scrolls):
            # 尝试找到
            result = self.find_comment_by_text(target_text, timeout=2)

            if result['found']:
                if self.logger:
                    self.logger.info(f"✓ 第 {scroll_idx + 1} 次尝试找到")
                else:
                    print(f"✓ 第 {scroll_idx + 1} 次尝试找到")
                return result

            # 没找到，向上滑动
            if scroll_idx < max_scrolls - 1:
                if self.logger:
                    self.logger.debug(f"  滑动 {scroll_idx + 1}/{max_scrolls}...")
                else:
                    print(f"  滑动 {scroll_idx + 1}/{max_scrolls}...")

                # 使用和评论提取相同的滑动方式,避免触发长按菜单
                self.device.drag_comment_list(direction='up', steps=3)
                time.sleep(1)

        # 所有滑动都失败了
        if self.logger:
            self.logger.warning(f"✗ 滑动 {max_scrolls} 次后仍未找到: {target_text[:40]}...")
        else:
            print(f"✗ 滑动 {max_scrolls} 次后仍未找到: {target_text[:40]}...")

        return {'found': False}

    def set_scroll_position(self, scroll_index):
        """
        设置当前滚动位置（在评论收集结束后调用）

        Args:
            scroll_index: 当前滚动索引
        """
        self.current_scroll_index = scroll_index
        if self.logger:
            self.logger.info(f"设置当前滚动位置: scroll_index={scroll_index}")
        else:
            print(f"设置当前滚动位置: scroll_index={scroll_index}")

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

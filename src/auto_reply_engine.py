#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动回复引擎
处理评论点击、输入、发送等完整流程
"""

import time
import logging
from element_ids import DouyinElementIds


class AutoReplyEngine:
    """自动回复引擎"""

    def __init__(self, device, locator, logger=None):
        """
        初始化自动回复引擎

        Args:
            device: DeviceInteraction 实例
            locator: DynamicLocator 实例（动态定位器）
            logger: 日志对象
        """
        self.device = device
        self.locator = locator
        self.logger = logger or logging.getLogger(__name__)

    def reply_to_comment(self, comment_text, reply_text, scroll_index=None, max_retries=3):
        """
        自动回复一条评论

        核心步骤:
        1. 使用 DynamicLocator 找到评论的最新位置（精确滚动或逐次查找）
        2. 点击评论
        3. 等待回复框打开
        4. 输入回复文本
        5. 点击发送按钮

        Args:
            comment_text: 评论文本（用于定位）
            reply_text: 要回复的文本
            scroll_index: 评论的scroll_index（如果提供，使用精确滚动定位）
            max_retries: 最多重试次数

        Returns:
            dict: 回复结果 {success: bool, reason: str}
        """
        self.logger.info(f"\n🎯 开始回复评论: {comment_text[:40]}...")

        for attempt in range(max_retries):
            try:
                # 步骤 1: 动态定位评论
                self.logger.info(f"  [1/5] 定位评论... (尝试 {attempt + 1}/{max_retries})")

                # 优先使用精确滚动定位
                if scroll_index is not None:
                    self.logger.info(f"  使用精确滚动定位 (scroll_index={scroll_index})")
                    location = self.locator.scroll_to_comment_precise(
                        comment_text,
                        scroll_index
                    )
                else:
                    # 降级到逐次滑动查找
                    self.logger.info(f"  使用逐次滑动查找")
                    location = self.locator.scroll_to_find_comment(
                        comment_text,
                        max_scrolls=10
                    )

                if not location['found']:
                    self.logger.warning(f"  ✗ 找不到评论")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return {
                            'success': False,
                            'reason': '评论未找到',
                            'attempt': attempt + 1
                        }

                self.logger.info(f"  ✓ 找到评论，坐标: ({location['center_x']}, {location['center_y']})")

                # 步骤 2: 点击评论
                self.logger.info(f"  [2/5] 点击评论...")
                self.device.click(location['center_x'], location['center_y'])
                time.sleep(1.5)

                # 步骤 3: 验证回复框打开
                self.logger.info(f"  [3/5] 等待回复框打开...")
                if not self._wait_for_input_box():
                    self.logger.warning(f"  ✗ 回复框未打开")
                    if attempt < max_retries - 1:
                        # 点击其他地方关闭，然后重试
                        self.device.click(540, 800)
                        time.sleep(1)
                        continue
                    else:
                        return {
                            'success': False,
                            'reason': '回复框未打开',
                            'attempt': attempt + 1
                        }

                self.logger.info(f"  ✓ 回复框已打开")

                # 步骤 4: 输入回复文本
                self.logger.info(f"  [4/5] 输入回复文本...")
                success = self._input_reply_text(reply_text)

                if not success:
                    self.logger.warning(f"  ✗ 输入失败")
                    if attempt < max_retries - 1:
                        self.device.click(540, 800)
                        time.sleep(1)
                        continue
                    else:
                        return {
                            'success': False,
                            'reason': '输入失败',
                            'attempt': attempt + 1
                        }

                self.logger.info(f"  ✓ 文本已输入")

                # 步骤 5: 发送回复
                self.logger.info(f"  [5/5] 发送回复...")
                success = self._send_reply()

                if not success:
                    self.logger.warning(f"  ✗ 发送失败")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        return {
                            'success': False,
                            'reason': '发送失败',
                            'attempt': attempt + 1
                        }

                self.logger.info(f"  ✓ 回复已发送！")
                return {
                    'success': True,
                    'reason': '成功',
                    'attempt': attempt + 1
                }

            except Exception as e:
                self.logger.error(f"  ✗ 异常: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return {
                        'success': False,
                        'reason': f'异常: {str(e)}',
                        'attempt': attempt + 1
                    }

        return {
            'success': False,
            'reason': '达到最大重试次数',
            'attempt': max_retries
        }

    def _wait_for_input_box(self, timeout=3):
        """
        等待回复输入框出现

        Args:
            timeout: 超时时间

        Returns:
            bool: 输入框是否出现
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                input_box = self.device.device(
                    resourceId=DouyinElementIds.COMMENT_INPUT
                )

                if input_box.exists:
                    return True

                time.sleep(0.3)

            except Exception as e:
                self.logger.debug(f"检查输入框异常: {e}")
                time.sleep(0.3)

        return False

    def _input_reply_text(self, reply_text):
        """
        输入回复文本

        Args:
            reply_text: 要输入的文本

        Returns:
            bool: 是否成功
        """
        try:
            # 点击输入框
            input_box = self.device.device(
                resourceId=DouyinElementIds.COMMENT_INPUT
            )

            if input_box.exists:
                input_box.click()
                time.sleep(0.5)

            # 输入文本
            self.device.input_text(reply_text)
            time.sleep(0.5)

            return True

        except Exception as e:
            self.logger.error(f"输入文本失败: {e}")
            return False

    def _send_reply(self):
        """
        发送回复

        Returns:
            bool: 是否成功
        """
        try:
            # 点击发送按钮
            send_btn = self.device.device(
                resourceId=DouyinElementIds.SEND_TEXT_COMMENT
            )

            if send_btn.exists:
                send_btn.click()
                time.sleep(2)  # 等待发送完成
                return True
            else:
                self.logger.warning("发送按钮未找到")
                return False

        except Exception as e:
            self.logger.error(f"发送失败: {e}")
            return False

    def batch_reply(self, matched_comments, wait_between_replies=3, max_replies=None):
        """
        批量回复多条评论

        Args:
            matched_comments: 匹配的评论列表（包含scroll_index字段）
            wait_between_replies: 回复间隔（秒）
            max_replies: 最多回复条数

        Returns:
            list: 回复结果列表
        """
        results = []
        reply_count = 0

        for idx, match in enumerate(matched_comments, 1):
            # 检查是否达到最大回复数
            if max_replies and reply_count >= max_replies:
                self.logger.info(f"已达到最大回复数 ({max_replies})，停止")
                break

            comment_text = match['comment_text']
            reply_text = match['reply_text']
            scroll_index = match.get('scroll_index')  # 获取scroll_index（如果有）

            self.logger.info(f"\n[{idx}/{len(matched_comments)}] 处理评论...")

            # 执行回复 - 传递scroll_index以启用精确滚动
            result = self.reply_to_comment(
                comment_text,
                reply_text,
                scroll_index=scroll_index,
                max_retries=2
            )

            results.append({
                'comment': comment_text,
                'keyword': match['keyword'],
                'reply': reply_text,
                'scroll_index': scroll_index,
                'result': result,
            })

            if result['success']:
                reply_count += 1

            # 等待，避免被封
            if idx < len(matched_comments):
                self.logger.info(f"等待 {wait_between_replies} 秒...")
                time.sleep(wait_between_replies)

        return results

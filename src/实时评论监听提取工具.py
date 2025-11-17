#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时评论监听提取工具 v2.0
一边滑动一边动态获取评论的定位信息和文字内容
利用 ui_viewer.py 的 UI 解析能力
"""

import sys
sys.path.insert(0, '.')

import json
import time
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from device_interaction import DeviceInteraction
from element_ids import DouyinElementIds


class RealtimeCommentMonitor:
    """实时评论监听提取器"""

    def __init__(self, device):
        """
        初始化实时监听器

        Args:
            device: DeviceInteraction 实例
        """
        self.device = device
        self.output_dir = Path('./outputs')
        self.output_dir.mkdir(exist_ok=True)

        # 评论缓存（用于去重）
        self.comment_cache = {}  # key: bounds_str, value: comment_data
        self.all_comments = []   # 所有评论的完整列表

        # 配置
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    def monitor_and_extract(self, scroll_times=5, interval=1):
        """
        实时监听并提取评论

        Args:
            scroll_times: 滑动次数
            interval: 每次滑动后的等待时间（秒）

        Returns:
            list: 所有提取的评论
        """
        print("\n" + "=" * 80)
        print("🎯 实时评论监听提取开始")
        print("=" * 80 + "\n")

        try:
            # 获取容器元素
            container = self.device.device(
                resourceId=DouyinElementIds.COMMENT_LIST_CONTAINER
            )

            if not container.exists:
                print("⚠️  评论列表容器未找到")
                return []

            # 第一次提取（不滑动）
            print("📍 第 1 次: 提取当前评论...\n")
            self._extract_current_comments()

            # 滑动并提取
            for scroll_idx in range(scroll_times):
                print(f"↑ 滚动评论 {scroll_idx + 1}/{scroll_times}...", end='', flush=True)

                # 直接对评论容器元素进行滚动（最稳定的方案）
                self.device.drag_comment_list(direction='up', steps=3)

                # 等待加载
                time.sleep(interval)

                # 提取当前屏幕的评论
                print(" 提取新评论...\n")
                self._extract_current_comments()

            # 显示统计
            self._show_summary()

            return self.all_comments

        except Exception as e:
            print(f"✗ 监听失败: {e}")
            import traceback
            traceback.print_exc()
            return self.all_comments

    def _extract_current_comments(self):
        """
        提取当前屏幕上的所有评论

        使用 UI 结构解析来精确获取评论的定位信息
        """
        try:
            # 获取 UI 层级树
            xml_str = self.device.device.dump_hierarchy()
            root = ET.fromstring(xml_str)

            # 在 XML 中找所有评论元素
            comment_elements = self._find_comment_elements(root)

            if not comment_elements:
                print("  ℹ️  本次未找到新评论")
                return

            print(f"  找到 {len(comment_elements)} 条评论:")

            # 提取每条评论
            for idx, element_info in enumerate(comment_elements, 1):
                comment_data = self._parse_comment_element(element_info, idx)

                # 使用 bounds 作为 key 来判断是否是新评论
                bounds_key = comment_data['bounds_str']

                if bounds_key not in self.comment_cache:
                    self.comment_cache[bounds_key] = comment_data
                    self.all_comments.append(comment_data)

                    print(f"    ✓ 新评论 {len(self.all_comments)}: {comment_data['text'][:50]}...")
                else:
                    print(f"    ℹ️  重复评论 (已有)")

        except Exception as e:
            print(f"  ✗ 提取失败: {e}")

    def _find_comment_elements(self, root):
        """
        在 XML 树中找所有评论元素

        返回匹配 COMMENT_ITEM ID 的所有元素信息
        """
        comment_elements = []

        def search_recursive(element):
            resource_id = element.get('resource-id', '')

            # 检查是否是评论元素
            if resource_id == DouyinElementIds.COMMENT_ITEM:
                # 收集此元素的信息
                element_info = {
                    'resource_id': resource_id,
                    'text': element.get('text', ''),
                    'bounds': element.get('bounds', ''),
                    'class': element.get('class', ''),
                    'content_desc': element.get('content-desc', ''),
                    'element': element  # 保存元素引用以便后续处理
                }
                comment_elements.append(element_info)

            # 继续搜索子元素
            for child in element:
                search_recursive(child)

        search_recursive(root)
        return comment_elements

    def _parse_comment_element(self, element_info, index):
        """
        解析单条评论元素

        Args:
            element_info: 元素信息字典
            index: 评论在当前屏幕上的索引

        Returns:
            dict: 评论数据
        """
        # 解析 bounds
        bounds = self._parse_bounds(element_info['bounds'])

        # 获取文本（直接从 XML 或通过遍历子元素）
        text = element_info['text']
        if not text:
            text = self._extract_text_from_children(element_info['element'])

        # 构建评论数据
        comment_data = {
            'id': len(self.all_comments) + 1,
            'index_on_screen': index,
            'text': text,
            'length': len(text) if text else 0,
            'bounds': bounds,
            'bounds_str': element_info['bounds'],
            'class': element_info['class'],
            'content_desc': element_info['content_desc'],
            'extraction_time': datetime.now().isoformat(),
            'position': {
                'x': bounds[0] if bounds else 0,
                'y': bounds[1] if bounds else 0,
                'width': (bounds[2] - bounds[0]) if bounds else 0,
                'height': (bounds[3] - bounds[1]) if bounds else 0,
                'center_x': ((bounds[0] + bounds[2]) // 2) if bounds else 0,
                'center_y': ((bounds[1] + bounds[3]) // 2) if bounds else 0,
            } if bounds else None
        }

        # 解析评论内容
        if text:
            parts = self._extract_comment_parts(text)
            comment_data.update(parts)
        else:
            comment_data['comment_content'] = ''
            comment_data['time'] = ''
            comment_data['location'] = ''
            comment_data['emoji_count'] = 0
            comment_data['has_reply'] = False
            comment_data['author_replied'] = False

        return comment_data

    def _extract_text_from_children(self, element):
        """从元素的子元素中递归提取所有文本"""
        text_parts = []

        if element.text:
            text_parts.append(element.text)

        for child in element:
            child_text = self._extract_text_from_children(child)
            if child_text:
                text_parts.append(child_text)

            if child.tail:
                text_parts.append(child.tail)

        return ''.join(text_parts).strip()

    def _extract_comment_parts(self, comment_text):
        """
        解析评论内容的各个部分

        示例: "太Zh子,博主你发，天天发。百看不腻[看][看],11-05, · 澳大利亚,回复 按钮,作者回复过"
        """
        parts = {
            'comment_content': '',
            'time': '',
            'location': '',
            'emoji_count': 0,
            'has_reply': False,
            'author_replied': False,
        }

        text = comment_text.strip()

        # 检测是否有"回复"和"作者回复过"
        parts['has_reply'] = '回复' in text
        parts['author_replied'] = '作者回复过' in text

        # 计算 emoji 数量
        emoji_pattern = r'\[[\u4e00-\u9fff]+\]'
        emoji_matches = re.findall(emoji_pattern, text)
        parts['emoji_count'] = len(emoji_matches)

        # 移除 emoji
        text_without_emoji = re.sub(emoji_pattern, '', text)

        # 提取时间 (MM-DD 格式)
        time_pattern = r'(\d{1,2}-\d{1,2})'
        time_match = re.search(time_pattern, text_without_emoji)
        if time_match:
            parts['time'] = time_match.group(1)
            text_without_emoji = re.sub(time_pattern, '', text_without_emoji)

        # 提取地点
        location_pattern = r'·\s*([^\s,，\|]+)'
        location_match = re.search(location_pattern, text_without_emoji)
        if location_match:
            parts['location'] = location_match.group(1).strip('，, ')
            text_without_emoji = re.sub(location_pattern, '', text_without_emoji)

        # 移除标记
        text_cleaned = re.sub(r'(回复\s*按钮|作者回复过)', '', text_without_emoji)
        text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()

        parts['comment_content'] = text_cleaned

        return parts

    def _parse_bounds(self, bounds_str):
        """解析 bounds 字符串"""
        try:
            match = re.findall(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match[0])
                return (x1, y1, x2, y2)
        except:
            pass
        return None

    def save_to_json(self, filename=None):
        """
        保存评论为 JSON

        Args:
            filename: 文件名（可选）

        Returns:
            str: 保存的文件路径
        """
        if not filename:
            filename = f'comments_realtime_{self.timestamp}.json'

        filepath = self.output_dir / filename

        try:
            output = {
                'metadata': {
                    'total': len(self.all_comments),
                    'extraction_time': datetime.now().isoformat(),
                    'timestamp': self.timestamp,
                },
                'comments': self.all_comments
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            print(f"\n✓ 已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"\n✗ 保存失败: {e}")
            return None

    def export_csv(self, filename=None):
        """
        导出为 CSV 格式

        Args:
            filename: 文件名（可选）

        Returns:
            str: 保存的文件路径
        """
        if not filename:
            filename = f'comments_realtime_{self.timestamp}.csv'

        filepath = self.output_dir / filename

        try:
            import csv

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)

                # 写入表头
                writer.writerow([
                    '序号', '文本', '内容', '时间', '地点', 'Emoji数',
                    '有回复', '作者回复', '位置X', '位置Y', '宽度', '高度'
                ])

                # 写入数据
                for comment in self.all_comments:
                    writer.writerow([
                        comment['id'],
                        comment['text'],
                        comment.get('comment_content', ''),
                        comment.get('time', ''),
                        comment.get('location', ''),
                        comment.get('emoji_count', 0),
                        '是' if comment.get('has_reply') else '否',
                        '是' if comment.get('author_replied') else '否',
                        comment['position']['x'] if comment['position'] else '',
                        comment['position']['y'] if comment['position'] else '',
                        comment['position']['width'] if comment['position'] else '',
                        comment['position']['height'] if comment['position'] else '',
                    ])

            print(f"✓ 已导出 CSV: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"✗ 导出 CSV 失败: {e}")
            return None

    def _show_summary(self):
        """显示统计摘要"""
        print("\n" + "=" * 80)
        print("📊 评论提取统计")
        print("=" * 80)

        if not self.all_comments:
            print("⚠️  未提取到任何评论")
            return

        print(f"总数: {len(self.all_comments)} 条\n")

        # 基础统计
        total_length = sum(c.get('length', 0) for c in self.all_comments)
        avg_length = total_length / len(self.all_comments) if self.all_comments else 0

        print(f"文本信息:")
        print(f"  - 平均长度: {int(avg_length)} 字")
        print(f"  - 总字数: {total_length} 字\n")

        # emoji 统计
        with_emoji = sum(1 for c in self.all_comments if c.get('emoji_count', 0) > 0)
        total_emoji = sum(c.get('emoji_count', 0) for c in self.all_comments)
        print(f"表情统计:")
        print(f"  - 包含表情的评论: {with_emoji} 条")
        print(f"  - 总表情数: {total_emoji} 个\n")

        # 回复统计
        with_reply = sum(1 for c in self.all_comments if c.get('has_reply'))
        author_replied = sum(1 for c in self.all_comments if c.get('author_replied'))
        print(f"交互统计:")
        print(f"  - 有回复按钮: {with_reply} 条")
        print(f"  - 作者已回复: {author_replied} 条\n")

        # 时间统计
        with_time = sum(1 for c in self.all_comments if c.get('time'))
        print(f"时间统计:")
        print(f"  - 有发布时间: {with_time} 条\n")

        # 地点统计
        with_location = sum(1 for c in self.all_comments if c.get('location'))
        print(f"地点统计:")
        print(f"  - 有地点信息: {with_location} 条\n")

        # 位置统计
        print(f"屏幕位置统计:")
        if self.all_comments[0].get('position'):
            top_y = min(c['position']['y'] for c in self.all_comments if c.get('position'))
            bottom_y = max(c['position']['y'] + c['position']['height']
                          for c in self.all_comments if c.get('position'))
            print(f"  - Y轴范围: {top_y} - {bottom_y}\n")

        print("=" * 80)

    def display_comments_table(self, max_rows=10):
        """以表格形式显示评论"""
        if not self.all_comments:
            print("⚠️  没有评论数据")
            return

        print("\n" + "=" * 120)
        print("📋 评论表格")
        print("=" * 120)

        # 表头
        print(f"{'序号':<5} | {'文本':<40} | {'时间':<6} | {'地点':<8} | {'位置':<20} | {'Emoji':<5}")
        print("-" * 120)

        # 数据行
        for comment in self.all_comments[:max_rows]:
            text = comment['text'][:40] if comment['text'] else '(空)'
            time_str = comment.get('time', '-')
            location = comment.get('location', '-')[:6]
            pos_str = f"({comment['position']['center_x']},{comment['position']['center_y']})" \
                     if comment.get('position') else '-'
            emoji_count = comment.get('emoji_count', 0)

            print(f"{comment['id']:<5} | {text:<40} | {time_str:<6} | {location:<8} | {pos_str:<20} | {emoji_count:<5}")

        if len(self.all_comments) > max_rows:
            print(f"\n... 还有 {len(self.all_comments) - max_rows} 条评论 ...\n")

        print("=" * 120)


def main():
    print("\n" + "=" * 80)
    print("🎯 实时评论监听提取工具 v2.0")
    print("一边滑动一边动态获取评论的定位和文字")
    print("=" * 80)

    try:
        # 连接设备
        print("\n1️⃣  连接设备...")
        device = DeviceInteraction(timeout=10)
        print("✓ 设备已连接\n")

        # 创建监听器
        monitor = RealtimeCommentMonitor(device)

        # 配置参数
        print("2️⃣  配置监听参数...")
        scroll_times_str = input("请输入滑动次数 (默认 5): ").strip()
        scroll_times = int(scroll_times_str) if scroll_times_str.isdigit() else 5

        interval_str = input("请输入每次滑动后的等待时间-秒 (默认 1): ").strip()
        interval = float(interval_str) if interval_str else 1

        # 开始监听和提取
        print("\n3️⃣  开始实时监听提取...\n")
        comments = monitor.monitor_and_extract(scroll_times=scroll_times, interval=interval)

        # 显示结果
        if comments:
            # 显示表格
            monitor.display_comments_table(max_rows=15)

            # 保存选项
            print("\n4️⃣  保存数据...\n")
            print("选择保存格式:")
            print("1. JSON (推荐)")
            print("2. CSV")
            print("3. 两者都保存")
            print("4. 不保存")

            choice = input("\n请选择 (1-4): ").strip()

            if choice in ['1', '3']:
                monitor.save_to_json()
            if choice in ['2', '3']:
                monitor.export_csv()

            print("\n✅ 完成！")
        else:
            print("⚠️  未提取到任何评论")

        device.close()

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

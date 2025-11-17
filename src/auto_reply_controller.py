#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动回复系统主控制器
整合关键字匹配、动态定位、自动回复等所有模块
"""

import sys
sys.path.insert(0, '.')

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from device_interaction import DeviceInteraction
from element_ids import DouyinElementIds
from keyword_matcher import KeywordMatcher
from dynamic_locator import DynamicLocator
from auto_reply_engine import AutoReplyEngine
from 实时评论监听提取工具 import RealtimeCommentMonitor


class AutoReplyController:
    """自动回复系统主控制器"""

    def __init__(self, device, logger=None):
        """
        初始化主控制器

        Args:
            device: DeviceInteraction 实例
            logger: 日志对象
        """
        self.device = device
        self.logger = logger or self._setup_logger()

        # 初始化各个模块
        self.comment_monitor = RealtimeCommentMonitor(device)
        self.keyword_matcher = KeywordMatcher()
        self.locator = DynamicLocator(device, self.logger)
        self.reply_engine = AutoReplyEngine(device, self.locator, self.logger)

        # 输出目录
        self.output_dir = Path('./outputs')
        self.output_dir.mkdir(exist_ok=True)

        # 统计信息
        self.stats = {
            'total_comments': 0,
            'matched_comments': 0,
            'successful_replies': 0,
            'failed_replies': 0,
            'start_time': None,
            'end_time': None,
        }

    def _setup_logger(self):
        """设置日志"""
        logger = logging.getLogger('AutoReplySystem')
        logger.setLevel(logging.INFO)

        # 文件处理器
        log_file = f'logs/auto_reply_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        Path('logs').mkdir(exist_ok=True)

        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)

        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def run_complete_workflow(self, scroll_times=5, max_replies=None, keywords_file=None):
        """
        运行完整的自动回复工作流

        步骤:
        1. 收集评论
        2. 匹配关键字
        3. 自动回复
        4. 生成报告

        Args:
            scroll_times: 滑动加载评论的次数
            max_replies: 最多回复条数
            keywords_file: 关键字配置文件

        Returns:
            dict: 完整的工作流结果
        """
        self.stats['start_time'] = datetime.now().isoformat()

        print("\n" + "=" * 80)
        print("🎯 自动回复系统 - 完整工作流")
        print("=" * 80 + "\n")

        try:
            # 步骤 1: 收集评论
            self.logger.info("=" * 80)
            self.logger.info("步骤 1: 收集评论")
            self.logger.info("=" * 80)

            comments = self._collect_comments(scroll_times)

            if not comments:
                self.logger.warning("未收集到任何评论，退出")
                return {'success': False, 'reason': '未收集到评论'}

            self.stats['total_comments'] = len(comments)

            # 步骤 2: 匹配关键字
            self.logger.info("\n" + "=" * 80)
            self.logger.info("步骤 2: 匹配关键字")
            self.logger.info("=" * 80)

            matched = self._match_keywords(comments, keywords_file)

            if not matched:
                self.logger.warning("未匹配到任何评论，退出")
                return {'success': False, 'reason': '未匹配到评论'}

            self.stats['matched_comments'] = len(matched)

            # 步骤 3: 自动回复
            self.logger.info("\n" + "=" * 80)
            self.logger.info("步骤 3: 自动回复")
            self.logger.info("=" * 80)

            reply_results = self._execute_replies(matched, max_replies)

            # 统计回复结果
            for result in reply_results:
                if result['result']['success']:
                    self.stats['successful_replies'] += 1
                else:
                    self.stats['failed_replies'] += 1

            # 步骤 4: 生成报告
            self.logger.info("\n" + "=" * 80)
            self.logger.info("步骤 4: 生成报告")
            self.logger.info("=" * 80)

            report = self._generate_report(reply_results)

            self.stats['end_time'] = datetime.now().isoformat()

            # 显示统计
            self._show_statistics()

            return {
                'success': True,
                'stats': self.stats,
                'report': report,
                'results': reply_results,
            }

        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'reason': str(e)}

    def _collect_comments(self, scroll_times):
        """收集评论"""
        self.logger.info(f"开始收集评论 (滑动 {scroll_times} 次)...")

        comments = self.comment_monitor.monitor_and_extract(
            scroll_times=scroll_times,
            interval=1
        )

        self.logger.info(f"✓ 收集完成，共 {len(comments)} 条评论")

        # 保存评论
        comments_file = self.output_dir / f'comments_collected_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(comments_file, 'w', encoding='utf-8') as f:
            json.dump({'total': len(comments), 'comments': comments}, f, ensure_ascii=False, indent=2)

        self.logger.info(f"评论已保存: {comments_file}")

        return comments

    def _match_keywords(self, comments, keywords_file=None):
        """匹配关键字"""
        self.logger.info("开始关键字匹配...")

        # 加载关键字配置
        if keywords_file:
            self.keyword_matcher = KeywordMatcher(keywords_file=keywords_file)
        else:
            self.keyword_matcher = KeywordMatcher()

        keywords = self.keyword_matcher.get_keywords()
        self.logger.info(f"已加载 {len(keywords)} 个关键字: {keywords}")

        # 匹配评论
        matched = self.keyword_matcher.match_comments(comments)

        self.logger.info(f"✓ 匹配完成，共 {len(matched)} 条评论匹配成功")

        # 显示匹配结果
        for idx, match in enumerate(matched[:5], 1):
            self.logger.info(f"  {idx}. 关键字: {match['keyword']}, 评论: {match['comment_text'][:40]}...")

        if len(matched) > 5:
            self.logger.info(f"  ... 还有 {len(matched) - 5} 条评论 ...")

        return matched

    def _execute_replies(self, matched, max_replies=None):
        """执行自动回复（已优化：支持滑动位置跟踪）"""
        self.logger.info(f"开始自动回复 (最多 {max_replies or '无限'} 条)...")

        # 🔑 获取当前滑动信息
        scroll_info = self.comment_monitor.get_scroll_info()
        current_offset = scroll_info['current_offset']

        self.logger.info(f"当前评论列表滑动偏移: {current_offset}")
        self.logger.info("开始逐个定位并回复评论...")

        # 传递滑动偏移信息给回复引擎
        results = self.reply_engine.batch_reply(
            matched,
            current_list_offset=current_offset,  # 🔑 传递当前偏移
            wait_between_replies=3,
            max_replies=max_replies
        )

        return results

    def _generate_report(self, reply_results):
        """生成报告"""
        self.logger.info("生成报告...")

        report = {
            'generation_time': datetime.now().isoformat(),
            'total_attempts': len(reply_results),
            'successful': sum(1 for r in reply_results if r['result']['success']),
            'failed': sum(1 for r in reply_results if not r['result']['success']),
            'results': reply_results,
        }

        # 保存报告
        report_file = self.output_dir / f'reply_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info(f"报告已保存: {report_file}")

        return report

    def _show_statistics(self):
        """显示统计信息"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 统计信息")
        self.logger.info("=" * 80)

        self.logger.info(f"总评论数: {self.stats['total_comments']} 条")
        self.logger.info(f"匹配评论: {self.stats['matched_comments']} 条")
        self.logger.info(f"成功回复: {self.stats['successful_replies']} 条")
        self.logger.info(f"失败回复: {self.stats['failed_replies']} 条")

        if self.stats['matched_comments'] > 0:
            success_rate = (self.stats['successful_replies'] / self.stats['matched_comments']) * 100
            self.logger.info(f"成功率: {success_rate:.1f}%")

        self.logger.info("=" * 80)


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🎯 抖音自动回复系统 v1.0")
    print("=" * 80 + "\n")

    try:
        # 1. 连接设备
        print("1️⃣  连接设备...")
        device = DeviceInteraction(timeout=10)
        print("✓ 设备已连接\n")

        # 2. 创建控制器
        controller = AutoReplyController(device)

        # 3. 获取参数
        print("2️⃣  配置参数...\n")

        scroll_times_str = input("请输入滑动次数加载评论 (默认 5): ").strip()
        scroll_times = int(scroll_times_str) if scroll_times_str.isdigit() else 5

        max_replies_str = input("请输入最多回复条数 (默认无限): ").strip()
        max_replies = int(max_replies_str) if max_replies_str.isdigit() else None

        keywords_file_str = input("请输入关键字配置文件路径 (默认使用内置): ").strip()
        keywords_file = keywords_file_str if keywords_file_str and Path(keywords_file_str).exists() else None

        # 4. 运行工作流
        print("\n3️⃣  开始工作流...\n")

        result = controller.run_complete_workflow(
            scroll_times=scroll_times,
            max_replies=max_replies,
            keywords_file=keywords_file
        )

        # 5. 显示结果
        if result['success']:
            print("\n✅ 工作流完成！\n")
            stats = result['stats']
            print(f"总评论数: {stats['total_comments']}")
            print(f"成功回复: {stats['successful_replies']}")
            print(f"失败回复: {stats['failed_replies']}")
        else:
            print(f"\n⚠️  工作流失败: {result['reason']}")

        device.close()

    except KeyboardInterrupt:
        print("\n\n用户中断")
        return 1
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

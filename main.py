#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抖音自动回复系统 - 主程序
功能：输入视频链接 → 打开浏览器 → 图像识别点击"打开" → 进入抖音 → 点击评论 → 获取评论 → 筛选评论 → 自动回复
"""

import sys
import json
import time
import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

from src.device_interaction import DeviceInteraction
from src.auto_reply_controller import AutoReplyController
from src.element_ids import DouyinElementIds

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/auto_reply_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutoReplyMain')


def show_default_keywords():
    """显示默认关键词"""
    default_keywords = {
        '点赞': '感谢点赞！🙏',
        '支持': '感谢支持，继续加油！💪',
        '棒': '感谢评价！😊',
        '👍': '谢谢！💕',
        '顶': '感谢支持！🎉',
        '很有意思': '哈哈，感谢喜欢！😄',
        '非常好': '感谢评论！✨',
        '推荐': '感谢推荐！🙏',
        '赞': '感谢点赞！',
        '加油': '谢谢鼓励，继续加油！💪'
    }

    print("\n📋 默认关键词 (10 个):")
    print("=" * 60)
    for i, (keyword, reply) in enumerate(default_keywords.items(), 1):
        print(f"{i:2d}. {keyword:15s} → {reply}")
    print("=" * 60)

    return default_keywords


def custom_keywords():
    """自定义关键词"""
    keywords_dict = {}
    idx = 1

    while True:
        user_input = input(f"{idx}. 请输入 (或按 Enter 完成): ").strip()

        if not user_input:
            # 如果第一次就按 Enter，表示不使用关键词筛选
            if idx == 1 and not keywords_dict:
                return {}  # 返回空字典，表示随机模式
            break

        if '|' not in user_input:
            print("❌ 格式错误，请用 | 分隔，例如: 点赞|感谢点赞")
            continue

        keyword, reply = user_input.split('|', 1)
        keyword = keyword.strip()
        reply = reply.strip()

        if not keyword or not reply:
            print("❌ 关键词和回复都不能为空")
            continue

        keywords_dict[keyword] = reply
        print(f"   ✓ 已添加: {keyword} → {reply}")
        idx += 1

    if keywords_dict:
        print(f"\n✅ 共添加 {len(keywords_dict)} 个关键词")

    return keywords_dict


def open_video_by_url(video_url, device):
    """
    通过分享链接打开视频
    流程：视频链接 → 浏览器 → 图像识别点击"打开" → 抖音应用
    """
    print("\n步骤 2️⃣ : 打开视频链接...\n")
    print(f"  链接: {video_url}\n")
    logger.info(f"打开视频链接: {video_url}")

    try:
        # 步骤 1: 使用 adb 打开链接（会自动打开浏览器）
        print("  1. 使用 adb 打开链接...")
        subprocess.run(
            ['adb', 'shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', video_url],
            check=True,
            timeout=10
        )

        # 等待浏览器加载页面
        print("  2. 等待浏览器加载页面...")
        time.sleep(2)

        # 步骤 2: 点击谷歌浏览器中的"打开"按钮（使用图像识别）
        print("  3. 使用图像识别点击\"打开\"按钮...")

        # 查找图像模板
        template_dir = "templates"
        template_paths = [
            os.path.join(template_dir, "dakaidouyin.png"),
            os.path.join(template_dir, "dakaiyouyin2.png"),
        ]

        # 检查模板文件是否存在
        valid_templates = [t for t in template_paths if os.path.exists(t)]
        if not valid_templates:
            print(f"  ⚠️  未找到图像模板文件:")
            for t in template_paths:
                print(f"     {t}")
            print("  ℹ️  将跳过图像识别，请手动点击\"打开\"按钮\n")
            input("点击\"打开\"按钮后按 Enter 继续...")
            return True

        # 使用图像识别定位并点击按钮
        print(f"  📸 使用 {len(valid_templates)} 个模板进行图像识别...")
        if device.find_button_by_image(valid_templates, timeout=10, threshold=0.7):
            print("  ✓ 已点击\"打开\"按钮\n")
            logger.info("成功点击\"打开\"按钮")
            time.sleep(2)
        else:
            print("  ⚠️  未找到\"打开\"按钮，请手动点击\n")
            input("点击\"打开\"按钮后按 Enter 继续...")

        # 步骤 3: 等待抖音应用加载视频页面
        print("  4. 等待抖音应用加载视频...")
        for attempt in range(5):
            time.sleep(2)
            # 检查是否在视频页面（查找评论按钮）
            comment_btn = device.device(resourceId=DouyinElementIds.COMMENT_BUTTON)
            if comment_btn.exists:
                print("  ✓ 视频页面已加载\n")
                logger.info("视频页面加载成功")
                return True

            print(f"     尝试 {attempt + 1}/5: 页面还未加载...")

        print("  ⚠️  视频页面加载超时，请确认是否已进入视频\n")
        input("进入视频后按 Enter 继续...")
        return True

    except subprocess.TimeoutExpired:
        print("  ✗ 打开链接超时\n")
        logger.error("打开链接超时")
        return False
    except Exception as e:
        print(f"  ✗ 打开链接失败: {e}\n")
        logger.error(f"打开链接失败: {e}")
        return False


def open_comment_section(device):
    """打开评论区 - 核心功能"""
    print("\n步骤 3️⃣ : 打开评论区...\n")
    logger.info("打开评论区...")

    try:
        # 方法 1: 尝试点击评论按钮
        print("  方法 1: 尝试点击评论按钮...")
        comment_btn = device.device(resourceId=DouyinElementIds.COMMENT_BUTTON)

        if comment_btn.exists:
            print("    ✓ 找到评论按钮，点击中...")
            comment_btn.click()
            time.sleep(2)

            # 验证评论区是否打开
            container = device.device(resourceId=DouyinElementIds.COMMENT_LIST_CONTAINER)
            if container.exists:
                print("  ✓ 评论区已打开\n")
                logger.info("评论区已打开 (方法1)")
                return True

        # 方法 2: 尝试点击评论数文本
        print("  方法 2: 尝试点击评论数文本...")
        comment_count = device.device(resourceId=DouyinElementIds.COMMENT_COUNT_TEXT)

        if comment_count.exists:
            print("    ✓ 找到评论数文本，点击中...")
            comment_count.click()
            time.sleep(2)

            container = device.device(resourceId=DouyinElementIds.COMMENT_LIST_CONTAINER)
            if container.exists:
                print("  ✓ 评论区已打开\n")
                logger.info("评论区已打开 (方法2)")
                return True

        # 方法 3: 检查评论容器是否已存在
        print("  方法 3: 检查评论容器是否已存在...")
        container = device.device(resourceId=DouyinElementIds.COMMENT_LIST_CONTAINER)

        if container.exists:
            print("    ✓ 评论容器已存在")
            print("  ✓ 评论区已打开\n")
            logger.info("评论区已打开 (方法3)")
            return True

        print("⚠️  无法打开评论区 - 三种方法都未成功\n")
        print("  💡 可能的原因:")
        print("     • 视频页面未完全加载")
        print("     • 需要手动打开评论区\n")

        logger.warning("无法打开评论区，所有方法都失败")
        return False

    except Exception as e:
        print(f"✗ 打开评论区异常: {e}\n")
        logger.error(f"打开评论区异常: {e}", exc_info=True)
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🚀 抖音自动回复系统")
    print("=" * 80)

    print("\n功能流程：")
    print("  1. 输入视频链接（或跳过，直接使用已打开的视频）")
    print("  2. 自动打开抖音应用")
    print("  3. 点击评论按钮，打开评论区")
    print("  4. 加载评论列表")
    print("  5. 筛选匹配关键词的评论")
    print("  6. 自动回复匹配的评论\n")

    # 步骤 1: 获取视频链接（可选）
    print("=" * 80)
    print("📹 步骤 1: 视频链接")
    print("=" * 80)
    video_url = input("\n请输入抖音视频分享链接 (按 Enter 跳过，使用已打开的视频): ").strip()

    if video_url:
        print(f"✓ 将通过链接打开视频\n")
    else:
        print("✓ 将使用当前已打开的视频\n")

    # 步骤 2: 关键词设置
    print("\n" + "=" * 80)
    print("🔑 步骤 2: 关键词设置")
    print("=" * 80)
    print("\n请输入关键词进行筛选回复:")
    print("格式: 关键词|回复文本 (用 | 分隔)")
    print("直接按 Enter 跳过 = 随机回复任意3条评论\n")

    keywords = custom_keywords()

    # 如果用户没有输入关键词，设置为空字典（随机模式）
    if not keywords:
        print("\n✓ 将随机回复 3 条评论（不筛选关键词）\n")
        keywords = {}

    # 步骤 3: 配置参数
    print("\n" + "=" * 80)
    print("⚙️  步骤 3: 运行参数")
    print("=" * 80)

    scroll_str = input("\n滑动次数加载评论 (默认 5 次): ").strip()
    scroll_times = int(scroll_str) if scroll_str.isdigit() else 5

    # 如果是随机模式（没有关键词），固定回复3条
    if not keywords:
        max_replies = 3
        print("随机模式: 固定回复 3 条评论")
    else:
        max_str = input("最多回复条数 (默认 20 条): ").strip()
        max_replies = int(max_str) if max_str.isdigit() else 20

    # 步骤 4: 确认配置
    print("\n" + "=" * 80)
    print("✅ 配置确认")
    print("=" * 80)
    print(f"\n视频链接: {video_url or '使用当前视频'}")

    if keywords:
        print(f"关键词数量: {len(keywords)} 个")
        print(f"滑动次数: {scroll_times} 次")
        print(f"最多回复: {max_replies} 条")
        print(f"预期加载评论: {scroll_times * 8}-{scroll_times * 10} 条\n")

        print("关键词列表:")
        for i, (keyword, reply) in enumerate(list(keywords.items())[:5], 1):
            print(f"  {i}. {keyword:15s} → {reply}")
        if len(keywords) > 5:
            print(f"  ... 还有 {len(keywords) - 5} 个关键词 ...")
    else:
        print(f"模式: 随机回复")
        print(f"滑动次数: {scroll_times} 次")
        print(f"回复数量: {max_replies} 条 (随机选择)")
        print(f"预期加载评论: {scroll_times * 8}-{scroll_times * 10} 条")

    print("\n" + "=" * 80)
    confirm = input("确认开始运行？(y/n, 默认 y): ").strip().lower() or 'y'

    if confirm != 'y':
        print("❌ 已取消")
        return 1

    # 保存配置
    config = {
        "keywords": keywords,
        "max_replies": max_replies,
        "scroll_times": scroll_times
    }

    config_file = Path('./outputs/config.json')
    config_file.parent.mkdir(exist_ok=True)

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 配置已保存: {config_file}")

    # 步骤 5: 开始运行
    try:
        print("\n" + "=" * 80)
        print("🎯 开始自动回复")
        print("=" * 80 + "\n")

        # 步骤 1: 连接设备
        print("步骤 1️⃣ : 连接设备...")
        device = DeviceInteraction(timeout=10)
        print("✓ 设备已连接\n")

        # 步骤 2: 打开视频 (如果有链接)
        if video_url:
            if not open_video_by_url(video_url, device):
                print("⚠️  视频打开失败，程序退出")
                return 1

        # 步骤 3: 打开评论区 (关键步骤！)
        if not open_comment_section(device):
            print("⚠️  评论区未打开，请手动打开评论区")
            input("打开评论区后按 Enter 继续...\n")

        # 创建控制器
        controller = AutoReplyController(device)

        # 步骤 4: 运行自动回复工作流
        print("步骤 4️⃣ : 开始自动回复工作流...\n")
        result = controller.run_complete_workflow(
            scroll_times=scroll_times,
            max_replies=max_replies,
            keywords_file=str(config_file)
        )

        # 显示结果
        if result['success']:
            print("\n✅ 完成！\n")
            stats = result.get('stats', {})
            print(f"📊 统计:")
            print(f"  • 总评论数: {stats.get('total_comments', 0)} 条")
            print(f"  • 匹配评论: {stats.get('matched_comments', 0)} 条")
            print(f"  • 成功回复: {stats.get('successful_replies', 0)} 条")
            print(f"  • 失败回复: {stats.get('failed_replies', 0)} 条")

            if stats.get('matched_comments', 0) > 0:
                success_rate = (stats.get('successful_replies', 0) / stats.get('matched_comments', 0)) * 100
                print(f"  • 成功率: {success_rate:.1f}%")

            print("\n" + "=" * 80 + "\n")
            return 0
        else:
            print(f"\n⚠️  失败: {result.get('reason', '未知错误')}\n")
            return 1

    except KeyboardInterrupt:
        print("\n\n⏸️  用户中断\n")
        return 1
    except Exception as e:
        print(f"\n✗ 错误: {e}\n")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'device' in locals():
            device.close()


if __name__ == "__main__":
    sys.exit(main())

# 模块开发指南

## 📋 目录

1. [VideoNavigator - 视频导航模块](#1-videonavigator---视频导航模块)
2. [CommentManager - 评论管理模块](#2-commentmanager---评论管理模块)
3. [ReplyHandler - 回复处理模块](#3-replyhandler---回复处理模块)
4. [Utils - 工具函数](#4-utils---工具函数)
5. [Main - 主程序](#5-main---主程序)

---

## 1. VideoNavigator - 视频导航模块

**文件**: `video_navigator.py`

**职责**: 管理视频的搜索、打开和页面检测

### 1.1 类结构

```python
class VideoNavigator:
    """视频导航管理器"""

    def __init__(self, device_interaction, logger=None):
        """
        初始化视频导航器

        Args:
            device_interaction: DeviceInteraction 实例
            logger: 日志对象
        """
        self.device = device_interaction
        self.logger = logger or logging.getLogger(__name__)
        self.current_page = None  # 当前页面状态缓存

    # ==================== 页面检测 ====================

    def detect_current_page(self):
        """
        检测当前页面类型

        Returns:
            str: 页面类型
                - 'home': 首页 (推荐流)
                - 'video': 视频详情页
                - 'user': 用户主页
                - 'live': 直播间
                - 'unknown': 未知页面
        """
        from element_ids import DouyinElementIds

        # 方案：按优先级检测页面特征

        # 1. 检测是否在直播间
        if self._is_in_live_room():
            self.current_page = 'live'
            return 'live'

        # 2. 检测是否在用户主页
        if self._is_in_user_page():
            self.current_page = 'user'
            return 'user'

        # 3. 检测是否在视频页面
        if self._is_in_video_page():
            self.current_page = 'video'
            return 'video'

        # 4. 检测是否在首页
        if self._is_in_home_page():
            self.current_page = 'home'
            return 'home'

        # 5. 未知页面
        self.current_page = 'unknown'
        self.logger.warning("⚠️  无法识别当前页面")
        return 'unknown'

    def _is_in_home_page(self):
        """检测是否在首页"""
        from element_ids import DouyinElementIds

        # 首页必须同时具备：
        # 1. 顶部导航栏
        # 2. 关注按钮
        # 3. 底部导航栏

        has_top_nav = self.device.wait_element(
            DouyinElementIds.HOMEPAGE_TOP_NAV, timeout=1
        )
        has_follow_btn = self.device.wait_element(
            DouyinElementIds.HOMEPAGE_FOLLOW_BUTTON, timeout=1
        )
        has_bottom_nav = self.device.wait_element(
            DouyinElementIds.BOTTOM_NAV_HOME, timeout=1
        )

        return has_top_nav and has_follow_btn and has_bottom_nav

    def _is_in_video_page(self):
        """检测是否在视频页面"""
        from element_ids import DouyinElementIds

        # 视频页面的特征：
        # 1. 能看到点赞按钮
        # 2. 能看到评论按钮
        # 3. 看不到底部导航栏（与首页区别）

        has_like_btn = self.device.wait_element(
            DouyinElementIds.LIKE_BUTTON, timeout=1
        )
        has_comment_btn = self.device.wait_element(
            DouyinElementIds.COMMENT_BUTTON, timeout=1
        )
        no_bottom_nav = not self.device.wait_element(
            DouyinElementIds.BOTTOM_NAV_HOME, timeout=1
        )

        return has_like_btn and has_comment_btn and no_bottom_nav

    def _is_in_user_page(self):
        """检测是否在用户主页"""
        from element_ids import DouyinElementIds

        # 用户主页的特征：
        # 1. 能看到用户头像
        # 2. 能看到用户名
        # 3. 能看到关注按钮

        has_avatar = self.device.wait_element(
            DouyinElementIds.USER_PAGE_AVATAR, timeout=1
        )
        has_name = self.device.wait_element(
            DouyinElementIds.USER_PAGE_NAME, timeout=1
        )
        has_follow_btn = self.device.wait_element(
            DouyinElementIds.USER_PAGE_FOLLOW_BUTTON, timeout=1
        )

        return has_avatar and has_name and has_follow_btn

    def _is_in_live_room(self):
        """检测是否在直播间"""
        from element_ids import DouyinElementIds

        return self.device.wait_element(
            DouyinElementIds.LIVE_ROOM_INDICATOR, timeout=1
        )

    # ==================== 导航操作 ====================

    def go_to_home(self):
        """
        返回到首页

        Returns:
            bool: 是否成功返回首页
        """
        from element_ids import DouyinElementIds
        import time

        self.logger.info("🏠 正在返回首页...")

        max_retries = 3
        for retry in range(max_retries):
            current_page = self.detect_current_page()

            if current_page == 'home':
                self.logger.info("✓ 已在首页")
                return True

            # 点击底部导航的首页按钮
            if self.device.click_element(DouyinElementIds.BOTTOM_NAV_HOME):
                time.sleep(1)
                if self.detect_current_page() == 'home':
                    self.logger.info("✓ 成功返回首页")
                    return True

            # 如果失败，尝试返回键
            if retry == max_retries - 1:
                self.device.device.press('back')
                time.sleep(1)

        self.logger.error("✗ 返回首页失败")
        return False

    def search_video_by_keyword(self, keyword):
        """
        通过关键字搜索视频

        Args:
            keyword: 搜索关键字

        Returns:
            bool: 是否成功找到并打开视频
        """
        from element_ids import DouyinElementIds
        import time

        self.logger.info(f"🔍 正在搜索视频: {keyword}")

        # 步骤 1: 确保在首页
        if not self.go_to_home():
            self.logger.error("✗ 无法返回首页")
            return False

        time.sleep(1)

        # 步骤 2: 点击搜索按钮
        if not self.device.click_element(DouyinElementIds.SEARCH_BUTTON):
            self.logger.error("✗ 点击搜索按钮失败")
            return False

        time.sleep(0.5)

        # 步骤 3: 输入搜索关键字
        if not self.device.input_text(DouyinElementIds.SEARCH_INPUT, keyword):
            self.logger.error(f"✗ 输入搜索关键字失败: {keyword}")
            return False

        time.sleep(0.5)

        # 步骤 4: 点击搜索确认
        if not self.device.click_element(DouyinElementIds.SEARCH_CONFIRM):
            self.logger.error("✗ 点击搜索确认失败")
            return False

        # 步骤 5: 等待搜索结果加载
        if not self.device.wait_element(
            DouyinElementIds.SEARCH_RESULT_TEXT_ELEMENT, timeout=15
        ):
            self.logger.error("✗ 搜索结果加载超时")
            return False

        time.sleep(1)

        # 步骤 6: 点击第一个搜索结果
        try:
            # 获取第一个结果元素
            result_element = self.device.get_element(
                DouyinElementIds.SEARCH_RESULT_TEXT_ELEMENT
            )
            if result_element:
                result_element.click()
                self.logger.info(f"✓ 点击搜索结果")
            else:
                self.logger.error("✗ 找不到搜索结果")
                return False
        except Exception as e:
            self.logger.error(f"✗ 点击搜索结果失败: {e}")
            return False

        # 步骤 7: 等待视频页面加载
        time.sleep(2)
        if not self._is_in_video_page():
            self.logger.error("✗ 视频页面加载失败")
            return False

        self.logger.info(f"✓ 成功打开视频: {keyword}")
        return True

    def open_video_by_url(self, video_url):
        """
        通过分享链接打开视频

        Args:
            video_url: 抖音视频分享链接

        Returns:
            bool: 是否成功打开
        """
        import subprocess
        import time

        self.logger.info(f"🔗 正在通过链接打开视频...")

        try:
            # 使用 adb 打开链接
            subprocess.run(
                [
                    'adb', 'shell', 'am', 'start',
                    '-a', 'android.intent.action.VIEW',
                    '-d', video_url
                ],
                check=True
            )

            # 等待页面加载
            time.sleep(3)

            if self._is_in_video_page():
                self.logger.info("✓ 成功打开视频")
                return True
            else:
                self.logger.error("✗ 视频页面加载失败")
                return False

        except Exception as e:
            self.logger.error(f"✗ 打开视频链接失败: {e}")
            return False

    def open_comment_section(self):
        """
        打开评论区

        Returns:
            bool: 是否成功打开评论区
        """
        from element_ids import DouyinElementIds
        import time

        self.logger.info("💬 正在打开评论区...")

        # 检查是否在视频页面
        if not self._is_in_video_page():
            self.logger.error("✗ 不在视频页面，无法打开评论区")
            return False

        # 点击评论按钮
        if not self.device.click_element(DouyinElementIds.COMMENT_BUTTON):
            self.logger.error("✗ 点击评论按钮失败")
            return False

        time.sleep(1)

        # 等待评论列表加载
        if not self.device.wait_element(
            DouyinElementIds.COMMENT_INPUT, timeout=10
        ):
            self.logger.error("✗ 评论列表加载超时")
            return False

        self.logger.info("✓ 评论区已打开")
        return True

    def is_on_video_page(self):
        """
        检查是否在视频页面

        Returns:
            bool: 是否在视频页面
        """
        return self._is_in_video_page()
```

### 1.2 测试例子

```python
def test_video_navigator():
    """测试视频导航器"""
    from device_interaction import DeviceInteraction
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 初始化设备
    device = DeviceInteraction(logger=logger)

    # 创建导航器
    navigator = VideoNavigator(device, logger=logger)

    # 测试页面检测
    current_page = navigator.detect_current_page()
    print(f"当前页面: {current_page}")

    # 测试搜索视频
    if navigator.search_video_by_keyword("抖音视频标题"):
        print("✓ 搜索成功")

        # 测试打开评论区
        if navigator.open_comment_section():
            print("✓ 评论区打开成功")
    else:
        print("✗ 搜索失败")

    device.close()
```

---

## 2. CommentManager - 评论管理模块

**文件**: `comment_manager.py`

**职责**: 管理评论的加载、提取和关键字匹配

### 2.1 类结构

```python
class CommentManager:
    """评论管理器"""

    def __init__(self, device_interaction, keyword_config, logger=None):
        """
        初始化评论管理器

        Args:
            device_interaction: DeviceInteraction 实例
            keyword_config: 关键字配置字典
                {
                    "keyword1": {"enabled": True, "reply_templates": [...]},
                    ...
                }
            logger: 日志对象
        """
        self.device = device_interaction
        self.keyword_config = keyword_config
        self.logger = logger or logging.getLogger(__name__)
        self.loaded_comments = []  # 已加载的评论列表

    # ==================== 评论加载 ====================

    def enter_comment_section(self):
        """
        进入评论区（点击评论按钮）

        Returns:
            bool: 是否成功进入
        """
        from element_ids import DouyinElementIds
        import time

        self.logger.info("📝 正在进入评论区...")

        if self.device.click_element(DouyinElementIds.COMMENT_BUTTON):
            time.sleep(1)
            self.logger.info("✓ 已进入评论区")
            return True
        else:
            self.logger.error("✗ 进入评论区失败")
            return False

    def load_more_comments(self, scroll_count=5):
        """
        向上滑动加载更多评论

        Args:
            scroll_count: 向上滑动的次数

        Returns:
            bool: 是否成功加载
        """
        import time

        self.logger.info(f"⬆️  向上滑动加载评论... (次数: {scroll_count})")

        for i in range(scroll_count):
            self.device.swipe(direction='up', steps=5, duration=500)
            time.sleep(self.logger.info(f"   已滑动 {i+1}/{scroll_count} 次"))

        return True

    def get_visible_comments(self):
        """
        获取当前屏幕上可见的所有评论

        Returns:
            List[Dict]: 评论列表
                [
                    {
                        'text': '评论文本',
                        'author': '作者名',
                        'ui_element': <element>,
                        'reply_count': 5,
                        ...
                    },
                    ...
                ]
        """
        self.logger.info("🔎 正在提取可见评论...")

        # 这是一个复杂的操作，需要通过 UI Automator 的 dump 功能获取
        # 评论通常在 RecyclerView 中，需要通过解析 XML 树来提取

        comments = []

        try:
            # 获取 UI 树
            hierarchy = self.device.get_dump_hierarchy()

            # 解析 XML 找出所有评论元素
            # 注意：这取决于抖音 APP 的具体 UI 结构
            # 通常评论有特定的 resource_id 或类名

            # 示例伪代码：
            # for comment_elem in hierarchy.find_all(comment_class):
            #     comment_dict = {
            #         'text': extract_text(comment_elem),
            #         'author': extract_author(comment_elem),
            #         'ui_element': comment_elem,
            #     }
            #     comments.append(comment_dict)

            self.logger.info(f"✓ 提取了 {len(comments)} 条评论")
            self.loaded_comments.extend(comments)
            return comments

        except Exception as e:
            self.logger.error(f"✗ 提取评论失败: {e}")
            return []

    # ==================== 关键字匹配 ====================

    def find_comments_by_keyword(self, comments_list, keywords=None):
        """
        根据关键字过滤评论

        Args:
            comments_list: 评论列表
            keywords: 关键字列表（默认使用配置中的关键字）

        Returns:
            List[Dict]: 匹配的评论列表，带上 matched_keywords 和 priority
        """
        if keywords is None:
            keywords = list(self.keyword_config.keys())

        self.logger.info(f"🔍 正在匹配关键字... (关键字数: {len(keywords)})")

        matched_comments = []

        for comment in comments_list:
            comment_text = comment.get('text', '').lower()
            matched_keywords = []
            max_priority = float('inf')

            # 遍历所有关键字
            for keyword in keywords:
                keyword_config = self.keyword_config.get(keyword, {})

                # 检查关键字是否启用
                if not keyword_config.get('enabled', True):
                    continue

                # 检查评论文本中是否包含关键字
                if keyword.lower() in comment_text:
                    matched_keywords.append(keyword)
                    # 记录最高优先级（最小的数字)
                    priority = keyword_config.get('priority', 999)
                    max_priority = min(max_priority, priority)

            # 如果匹配到关键字，添加到结果列表
            if matched_keywords:
                comment['matched_keywords'] = matched_keywords
                comment['priority'] = max_priority
                matched_comments.append(comment)

        # 按优先级排序
        matched_comments.sort(key=lambda x: x['priority'])

        self.logger.info(f"✓ 找到 {len(matched_comments)} 条匹配评论")
        return matched_comments

    def extract_comment_text(self, element):
        """
        从 UI 元素中提取评论文本

        Args:
            element: UI 元素

        Returns:
            str: 评论文本内容
        """
        try:
            # 尝试多种方式获取文本
            text = element.get_text()
            if text:
                return text

            # 如果没有，尝试获取 text 属性
            text = element.info.get('text', '')
            if text:
                return text

            # 如果还是没有，尝试递归获取子元素的文本
            return self._extract_text_recursive(element)

        except Exception as e:
            self.logger.warning(f"✗ 提取文本失败: {e}")
            return ""

    def _extract_text_recursive(self, element, depth=0, max_depth=3):
        """递归提取元素及其子元素的文本"""
        if depth > max_depth:
            return ""

        texts = []

        try:
            # 获取元素自身的文本
            if hasattr(element, 'info'):
                text = element.info.get('text', '')
                if text:
                    texts.append(text)

            # 尝试获取子元素的文本
            if hasattr(element, 'child'):
                children = element.child()
                for child in children:
                    texts.append(self._extract_text_recursive(child, depth + 1))

        except:
            pass

        return ' '.join(texts)

    def get_all_comments(self, max_scroll=20):
        """
        加载并获取所有可见的评论

        Args:
            max_scroll: 最大滑动次数

        Returns:
            List[Dict]: 评论列表
        """
        self.logger.info(f"📚 正在加载所有评论... (最大滑动次数: {max_scroll})")

        all_comments = []

        for i in range(max_scroll):
            # 获取当前屏幕的评论
            visible_comments = self.get_visible_comments()
            all_comments.extend(visible_comments)

            # 向上滑动加载更多
            self.device.swipe(direction='up', steps=5, duration=500)

            self.logger.info(f"   已加载 {len(all_comments)} 条评论 ({i+1}/{max_scroll})")

        return all_comments
```

---

## 3. ReplyHandler - 回复处理模块

**文件**: `reply_handler.py`

**职责**: 处理对评论的自动回复

### 3.1 类结构

```python
import time
import logging

class ReplyHandler:
    """回复处理器"""

    def __init__(self, device_interaction, logger=None):
        """
        初始化回复处理器

        Args:
            device_interaction: DeviceInteraction 实例
            logger: 日志对象
        """
        self.device = device_interaction
        self.logger = logger or logging.getLogger(__name__)
        self.reply_count = 0  # 已发送回复数

    def click_reply_to_comment(self, comment_element):
        """
        点击评论以展开回复框

        Args:
            comment_element: 评论的 UI 元素

        Returns:
            bool: 是否成功
        """
        self.logger.info("➡️  正在点击评论...")

        try:
            if isinstance(comment_element, dict):
                # 如果是字典，获取 UI 元素
                ui_element = comment_element.get('ui_element')
                if not ui_element:
                    self.logger.error("✗ 找不到评论的 UI 元素")
                    return False
                comment_element = ui_element

            # 点击评论
            comment_element.click()
            time.sleep(0.5)

            self.logger.info("✓ 已点击评论")
            return True

        except Exception as e:
            self.logger.error(f"✗ 点击评论失败: {e}")
            return False

    def input_reply_text(self, reply_text, timeout=10):
        """
        输入回复内容

        Args:
            reply_text: 回复内容
            timeout: 超时时间

        Returns:
            bool: 是否成功
        """
        from element_ids import DouyinElementIds

        self.logger.info(f"⌨️  正在输入回复内容...")

        try:
            # 找到回复输入框
            if not self.device.wait_element(
                DouyinElementIds.COMMENT_INPUT, timeout=timeout
            ):
                self.logger.error("✗ 回复输入框加载超时")
                return False

            # 输入文本
            if self.device.input_text(
                DouyinElementIds.COMMENT_INPUT, reply_text, clear_first=True
            ):
                self.logger.info(f"✓ 已输入回复内容: {reply_text}")
                return True
            else:
                self.logger.error("✗ 输入回复内容失败")
                return False

        except Exception as e:
            self.logger.error(f"✗ 输入回复内容异常: {e}")
            return False

    def send_reply(self, timeout=10):
        """
        发送回复

        Returns:
            bool: 是否成功
        """
        from element_ids import DouyinElementIds

        self.logger.info("📤 正在发送回复...")

        try:
            # 点击发送按钮
            if self.device.click_element(DouyinElementIds.SEND_TEXT_COMMENT):
                time.sleep(1)
                self.reply_count += 1
                self.logger.info(f"✓ 回复已发送 (共 {self.reply_count} 条)")
                return True
            else:
                self.logger.error("✗ 点击发送按钮失败")
                return False

        except Exception as e:
            self.logger.error(f"✗ 发送回复失败: {e}")
            return False

    def reply_to_comment(self, comment_element, reply_text):
        """
        一体化回复流程：点击、输入、发送

        Args:
            comment_element: 评论元素
            reply_text: 回复内容

        Returns:
            Dict: 回复结果
                {
                    'success': True/False,
                    'error_message': str,
                    'time_taken': float
                }
        """
        import time

        self.logger.info(f"💬 正在执行完整回复流程...")

        start_time = time.time()
        result = {
            'success': False,
            'error_message': None,
            'time_taken': 0
        }

        try:
            # 步骤 1: 点击评论
            if not self.click_reply_to_comment(comment_element):
                result['error_message'] = "点击评论失败"
                return result

            time.sleep(0.5)

            # 步骤 2: 输入回复内容
            if not self.input_reply_text(reply_text, timeout=5):
                result['error_message'] = "输入回复失败"
                return result

            time.sleep(0.5)

            # 步骤 3: 发送回复
            if not self.send_reply(timeout=5):
                result['error_message'] = "发送回复失败"
                return result

            # 成功
            result['success'] = True
            result['time_taken'] = time.time() - start_time

            self.logger.info(
                f"✓ 回复成功 (耗时: {result['time_taken']:.2f}秒)"
            )
            return result

        except Exception as e:
            result['error_message'] = str(e)
            self.logger.error(f"✗ 回复过程异常: {e}")
            return result
```

---

## 4. Utils - 工具函数

**文件**: `utils.py`

```python
"""工具函数库"""

import logging
import time
from functools import wraps

# ==================== 日志工具 ====================

def setup_logger(name, level=logging.INFO, log_file=None):
    """
    设置日志记录器

    Args:
        name: 日志名称
        level: 日志级别
        log_file: 日志文件路径

    Returns:
        logging.Logger: 日志对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# ==================== 重试装饰器 ====================

def retry(max_attempts=3, delay=1):
    """
    重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）

    Usage:
        @retry(max_attempts=3, delay=1)
        def some_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# ==================== 随机延迟 ====================

def random_delay(min_seconds, max_seconds):
    """
    随机延迟，使操作看起来更像真人

    Args:
        min_seconds: 最小延迟
        max_seconds: 最大延迟
    """
    import random
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


# ==================== 字符串匹配 ====================

def contains_keyword(text, keywords, case_sensitive=False):
    """
    检查文本是否包含任何关键字

    Args:
        text: 文本
        keywords: 关键字列表
        case_sensitive: 是否区分大小写

    Returns:
        bool: 是否包含
    """
    if not case_sensitive:
        text = text.lower()
        keywords = [k.lower() for k in keywords]

    for keyword in keywords:
        if keyword in text:
            return True

    return False


# ==================== 时间格式化 ====================

def format_duration(seconds):
    """
    格式化时间长度

    Args:
        seconds: 秒数

    Returns:
        str: 格式化后的字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}小时{minutes}分钟{secs}秒"
    elif minutes > 0:
        return f"{minutes}分钟{secs}秒"
    else:
        return f"{secs}秒"
```

---

## 5. Main - 主程序

**文件**: `main.py`

```python
"""主程序入口"""

import logging
import time
from datetime import datetime

from config import TASK_CONFIG, DEVICE_CONFIG, LOG_CONFIG
from device_interaction import DeviceInteraction
from video_navigator import VideoNavigator
from comment_manager import CommentManager
from reply_handler import ReplyHandler
from utils import setup_logger, format_duration, random_delay


class AutomaticCommentReplyBot:
    """自动评论回复机器人"""

    def __init__(self, task_config, device_config, log_config):
        """
        初始化机器人

        Args:
            task_config: 任务配置
            device_config: 设备配置
            log_config: 日志配置
        """
        self.task_config = task_config
        self.device_config = device_config
        self.log_config = log_config

        # 初始化日志
        self.logger = setup_logger(
            'DouyinBot',
            level=getattr(logging, log_config['level']),
            log_file=log_config.get('log_file')
        )

        # 初始化各个模块
        self.device = None
        self.navigator = None
        self.comment_manager = None
        self.reply_handler = None

        # 统计数据
        self.stats = {
            'start_time': None,
            'end_time': None,
            'videos_processed': 0,
            'comments_found': 0,
            'comments_matched': 0,
            'replies_sent': 0,
            'replies_failed': 0,
            'errors': []
        }

    def initialize(self):
        """初始化所有模块"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🤖 抖音自动评论回复机器人 - 初始化中...")
            self.logger.info("=" * 60)

            # 连接设备
            self.logger.info("连接设备中...")
            self.device = DeviceInteraction(
                device_id=self.device_config['device_id'],
                timeout=self.device_config['default_timeout'],
                logger=self.logger
            )

            # 初始化各模块
            self.navigator = VideoNavigator(self.device, self.logger)
            self.comment_manager = CommentManager(
                self.device,
                self.task_config['keywords_to_reply'],
                self.logger
            )
            self.reply_handler = ReplyHandler(self.device, self.logger)

            self.logger.info("✓ 初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"✗ 初始化失败: {e}")
            self.stats['errors'].append(f"初始化失败: {e}")
            return False

    def run_task(self):
        """运行完整任务"""
        self.stats['start_time'] = datetime.now()

        try:
            # 初始化
            if not self.initialize():
                return False

            # 获取目标视频列表
            video_sources = []

            # 添加搜索关键字的视频
            if 'video_search_keywords' in self.task_config:
                video_sources.extend([
                    {'type': 'keyword', 'value': kw}
                    for kw in self.task_config['video_search_keywords']
                ])

            # 添加分享链接的视频
            if 'video_urls' in self.task_config:
                video_sources.extend([
                    {'type': 'url', 'value': url}
                    for url in self.task_config['video_urls']
                ])

            # 处理每个视频
            for video_source in video_sources:
                self.logger.info("\n" + "-" * 60)

                if not self.process_video(video_source):
                    continue

                # 延迟
                delay_range = self.task_config.get(
                    'delay_between_replies', [1, 3]
                )
                random_delay(delay_range[0], delay_range[1])

            # 生成报告
            self.generate_report()

        except Exception as e:
            self.logger.error(f"✗ 任务执行出错: {e}")
            self.stats['errors'].append(str(e))

        finally:
            self.cleanup()

    def process_video(self, video_source):
        """处理单个视频"""
        try:
            # 打开视频
            if video_source['type'] == 'keyword':
                if not self.navigator.search_video_by_keyword(video_source['value']):
                    return False
            elif video_source['type'] == 'url':
                if not self.navigator.open_video_by_url(video_source['value']):
                    return False

            self.stats['videos_processed'] += 1
            time.sleep(1)

            # 打开评论区
            if not self.navigator.open_comment_section():
                self.logger.error("✗ 打开评论区失败")
                return False

            time.sleep(1)

            # 加载评论
            self.comment_manager.load_more_comments(
                scroll_count=self.task_config.get('max_scroll_count', 20)
            )

            # 获取所有评论
            all_comments = self.comment_manager.get_visible_comments()
            self.stats['comments_found'] += len(all_comments)

            # 匹配关键字
            matched_comments = self.comment_manager.find_comments_by_keyword(
                all_comments
            )
            self.stats['comments_matched'] += len(matched_comments)

            # 回复评论
            self.reply_to_comments(matched_comments)

            return True

        except Exception as e:
            self.logger.error(f"✗ 处理视频失败: {e}")
            self.stats['errors'].append(str(e))
            return False

    def reply_to_comments(self, comments):
        """对评论进行回复"""
        max_replies = self.task_config.get('max_replies_per_video', 10)
        replied_count = 0

        for comment in comments:
            if replied_count >= max_replies:
                self.logger.info(f"📊 已达到单视频最大回复数: {max_replies}")
                break

            # 获取回复内容
            reply_text = self.get_reply_text(comment)

            # 执行回复
            result = self.reply_handler.reply_to_comment(
                comment, reply_text
            )

            if result['success']:
                self.stats['replies_sent'] += 1
                replied_count += 1
            else:
                self.stats['replies_failed'] += 1
                self.logger.warning(
                    f"⚠️  回复失败: {result['error_message']}"
                )

            # 延迟
            delay_range = self.task_config.get(
                'delay_between_replies', [1, 3]
            )
            random_delay(delay_range[0], delay_range[1])

    def get_reply_text(self, comment):
        """获取回复文本"""
        mode = self.task_config.get('operation_mode', 'random')
        keywords = comment.get('matched_keywords', [])

        # 获取所有匹配关键字的回复模板
        reply_templates = []
        for keyword in keywords:
            keyword_config = self.task_config['keywords_to_reply'].get(
                keyword, {}
            )
            templates = keyword_config.get('reply_templates', [])
            reply_templates.extend(templates)

        if not reply_templates:
            return "感谢支持！"

        if mode == 'first':
            return reply_templates[0]
        elif mode == 'random':
            import random
            return random.choice(reply_templates)
        else:
            return reply_templates[0]

    def generate_report(self):
        """生成任务报告"""
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 任务完成 - 统计报告")
        self.logger.info("=" * 60)
        self.logger.info(f"开始时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"结束时间: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"总耗时: {format_duration(duration)}")
        self.logger.info(f"处理视频数: {self.stats['videos_processed']}")
        self.logger.info(f"发现评论数: {self.stats['comments_found']}")
        self.logger.info(f"匹配评论数: {self.stats['comments_matched']}")
        self.logger.info(f"成功回复数: {self.stats['replies_sent']}")
        self.logger.info(f"失败回复数: {self.stats['replies_failed']}")

        if self.stats['errors']:
            self.logger.warning(f"\n⚠️  出现 {len(self.stats['errors'])} 个错误:")
            for error in self.stats['errors']:
                self.logger.warning(f"  - {error}")

        self.logger.info("=" * 60 + "\n")

    def cleanup(self):
        """清理资源"""
        try:
            if self.device:
                self.device.close()
                self.logger.info("✓ 设备连接已关闭")
        except Exception as e:
            self.logger.error(f"✗ 清理资源失败: {e}")


def main():
    """主入口"""
    bot = AutomaticCommentReplyBot(TASK_CONFIG, DEVICE_CONFIG, LOG_CONFIG)
    bot.run_task()


if __name__ == '__main__':
    main()
```

---

## 开发顺序建议

1. **先完成 DeviceInteraction** - 所有其他模块都依赖它
2. **然后完成 VideoNavigator** - 必须能够打开视频
3. **接着完成 CommentManager** - 必须能够加载和解析评论
4. **然后完成 ReplyHandler** - 实现回复功能
5. **最后完成 Main** - 整合所有模块


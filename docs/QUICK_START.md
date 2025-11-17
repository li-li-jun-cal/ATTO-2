# 快速开始指南

## 前置条件

### 1. 环境要求
- Python 3.8+
- Android 设备（vivo S12 或兼容设备）
- USB 调试开启
- ADB 驱动正确安装

### 2. 安装依赖

```bash
pip install uiautomator2 pyyaml requests pillow
```

### 3. 设备准备

```bash
# 检查设备连接
adb devices

# 初始化 uiautomator2
python -m uiautomator2 init

# 安装 uiautomator2 应用
python -c "import uiautomator2; uiautomator2.init()"
```

---

## 项目初始化

### 步骤 1: 创建项目文件结构

```
AOTO/
├── element_ids.py              # 已有 - UI元素ID配置
├── IMPLEMENTATION_GUIDE.md      # 已有 - 完整实现指南
├── QUICK_START.md               # 本文件
├── device_interaction.py        # 待创建 - 设备交互层
├── video_navigator.py          # 待创建 - 视频导航模块
├── comment_manager.py          # 待创建 - 评论管理模块
├── reply_handler.py            # 待创建 - 回复处理模块
├── config.py                   # 待创建 - 配置管理
├── main.py                     # 待创建 - 主程序
├── utils.py                    # 待创建 - 工具函数
└── tests/                      # 待创建 - 测试文件
    ├── test_device.py
    └── test_navigator.py
```

### 步骤 2: 创建配置文件

创建 `config.py`:

```python
import os
from datetime import datetime

# ============= 任务配置 =============
TASK_CONFIG = {
    # 视频导航方式
    # 选项 1: 使用关键字搜索
    "video_search_keywords": ["抖音视频标题"],

    # 选项 2: 使用分享链接
    # "video_urls": ["https://v.douyin.com/..."],

    # 关键字回复配置
    "keywords_to_reply": {
        "很好看": {
            "enabled": True,
            "reply_templates": [
                "感谢您的支持！",
                "谢谢喜欢！"
            ],
            "priority": 1
        },
        "棒": {
            "enabled": True,
            "reply_templates": [
                "谢谢夸奖！"
            ],
            "priority": 2
        }
    },

    # 操作模式: 'first' | 'random' | 'all'
    # first: 总是选择第一个回复模板
    # random: 随机选择一个回复模板
    # all: 对同一评论多次回复（不推荐）
    "operation_mode": "random",

    # 每个视频最多回复数
    "max_replies_per_video": 10,

    # 回复间隔（秒）：随机选择范围内的值
    "delay_between_replies": [1, 3],

    # 评论加载配置
    "max_scroll_count": 20,  # 最多向上滑动次数
    "scroll_pause_time": 1,  # 滑动后等待时间（秒）

    # 停止条件
    "stop_when_no_match": False,  # 未找到匹配时是否停止
}

# ============= 设备配置 =============
DEVICE_CONFIG = {
    "device_id": None,  # None 表示自动检测，或指定具体ID如 "192.168.1.100:7555"

    # 超时设置
    "default_timeout": 10,  # 单位：秒
    "long_timeout": 20,
    "short_timeout": 3,

    # 截图配置
    "screenshot_dir": "./screenshots",
    "save_screenshot": True,  # 调试时设为 True，生产环境设为 False

    # UI 操作配置
    "click_duration": 100,  # 点击持续时间（毫秒）
    "swipe_duration": 500,  # 滑动持续时间（毫秒）
}

# ============= 日志配置 =============
LOG_CONFIG = {
    "level": "INFO",  # DEBUG | INFO | WARNING | ERROR
    "log_file": f"./logs/douyin_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "console_output": True,
}

# ============= 自动创建目录 =============
os.makedirs(DEVICE_CONFIG["screenshot_dir"], exist_ok=True)
os.makedirs(os.path.dirname(LOG_CONFIG["log_file"]), exist_ok=True)
```

### 步骤 3: 创建基础设备交互类

创建 `device_interaction.py`:

```python
import uiautomator2 as u2
import time
import os
from datetime import datetime
import logging

from element_ids import DouyinElementIds

class DeviceInteraction:
    """设备交互核心类"""

    def __init__(self, device_id=None, timeout=10, logger=None):
        """
        初始化设备连接

        Args:
            device_id: 设备ID，None 表示自动检测
            timeout: 默认超时时间（秒）
            logger: 日志对象
        """
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout

        try:
            if device_id:
                self.device = u2.connect(device_id)
                self.logger.info(f"✓ 已连接设备: {device_id}")
            else:
                # 自动检测设备
                devices = u2.list_adb_devices()
                if not devices:
                    raise Exception("未找到任何Android设备，请检查USB连接")
                self.device = u2.connect(devices[0])
                self.logger.info(f"✓ 自动检测到设备: {devices[0]}")

            # 检查抖音应用
            self.check_douyin_app()

        except Exception as e:
            self.logger.error(f"✗ 设备初始化失败: {e}")
            raise

    def check_douyin_app(self):
        """检查抖音应用是否已安装"""
        result = self.device.app_info(DouyinElementIds.DOUYIN_PACKAGE)
        if result['version_name']:
            self.logger.info(f"✓ 抖音已安装，版本: {result['version_name']}")
        else:
            raise Exception("抖音应用未安装或未正确启动")

    def click_element(self, resource_id, text=None, timeout=None):
        """
        点击指定元素

        Args:
            resource_id: 元素的 resource_id
            text: 元素的 text 属性（可选）
            timeout: 超时时间

        Returns:
            bool: 是否成功点击
        """
        timeout = timeout or self.timeout
        try:
            if text:
                element = self.device(resourceId=resource_id, text=text)
            else:
                element = self.device(resourceId=resource_id)

            element.wait.exists(timeout=timeout)
            element.click()
            self.logger.debug(f"✓ 点击元素: {resource_id}")
            return True
        except Exception as e:
            self.logger.warning(f"✗ 点击失败 [{resource_id}]: {e}")
            return False

    def input_text(self, resource_id, text, clear_first=True, timeout=None):
        """
        输入文本到输入框

        Args:
            resource_id: 输入框的 resource_id
            text: 要输入的文本
            clear_first: 是否先清空
            timeout: 超时时间

        Returns:
            bool: 是否成功输入
        """
        timeout = timeout or self.timeout
        try:
            element = self.device(resourceId=resource_id)
            element.wait.exists(timeout=timeout)

            if clear_first:
                element.clear_text()

            element.set_text(text)
            self.logger.debug(f"✓ 输入文本: {text}")
            return True
        except Exception as e:
            self.logger.warning(f"✗ 输入失败 [{resource_id}]: {e}")
            return False

    def swipe(self, direction='up', steps=5, duration=300):
        """
        滑动屏幕

        Args:
            direction: 滑动方向 'up' | 'down' | 'left' | 'right'
            steps: 滑动步数
            duration: 滑动持续时间（毫秒）

        Returns:
            bool: 是否成功滑动
        """
        try:
            width = self.device.window_size()[0]
            height = self.device.window_size()[1]

            center_x = width // 2
            center_y = height // 2

            if direction == 'up':
                self.device.swipe(center_x, center_y, center_x, center_y - steps * 50, duration)
            elif direction == 'down':
                self.device.swipe(center_x, center_y, center_x, center_y + steps * 50, duration)
            elif direction == 'left':
                self.device.swipe(center_x, center_y, center_x - steps * 50, center_y, duration)
            elif direction == 'right':
                self.device.swipe(center_x, center_y, center_x + steps * 50, center_y, duration)

            self.logger.debug(f"✓ 向{direction}滑动")
            time.sleep(0.5)
            return True
        except Exception as e:
            self.logger.warning(f"✗ 滑动失败: {e}")
            return False

    def wait_element(self, resource_id, text=None, timeout=None):
        """
        等待元素出现

        Args:
            resource_id: 元素 resource_id
            text: 元素的 text 属性（可选）
            timeout: 超时时间

        Returns:
            bool: 元素是否出现
        """
        timeout = timeout or self.timeout
        try:
            if text:
                element = self.device(resourceId=resource_id, text=text)
            else:
                element = self.device(resourceId=resource_id)

            element.wait.exists(timeout=timeout)
            return True
        except:
            return False

    def get_element(self, resource_id, text=None):
        """
        获取元素对象

        Args:
            resource_id: 元素 resource_id
            text: 元素的 text 属性（可选）

        Returns:
            element 或 None
        """
        try:
            if text:
                return self.device(resourceId=resource_id, text=text)
            else:
                return self.device(resourceId=resource_id)
        except:
            return None

    def take_screenshot(self, filename=None):
        """
        保存截图

        Args:
            filename: 文件名，不指定则自动生成

        Returns:
            str: 截图文件路径
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"screenshot_{timestamp}.png"

            filepath = os.path.join('./screenshots', filename)
            self.device.screenshot(filepath)
            self.logger.debug(f"✓ 截图已保存: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"✗ 截图失败: {e}")
            return None

    def get_dump_hierarchy(self):
        """获取当前UI树（用于调试）"""
        try:
            return self.device.dump_hierarchy()
        except Exception as e:
            self.logger.error(f"✗ 获取UI树失败: {e}")
            return None

    def close(self):
        """关闭设备连接"""
        try:
            if self.device:
                self.device.close()
                self.logger.info("✓ 设备连接已关闭")
        except:
            pass
```

### 步骤 4: 运行测试

创建 `test_basic.py`:

```python
import logging
from config import DEVICE_CONFIG, LOG_CONFIG
from device_interaction import DeviceInteraction

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format']
)
logger = logging.getLogger(__name__)

def test_device_connection():
    """测试设备连接"""
    logger.info("=" * 50)
    logger.info("测试 1: 设备连接")
    logger.info("=" * 50)

    try:
        device = DeviceInteraction(
            device_id=DEVICE_CONFIG["device_id"],
            timeout=DEVICE_CONFIG["default_timeout"],
            logger=logger
        )
        logger.info("✓ 设备连接成功")
        device.close()
        return True
    except Exception as e:
        logger.error(f"✗ 设备连接失败: {e}")
        return False

def test_screenshot():
    """测试截图"""
    logger.info("=" * 50)
    logger.info("测试 2: 屏幕截图")
    logger.info("=" * 50)

    try:
        device = DeviceInteraction(logger=logger)
        filepath = device.take_screenshot("test_screenshot.png")
        if filepath:
            logger.info(f"✓ 截图保存成功: {filepath}")
        device.close()
        return True
    except Exception as e:
        logger.error(f"✗ 截图失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始基础测试...")

    results = [
        ("设备连接", test_device_connection()),
        ("屏幕截图", test_screenshot()),
    ]

    logger.info("\n" + "=" * 50)
    logger.info("测试总结")
    logger.info("=" * 50)
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
```

运行测试：

```bash
python test_basic.py
```

---

## 下一步

1. ✓ 完成设备交互层 (`device_interaction.py`)
2. 完成视频导航模块 (`video_navigator.py`)
3. 完成评论管理模块 (`comment_manager.py`)
4. 完成回复处理模块 (`reply_handler.py`)
5. 编写主程序 (`main.py`)
6. 完整测试和优化

---

## 常见问题

### Q: 如何找到正确的元素 ID?

A: 使用 `uiautomator2` 的 UI Inspector:

```bash
python -m uiautomator2 init  # 首次初始化
python -c "import uiautomator2; uiautomator2.device().open('com.ss.android.ugc.aweme')"
# 然后在 Chrome 中访问: http://localhost:7912
```

### Q: 如何处理元素加载缓慢?

A: 增加超时时间:

```python
device.wait_element(resource_id, timeout=20)  # 增加超时到 20 秒
```

### Q: 如何调试失败的操作?

A: 保存截图并查看 UI 树:

```python
device.take_screenshot("debug.png")
hierarchy = device.get_dump_hierarchy()
print(hierarchy)  # 查看当前的 UI 层级
```

---

## 获取帮助

- 查看 `IMPLEMENTATION_GUIDE.md` 了解完整架构
- 查看 `element_ids.py` 了解所有可用的 UI 元素
- 查阅 [uiautomator2 官方文档](https://github.com/openatx/uiautomator2)


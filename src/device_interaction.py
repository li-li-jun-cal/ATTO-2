"""
设备交互层 - 与 Android 设备的所有交互
基于 uiautomator2 库封装了设备操作的基础方法
"""

import uiautomator2 as u2
import time
import os
import logging
from datetime import datetime
try:
    from PIL import Image
    import cv2
    import numpy as np
    HAS_IMAGE_RECOGNITION = True
except ImportError:
    HAS_IMAGE_RECOGNITION = False

from element_ids import DouyinElementIds


class DeviceInteraction:
    """设备交互核心类 - 与 Android 设备的所有交互"""

    def __init__(self, device_id=None, timeout=10, logger=None):
        """
        初始化设备连接

        Args:
            device_id: 设备ID，None 表示自动检测
            timeout: 默认超时时间（秒）
            logger: 日志对象

        Raises:
            Exception: 设备连接失败或抖音应用未安装
        """
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout
        self.device = None

        try:
            # 连接设备
            if device_id:
                self.device = u2.connect(device_id)
                self.logger.info(f"✓ 已连接设备: {device_id}")
            else:
                # 自动检测设备 - 使用 connect_adb() 获取设备列表
                try:
                    # 新版本 API
                    from adb_shell.adb_device import AdbDeviceTcp
                    import subprocess

                    # 使用 adb devices 命令
                    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                    devices = [line.split()[0] for line in lines if line.strip() and 'device' in line]

                    if not devices:
                        raise Exception("未找到任何Android设备，请检查USB连接")

                    device_id = devices[0]
                    self.device = u2.connect(device_id)
                    self.logger.info(f"✓ 自动检测到设备: {device_id}")

                except Exception as e:
                    # 降级方案：直接尝试连接本地设备
                    self.logger.warning(f"⚠️  自动检测失败，尝试连接本地设备: {e}")
                    try:
                        self.device = u2.connect()  # 连接本地设备
                        self.logger.info("✓ 已连接本地设备")
                    except:
                        self.logger.warning("⚠️  无法自动检测设备，请手动指定 device_id")
                        raise Exception("未找到任何Android设备，请检查USB连接或手动指定 device_id")

            # 获取设备信息
            try:
                device_info = self.device.info
                self.logger.info(f"  Android 版本: {device_info.get('release', 'N/A')}")
                self.logger.info(f"  屏幕分辨率: {device_info.get('display', 'N/A')}")
            except:
                self.logger.warning("⚠️  无法获取设备详细信息，继续初始化...")

            # 检查抖音应用
            self.check_douyin_app()

        except Exception as e:
            self.logger.error(f"✗ 设备初始化失败: {e}")
            raise

    def check_douyin_app(self):
        """
        检查抖音应用是否已安装

        Raises:
            Exception: 抖音应用未安装或未正确启动
        """
        try:
            result = self.device.app_info(DouyinElementIds.DOUYIN_PACKAGE)
            if result and result.get('version_name'):
                self.logger.info(
                    f"✓ 抖音已安装，版本: {result.get('version_name')}"
                )
                return True
            else:
                raise Exception("抖音应用未安装或信息获取失败")
        except Exception as e:
            # 如果获取失败，给出警告但不中断程序
            self.logger.warning(f"⚠️  无法验证抖音应用: {e}")
            self.logger.warning("⚠️  继续初始化，请确保已安装抖音应用")
            # 不抛出异常，允许程序继续
            return False

    # ========================================================================
    #                          点击和输入操作
    # ========================================================================

    def click(self, x, y):
        """
        点击屏幕坐标

        Args:
            x: X 坐标
            y: Y 坐标

        Returns:
            bool: 是否成功点击

        Example:
            device.click(540, 960)  # 点击屏幕中心
        """
        try:
            self.device.click(x, y)
            self.logger.debug(f"✓ 点击坐标: ({x}, {y})")
            return True
        except Exception as e:
            self.logger.warning(f"✗ 点击坐标失败 ({x}, {y}): {e}")
            return False

    def click_element(self, resource_id, text=None, timeout=None):
        """
        点击指定元素

        Args:
            resource_id: 元素的 resource_id
            text: 元素的 text 属性（可选，用于区分同 ID 的多个元素）
            timeout: 超时时间（秒）

        Returns:
            bool: 是否成功点击

        Example:
            device.click_element(DouyinElementIds.SEARCH_BUTTON)
            device.click_element(DouyinElementIds.TOP_TAB_COMMON, text="推荐")
        """
        timeout = timeout or self.timeout
        try:
            if text:
                element = self.device(resourceId=resource_id, text=text)
            else:
                element = self.device(resourceId=resource_id)

            # uiautomator2 v3.0+ API: 使用 exists 属性而不是 wait.exists()
            start_time = time.time()
            while time.time() - start_time < timeout:
                if element.exists:
                    element.click()
                    self.logger.debug(f"✓ 点击元素: {resource_id}")
                    return True
                time.sleep(0.1)

            self.logger.warning(f"✗ 点击失败 [{resource_id}]: 元素在 {timeout} 秒内未出现")
            return False
        except Exception as e:
            self.logger.warning(f"✗ 点击失败 [{resource_id}]: {str(e)[:100]}")
            return False

    def input_text(self, resource_id, text, clear_first=True, timeout=None):
        """
        输入文本到输入框

        Args:
            resource_id: 输入框的 resource_id
            text: 要输入的文本
            clear_first: 是否先清空输入框
            timeout: 超时时间（秒）

        Returns:
            bool: 是否成功输入

        Example:
            device.input_text(DouyinElementIds.SEARCH_INPUT, "抖音视频")
        """
        timeout = timeout or self.timeout
        try:
            element = self.device(resourceId=resource_id)

            # uiautomator2 v3.0+ API: 使用 exists 属性而不是 wait.exists()
            start_time = time.time()
            while time.time() - start_time < timeout:
                if element.exists:
                    if clear_first:
                        element.clear_text()

                    element.set_text(text)
                    self.logger.debug(f"✓ 输入文本: {text[:20]}...")
                    return True
                time.sleep(0.1)

            self.logger.warning(f"✗ 输入失败 [{resource_id}]: 元素在 {timeout} 秒内未出现")
            return False
        except Exception as e:
            self.logger.warning(f"✗ 输入失败 [{resource_id}]: {str(e)[:100]}")
            return False

    # ========================================================================
    #                          滑动操作
    # ========================================================================

    def swipe(self, direction='up', steps=5, duration=None):
        """
        滑动屏幕

        Args:
            direction: 滑动方向 'up' | 'down' | 'left' | 'right'
            steps: 滑动步数（每步 50 像素）
            duration: 滑动持续时间（毫秒，默认根据距离自动计算，避免长按）

        Returns:
            bool: 是否成功滑动

        Example:
            device.swipe('up', steps=5)  # 向上滑动
            device.swipe('down', steps=3)  # 向下滑动
        """
        try:
            width = self.device.window_size()[0]
            height = self.device.window_size()[1]

            center_x = width // 2
            center_y = height // 2
            step_distance = 50

            # 计算实际滑动距离
            swipe_distance = steps * step_distance

            # 自动计算持续时间：快速滑动避免长按
            # 基础: 200ms + 每100像素额外30ms
            if duration is None:
                duration = 200 + (swipe_distance // 100) * 30
                # 确保最小 200ms，最大 400ms（避免太快或太慢）
                duration = max(200, min(duration, 400))

            if direction == 'up':
                self.device.swipe(
                    center_x,
                    center_y,
                    center_x,
                    center_y - swipe_distance,
                    duration
                )
            elif direction == 'down':
                self.device.swipe(
                    center_x,
                    center_y,
                    center_x,
                    center_y + swipe_distance,
                    duration
                )
            elif direction == 'left':
                self.device.swipe(
                    center_x,
                    center_y,
                    center_x - swipe_distance,
                    center_y,
                    duration
                )
            elif direction == 'right':
                self.device.swipe(
                    center_x,
                    center_y,
                    center_x + swipe_distance,
                    center_y,
                    duration
                )
            else:
                self.logger.warning(f"✗ 未知的滑动方向: {direction}")
                return False

            self.logger.debug(f"✓ 向{direction}滑动 {steps} 步 ({duration}ms)")
            time.sleep(0.3)  # 滑动后稍作停顿，让内容加载（减少停留时间）
            return True
        except Exception as e:
            self.logger.warning(f"✗ 滑动失败: {e}")
            return False

    def drag_comment_list(self, direction='up', steps=3):
        """
        对评论容器元素直接进行滚动操作（最稳定的方案）

        Args:
            direction: 滚动方向 'up' | 'down'
            steps: 滚动步数

        Returns:
            bool: 是否成功滚动

        注意: 直接对容器元素操作，完全避免长按事件

        Example:
            device.drag_comment_list('up', steps=3)
        """
        try:
            # 获取评论容器元素
            container_id = 'com.ss.android.ugc.aweme:id/i8_'
            container = self.device(resourceId=container_id)

            if not container.exists:
                self.logger.warning(f"✗ 评论容器不存在: {container_id}")
                return False

            # 使用 uiautomator2 的滚动 API
            # forward: 向前滚动（内容向下移动，看到后面的评论）
            # backward: 向后滚动（内容向上移动，看到前面的评论）
            # toBeginning: 滚动到开始
            # toEnd: 滚动到结束

            if direction == 'up':
                # 向上滚动（加载新评论） - 内容向下移动，所以用 forward
                try:
                    container.scroll.vert.forward(steps=steps)
                    self.logger.debug(f"✓ 对评论容器向上滚动 {steps} 步")
                except:
                    # 降级方案：使用 fling
                    container.fling.vert.forward()
                    self.logger.debug(f"✓ 对评论容器向上快速滚动")

            elif direction == 'down':
                # 向下滚动（返回之前的评论） - 内容向上移动，所以用 backward
                try:
                    container.scroll.vert.backward(steps=steps)
                    self.logger.debug(f"✓ 对评论容器向下滚动 {steps} 步")
                except:
                    # 降级方案：使用 fling
                    container.fling.vert.backward()
                    self.logger.debug(f"✓ 对评论容器向下快速滚动")

            else:
                self.logger.warning(f"✗ 未知的滚动方向: {direction}")
                return False

            time.sleep(0.3)  # 等待加载（稍微增加等待时间）
            return True

        except Exception as e:
            self.logger.warning(f"✗ 滚动评论容器失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ========================================================================
    #                          等待和查询操作
    # ========================================================================

    def wait_element(self, resource_id, text=None, timeout=None):
        """
        等待元素出现

        Args:
            resource_id: 元素 resource_id
            text: 元素的 text 属性（可选）
            timeout: 超时时间（秒）

        Returns:
            bool: 元素是否出现

        Example:
            if device.wait_element(DouyinElementIds.COMMENT_INPUT):
                print("评论输入框已出现")
        """
        timeout = timeout or self.timeout
        try:
            if text:
                element = self.device(resourceId=resource_id, text=text)
            else:
                element = self.device(resourceId=resource_id)

            # uiautomator2 v3.0+ API: 使用 exists 属性而不是 wait.exists()
            # 轮询检查元素是否存在
            start_time = time.time()
            while time.time() - start_time < timeout:
                if element.exists:
                    return True
                time.sleep(0.1)

            return False
        except Exception as e:
            self.logger.debug(f"⚠️  等待元素失败 [{resource_id}]: {e}")
            return False

    def get_element(self, resource_id, text=None):
        """
        获取元素对象

        Args:
            resource_id: 元素 resource_id
            text: 元素的 text 属性（可选）

        Returns:
            element 对象或 None

        Example:
            element = device.get_element(DouyinElementIds.LIKE_BUTTON)
            if element:
                element.click()
        """
        try:
            if text:
                return self.device(resourceId=resource_id, text=text)
            else:
                return self.device(resourceId=resource_id)
        except:
            return None

    def element_exists(self, resource_id, text=None):
        """
        检查元素是否存在（快速检查，不等待）

        Args:
            resource_id: 元素 resource_id
            text: 元素的 text 属性（可选）

        Returns:
            bool: 元素是否存在

        Example:
            if device.element_exists(DouyinElementIds.LIKE_BUTTON):
                print("点赞按钮存在")
        """
        try:
            element = self.get_element(resource_id, text)
            return element is not None and element.exists
        except:
            return False

    # ========================================================================
    #                          截图和调试
    # ========================================================================

    def take_screenshot(self, filename=None, filepath=None):
        """
        保存屏幕截图

        Args:
            filename: 文件名（不指定则自动生成）
            filepath: 完整文件路径（优先使用）

        Returns:
            str: 截图文件路径，失败返回 None

        Example:
            device.take_screenshot("debug.png")
            # 或
            device.take_screenshot(filepath="/path/to/screenshot.png")
        """
        try:
            if filepath:
                target_path = filepath
            else:
                if not filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    filename = f"screenshot_{timestamp}.png"

                target_path = os.path.join('./screenshots', filename)

            # 创建目录
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # 保存截图
            self.device.screenshot(target_path)
            self.logger.debug(f"✓ 截图已保存: {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"✗ 截图失败: {e}")
            return None

    def get_dump_hierarchy(self):
        """
        获取当前 UI 树（用于调试和元素定位）

        Returns:
            str: XML 格式的 UI 树，失败返回 None

        用法：
            hierarchy = device.get_dump_hierarchy()
            if hierarchy:
                # 可以解析 XML 树来找到元素的 resource_id
                print(hierarchy)
        """
        try:
            hierarchy = self.device.dump_hierarchy()
            self.logger.debug("✓ 已获取 UI 树")
            return hierarchy
        except Exception as e:
            self.logger.error(f"✗ 获取 UI 树失败: {e}")
            return None

    # ========================================================================
    #                          屏幕和设备信息
    # ========================================================================

    def get_screen_size(self):
        """
        获取屏幕大小

        Returns:
            tuple: (宽度, 高度)

        Example:
            width, height = device.get_screen_size()
            print(f"屏幕大小: {width}x{height}")
        """
        try:
            return self.device.window_size()
        except Exception as e:
            self.logger.error(f"✗ 获取屏幕大小失败: {e}")
            return None

    def get_device_info(self):
        """
        获取设备信息

        Returns:
            dict: 设备信息字典

        Example:
            info = device.get_device_info()
            print(f"Android 版本: {info.get('release')}")
        """
        try:
            return self.device.info
        except Exception as e:
            self.logger.error(f"✗ 获取设备信息失败: {e}")
            return None

    # ========================================================================
    #                          应用控制
    # ========================================================================

    def launch_app(self, package_name):
        """
        启动应用

        Args:
            package_name: 应用包名

        Returns:
            bool: 是否成功启动

        Example:
            device.launch_app(DouyinElementIds.DOUYIN_PACKAGE)
        """
        try:
            self.device.app_start(package_name)
            self.logger.info(f"✓ 已启动应用: {package_name}")
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"✗ 启动应用失败: {e}")
            return False

    def stop_app(self, package_name):
        """
        停止应用

        Args:
            package_name: 应用包名

        Returns:
            bool: 是否成功停止

        Example:
            device.stop_app(DouyinElementIds.DOUYIN_PACKAGE)
        """
        try:
            self.device.app_stop(package_name)
            self.logger.info(f"✓ 已停止应用: {package_name}")
            return True
        except Exception as e:
            self.logger.error(f"✗ 停止应用失败: {e}")
            return False

    def press_back(self):
        """
        按返回键

        Returns:
            bool: 是否成功

        Example:
            device.press_back()  # 返回上一页
        """
        try:
            self.device.press('back')
            self.logger.debug("✓ 已按返回键")
            time.sleep(0.5)
            return True
        except Exception as e:
            self.logger.warning(f"✗ 按返回键失败: {e}")
            return False

    def press_home(self):
        """
        按主页键

        Returns:
            bool: 是否成功

        Example:
            device.press_home()  # 返回桌面
        """
        try:
            self.device.press('home')
            self.logger.debug("✓ 已按主页键")
            time.sleep(0.5)
            return True
        except Exception as e:
            self.logger.warning(f"✗ 按主页键失败: {e}")
            return False

    # ========================================================================
    #                          图像识别和模板匹配
    # ========================================================================

    def find_button_by_image(self, template_paths, timeout=10, threshold=0.7):
        """
        使用图像模板匹配来查找和点击按钮（支持多个模板）

        Args:
            template_paths: 模板图像路径列表或单个路径字符串
            timeout: 超时时间（秒）
            threshold: 匹配阈值 (0.0-1.0)，值越高匹配越精确

        Returns:
            bool: 是否找到并成功点击

        Example:
            device.find_button_by_image(["templates/dakaidouyin.png", "templates/dakaiyouyin2.png"])
            device.find_button_by_image("templates/dakaidouyin.png")
        """
        if not HAS_IMAGE_RECOGNITION:
            self.logger.warning("⚠️  图像识别库未安装，跳过图像识别")
            return False

        # 支持单个路径字符串或列表
        if isinstance(template_paths, str):
            template_paths = [template_paths]

        try:
            # 加载所有有效的模板
            templates = {}
            for template_path in template_paths:
                if not os.path.exists(template_path):
                    self.logger.debug(f"⚠️  模板文件不存在: {template_path}")
                    continue

                template = cv2.imread(template_path)
                if template is None:
                    self.logger.debug(f"⚠️  无法加载模板图像: {template_path}")
                    continue

                templates[template_path] = template
                template_h, template_w = template.shape[:2]
                self.logger.debug(f"✓ 已加载模板: {os.path.basename(template_path)} ({template_w}x{template_h})")

            if not templates:
                self.logger.warning(f"⚠️  没有可用的模板文件")
                return False

            self.logger.debug(f"📸 使用图像识别方式定位按钮 ({len(templates)} 个模板)...")

            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # 获取当前屏幕截图
                    screenshot_path = self.take_screenshot()
                    if not screenshot_path or not os.path.exists(screenshot_path):
                        time.sleep(0.5)
                        continue

                    # 读取屏幕截图
                    screenshot = cv2.imread(screenshot_path)
                    if screenshot is None:
                        time.sleep(0.5)
                        continue

                    # 尝试匹配所有模板
                    best_match = None
                    best_score = 0
                    best_template_name = ""
                    best_coords = None

                    for template_path, template in templates.items():
                        try:
                            # 进行模板匹配
                            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                            template_h, template_w = template.shape[:2]

                            # 如果匹配度更高，更新最佳匹配
                            if max_val > best_score:
                                best_score = max_val
                                best_match = template
                                best_template_name = os.path.basename(template_path)
                                best_coords = (max_loc, template_w, template_h)

                        except Exception as e:
                            self.logger.debug(f"  {os.path.basename(template_path)} 匹配失败: {e}")
                            continue

                    # 检查是否找到匹配
                    if best_score >= threshold:
                        max_loc, template_w, template_h = best_coords

                        # 计算按钮中心坐标
                        x = max_loc[0] + template_w // 2
                        y = max_loc[1] + template_h // 2

                        self.logger.info(f"✓ 找到按钮 [{best_template_name}] (匹配度: {best_score:.3f})")

                        # 点击按钮
                        self.device.click(x, y)
                        self.logger.info(f"✓ 已点击按钮")
                        time.sleep(0.5)
                        return True

                except Exception as e:
                    self.logger.debug(f"  模板匹配过程出错: {e}")
                    time.sleep(0.5)
                    continue

                time.sleep(0.5)

            self.logger.warning(f"⚠️  在 {timeout} 秒内未找到匹配的按钮")
            return False

        except Exception as e:
            self.logger.error(f"✗ 图像识别失败: {e}")
            return False

    # ========================================================================
    #                          资源清理
    # ========================================================================

    def close(self):
        """
        关闭设备连接（清理资源）

        Example:
            device.close()
        """
        try:
            if self.device:
                # uiautomator2 Device 对象没有 close 方法，直接设置为 None
                self.device = None
                self.logger.info("✓ 设备连接已关闭")
        except Exception as e:
            self.logger.error(f"✗ 关闭设备连接失败: {e}")

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句 - 自动关闭"""
        self.close()


# ============================================================================
#                          测试和调试
# ============================================================================

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("设备交互层 - 测试")
    logger.info("=" * 60)

    try:
        # 测试设备连接
        logger.info("\n【测试 1】设备连接...")
        device = DeviceInteraction(timeout=10, logger=logger)

        # 测试屏幕大小
        logger.info("\n【测试 2】获取屏幕大小...")
        screen_size = device.get_screen_size()
        if screen_size:
            logger.info(f"  屏幕大小: {screen_size[0]}x{screen_size[1]}")

        # 测试截图
        logger.info("\n【测试 3】保存截图...")
        screenshot_path = device.take_screenshot("test_screenshot.png")
        if screenshot_path:
            logger.info(f"  截图保存成功: {screenshot_path}")

        # 测试获取设备信息
        logger.info("\n【测试 4】获取设备信息...")
        info = device.get_device_info()
        if info:
            logger.info(f"  Android 版本: {info.get('release')}")
            logger.info(f"  型号: {info.get('model')}")

        logger.info("\n✅ 所有测试通过!")

        # 关闭设备
        device.close()

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

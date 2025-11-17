# 📸 图像识别按钮点击 - 快速参考

## 核心实现

### 1. 设备交互层 (device_interaction.py)

```python
def find_button_by_image(self, template_paths, timeout=10, threshold=0.7):
    """
    使用图像模板匹配来查找和点击按钮（支持多个模板）
    """
    # 支持列表或单个路径
    if isinstance(template_paths, str):
        template_paths = [template_paths]

    # 加载所有有效的模板
    templates = {}
    for template_path in template_paths:
        if os.path.exists(template_path):
            template = cv2.imread(template_path)
            if template is not None:
                templates[template_path] = template

    if not templates:
        return False

    # 在指定超时内尝试匹配
    start_time = time.time()
    while time.time() - start_time < timeout:
        # 获取屏幕截图
        screenshot = cv2.imread(self.take_screenshot())

        # 匹配所有模板，选择最高匹配度
        best_score = 0
        best_match_info = None

        for template_path, template in templates.items():
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_score:
                best_score = max_val
                best_match_info = (template, template_path, max_loc)

        # 如果找到匹配，点击按钮
        if best_score >= threshold:
            template, template_path, max_loc = best_match_info

            # 计算按钮中心坐标
            h, w = template.shape[:2]
            x = max_loc[0] + w // 2
            y = max_loc[1] + h // 2

            # 点击按钮
            self.device.click(x, y)
            return True

        time.sleep(0.5)

    return False
```

### 2. 视频导航器 (video_navigator.py)

```python
def open_video_by_url(self, video_url):
    """打开视频分享链接"""

    # 使用 adb 打开链接
    subprocess.run([
        'adb', 'shell', 'am', 'start',
        '-a', 'android.intent.action.VIEW',
        '-d', video_url
    ])

    # 等待浏览器加载
    time.sleep(2)

    # 使用图像识别点击"打开"按钮
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    template_paths = [
        os.path.join(template_dir, "dakaidouyin.png"),      # 模板 1
        os.path.join(template_dir, "dakaiyouyin2.png"),     # 模板 2
    ]

    if self.device.find_button_by_image(template_paths, timeout=5, threshold=0.7):
        self.logger.info("✓ 已点击打开按钮")
        time.sleep(2)
    else:
        self.logger.warning("⚠️  未找到打开按钮")

    # 等待抖音应用加载视频页面
    for attempt in range(5):
        time.sleep(2)
        if self._is_in_video_page():
            return True

    return False
```

## 模板文件

### dakaidouyin.png
- **按钮文本**: "打开看看"
- **尺寸**: 215x71 像素
- **格式**: PNG
- **大小**: 15.6 KB

### dakaiyouyin2.png
- **按钮文本**: "打开抖音看精彩视频"
- **尺寸**: 392x73 像素
- **格式**: PNG
- **大小**: 41.5 KB

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| timeout | 5 | 超时时间（秒） |
| threshold | 0.7 | 匹配阈值（0-1） |

### 阈值调整建议

```python
# 模板匹配困难时降低阈值
device.find_button_by_image(paths, threshold=0.6)

# 需要更精确匹配时提高阈值
device.find_button_by_image(paths, threshold=0.8)

# 需要更多尝试时增加超时
device.find_button_by_image(paths, timeout=10)
```

## 日志输出

### 成功情况

```
📸 已加载模板: dakaidouyin.png (215x71)
📸 已加载模板: dakaiyouyin2.png (392x73)
📸 使用图像识别方式定位按钮 (2 个模板)...
✓ 找到按钮 [dakaidouyin.png] (匹配度: 0.895)
✓ 已点击按钮
✓ 已点击谷歌浏览器'打开'按钮
```

### 匹配失败

```
⚠️  在 5 秒内未找到匹配的按钮
⚠️  谷歌浏览器中的'打开'按钮未找到，继续尝试...
```

## 依赖库

```
opencv-python >= 4.5.0
Pillow >= 8.0.0
numpy >= 1.19.0
```

安装：
```bash
pip install opencv-python Pillow numpy
```

## 工作原理

```
1. 加载所有模板文件
   ↓
2. 进入轮询循环（最多 timeout 秒）
   ├─ 获取当前屏幕截图
   ├─ 与所有模板进行匹配
   ├─ 选择最高匹配度的模板
   └─ 如果匹配度 >= threshold → 点击并返回
   ↓
3. 超时仍未找到 → 返回 False
```

## 优势

✅ **最可靠** - 直接匹配视觉效果
✅ **版本无关** - 不受 Chrome/Android 版本影响
✅ **容错能力强** - 支持多个模板
✅ **精确定位** - 自动计算按钮中心
✅ **易于调试** - 清晰的日志输出

## 常见问题

**Q: 找不到按钮怎么办？**
A: 降低匹配阈值，或增加超时时间。

**Q: 误点击其他元素？**
A: 提高匹配阈值，或更新模板图像。

**Q: 需要支持更多按钮样式？**
A: 添加新的模板文件到 templates/ 目录，方法会自动识别。

---

**现在可以直接运行**: `python main.py` ✨

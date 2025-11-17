# 🔧 故障排查和 DEBUG 指南

**创建时间**: 2025-11-17
**版本**: v1.0

---

## 🚨 常见问题和解决方案

### 问题 1: "设备连接失败"

**症状**:
```
✗ 设备连接失败: ...
```

**可能原因**:
1. Android 设备未连接
2. USB 调试未启用
3. adb 驱动问题
4. 网络连接问题

**解决步骤**:
```bash
# 1. 检查设备是否连接
adb devices

# 2. 确认 USB 调试已启用
# 设置 → 关于手机 → 连续点击版本号 → 开发者选项 → USB 调试

# 3. 重新连接
adb kill-server
adb start-server

# 4. 重新授权
# 手机会弹出提示，选择"允许"
```

### 问题 2: "打不开评论区"

**症状**:
```
⚠️  无法打开评论区 - 三种方法都未成功
```

**原因分析**:
1. 视频页面未完全加载
2. UI 元素 ID 不正确
3. 需要手动打开

**解决步骤**:

**方案 A: 检查视频页面是否加载**
```bash
# 查看日志
cat logs/auto_reply_*.log | grep -A5 "视频页面"

# 应该看到:
# ✓ 视频页面已加载
```

**方案 B: 手动打开评论区**
```
1. 手动在手机上点击评论区
2. 确认评论区已打开
3. 再运行脚本
```

**方案 C: 更新元素 ID**
```python
# 在 element_ids.py 中检查:
# COMMENT_BUTTON 是否正确
# COMMENT_COUNT_TEXT 是否正确
# COMMENT_LIST_CONTAINER 是否正确

# 使用 UI 检查工具获取最新 ID:
# uiautomator2 提供的 dump_hierarchy()
```

### 问题 3: "评论无法定位"

**症状**:
```
⚠️  评论未找到
```

**可能原因**:
1. 评论已滑出屏幕
2. 网络延迟导致 UI 未更新
3. 评论内容与预期不符

**解决步骤**:

**增加滑动次数**:
```bash
python main_improved.py
# 选择完整模式 (10 次滑动)
```

**或自定义参数**:
```python
result = workflow.run(
    scroll_times=10,  # 从 5 增加到 10
    max_replies=20
)
```

**查看加载的评论**:
```bash
# 查看收集的评论文件
cat outputs/comments_collected_*.json | python -m json.tool

# 应该能看到所有评论及其坐标
```

### 问题 4: "回复失败或超时"

**症状**:
```
✗ 回复失败: 输入失败
✗ 回复失败: 发送失败
```

**可能原因**:
1. 网络延迟
2. 设备响应慢
3. 输入框未获得焦点

**解决步骤**:

**检查网络连接**:
```bash
# 在手机上运行网络测试
ping 8.8.8.8

# 或通过 adb 检查
adb shell ping 8.8.8.8
```

**增加等待时间**:
目前系统内置的延迟是合理的，无需手动调整。

**查看详细日志**:
```bash
# 查看完整日志
cat logs/auto_reply_*.log

# 查看特定错误
cat logs/auto_reply_*.log | grep -i "失败"
```

**手动测试输入**:
```
1. 打开评论区
2. 手动点击评论，弹出输入框
3. 验证输入框是否正常工作
4. 再运行脚本
```

### 问题 5: "成功率太低"

**症状**:
```
成功率: 40.0%  (预期 80%+)
```

**可能原因**:
1. 网络或设备性能问题
2. 评论内容不稳定（评论被删除）
3. UI 动画导致定位失败

**改进方案**:

**方案 1: 重新启动**
```bash
# 重启设备
adb reboot

# 重启脚本
python 快速启动.py
```

**方案 2: 减少并发负载**
```bash
# 关闭其他应用
adb shell am force-stop com.other.app

# 减少回复数
python main_improved.py  # 选择快速模式
```

**方案 3: 更新系统**
```bash
# 确保依赖库最新
pip install --upgrade uiautomator2
pip install --upgrade opencv-python
```

### 问题 6: "脚本卡住不动"

**症状**:
```
脚本运行中，但没有进展（5 分钟以上没有输出）
```

**可能原因**:
1. 设备无响应
2. 网络断连
3. UI 加载特别慢

**解决步骤**:

**方案 1: 中断并重启**
```bash
# 按 Ctrl+C 中断
# 然后重新运行

# 或在另一个终端强制停止
adb shell am force-stop com.ss.android.ugc.aweme
sleep 3
python 快速启动.py
```

**方案 2: 检查设备状态**
```bash
# 查看设备是否响应
adb shell getprop ro.build.version.release

# 查看抖音是否还在运行
adb shell ps | grep aweme
```

**方案 3: 清除缓存**
```bash
# 清除抖音缓存
adb shell pm clear com.ss.android.ugc.aweme

# 重新打开抖音
adb shell am start -n com.ss.android.ugc.aweme/.ui.main.MainActivity
```

---

## 🔍 DEBUG 模式

### 启用详细日志

**查看日志流**:
```bash
# 实时查看日志
adb logcat | grep -i douyin

# 或用 Python 查看
tail -f logs/auto_reply_*.log
```

### 获取 UI 层级信息

**方法 1: 直接导出**
```bash
# 导出当前屏幕 UI 结构
adb shell uiautomator dump /sdcard/ui.xml

# 下载文件
adb pull /sdcard/ui.xml ./ui_dump.xml

# 查看文件
cat ui_dump.xml | python -m json.tool
```

**方法 2: 使用 Python**
```python
from device_interaction import DeviceInteraction

device = DeviceInteraction()
xml = device.device.dump_hierarchy()

# 保存为文件
with open('ui_dump.xml', 'w') as f:
    f.write(xml)

# 查看 UI 树
print(xml)
```

### 截图保存

**保存当前屏幕截图**:
```python
device = DeviceInteraction()
device.take_screenshot('debug_screenshot.png')

# 或通过 adb
adb shell screencap /sdcard/screenshot.png
adb pull /sdcard/screenshot.png ./
```

---

## 📊 日志分析

### 日志格式

```
2025-11-17 10:30:00,123 - MainImproved - INFO - 连接 Android 设备...
2025-11-17 10:30:01,456 - MainImproved - INFO - 设备连接成功
```

### 查看关键日志

**连接状态**:
```bash
grep "连接" logs/auto_reply_*.log
```

**页面状态**:
```bash
grep "页面\|视频" logs/auto_reply_*.log
```

**评论区状态**:
```bash
grep "评论区" logs/auto_reply_*.log
```

**回复状态**:
```bash
grep "回复" logs/auto_reply_*.log
```

**错误信息**:
```bash
grep -i "error\|失败\|异常" logs/auto_reply_*.log
```

### 生成诊断报告

```python
import json
from pathlib import Path

# 收集所有日志和报告
logs = list(Path('./logs').glob('*.log'))
reports = list(Path('./outputs').glob('*.json'))

print("=== 系统诊断 ===")
print(f"日志文件: {len(logs)} 个")
print(f"报告文件: {len(reports)} 个")

# 显示最新文件
if logs:
    latest_log = sorted(logs)[-1]
    print(f"\n最新日志: {latest_log}")

if reports:
    latest_report = sorted(reports)[-1]
    print(f"最新报告: {latest_report}")
```

---

## 🧪 测试和验证

### 单步测试

**测试 1: 设备连接**
```python
from device_interaction import DeviceInteraction

device = DeviceInteraction()
print("✓ 设备连接成功")
device.close()
```

**测试 2: UI 元素检查**
```python
from device_interaction import DeviceInteraction
from element_ids import DouyinElementIds

device = DeviceInteraction()

# 检查评论按钮
comment_btn = device.device(resourceId=DouyinElementIds.COMMENT_BUTTON)
print(f"评论按钮存在: {comment_btn.exists}")

# 检查评论容器
container = device.device(resourceId=DouyinElementIds.COMMENT_LIST_CONTAINER)
print(f"评论容器存在: {container.exists}")

device.close()
```

**测试 3: 关键字匹配**
```python
from keyword_matcher import KeywordMatcher

matcher = KeywordMatcher()

# 测试评论
test_comments = [
    {"text": "点赞，很喜欢", "user": "用户1"},
    {"text": "支持你，继续加油", "user": "用户2"},
    {"text": "这个不错", "user": "用户3"}
]

matched = matcher.match_comments(test_comments)
print(f"匹配结果: {matched}")
```

**测试 4: 动态定位**
```python
from dynamic_locator import DynamicLocator
from device_interaction import DeviceInteraction

device = DeviceInteraction()
locator = DynamicLocator(device)

# 测试查找
result = locator.find_comment_by_text("点赞")
print(f"查找结果: {result}")

device.close()
```

### 完整流程测试

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整流程测试"""

from main_improved import ImprovedAutomationWorkflow

# 创建工作流
workflow = ImprovedAutomationWorkflow()

# 运行
result = workflow.run(
    scroll_times=3,   # 少滑动几次快速测试
    max_replies=5,    # 只回复 5 条
    keywords_file=None
)

# 打印结果
import json
print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 📝 常见错误和修复

### 错误 1: AttributeError: 'function' object has no attribute 'exists'

**原因**: uiautomator2 版本问题
**修复**:
```bash
pip install --upgrade uiautomator2==2.16.1
```

### 错误 2: ModuleNotFoundError: No module named 'cv2'

**原因**: OpenCV 未安装
**修复**:
```bash
pip install opencv-python
```

### 错误 3: ModuleNotFoundError: No module named 'uiautomator2'

**原因**: 依赖未安装
**修复**:
```bash
pip install -r requirements.txt
# 或手动安装
pip install uiautomator2 opencv-python pillow
```

### 错误 4: ConnectionError: Failed to connect to device

**原因**: 设备未连接或 adb 无法识别
**修复**:
```bash
# 重启 adb 服务
adb kill-server
adb start-server

# 检查连接
adb devices

# 如果设备显示 "offline"，重新插入 USB 并授权
```

---

## 💡 性能优化建议

### 1. 加快执行速度

**减少滑动次数**:
```python
# 从 5 改成 3
result = workflow.run(scroll_times=3)
```

**减少回复条数**:
```python
# 从 20 改成 10
result = workflow.run(max_replies=10)
```

### 2. 提高成功率

**增加等待时间**:
目前系统的等待时间已经优化，无需修改。

**增加滑动次数加载更多评论**:
```python
# 从 5 改成 10
result = workflow.run(scroll_times=10)
```

### 3. 监控资源使用

```bash
# 查看 Python 进程
ps aux | grep python

# 查看 adb 连接状态
adb shell top

# 查看内存使用
adb shell dumpsys meminfo
```

---

## 📞 获得进一步帮助

### 收集诊断信息

```bash
# 生成诊断包
mkdir -p diagnosis
cp logs/* diagnosis/
cp outputs/* diagnosis/
zip -r diagnosis_$(date +%Y%m%d_%H%M%S).zip diagnosis/

# 包含的信息:
# • 所有日志文件
# • 所有报告文件
# • 时间戳
```

### 快速排查清单

- [ ] 设备已连接: `adb devices`
- [ ] USB 调试已启用
- [ ] 抖音应用已打开
- [ ] 已进入视频页面
- [ ] 网络连接正常
- [ ] Python 环境正常: `python --version`
- [ ] 依赖库已安装: `pip list | grep -E "uiautomator|cv2|pillow"`

---

**版本**: v1.0
**更新**: 2025-11-17


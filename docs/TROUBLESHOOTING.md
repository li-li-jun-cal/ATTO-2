# 故障排查指南 - 抖音自动评论回复系统

**最后更新**: 2024 年 11 月
**版本**: 1.0

---

## 问题 1: `module 'uiautomator2' has no attribute 'list_adb_devices'`

### 错误信息
```
2025-11-16 21:21:20,646 - DouyinBot - ERROR - ✗ 设备初始化失败: module 'uiautomator2' has no attribute 'list_adb_devices'
```

### 原因
uiautomator2 库的新版本中移除了 `list_adb_devices()` 方法。

### 解决方案

**已自动修复！** 代码已更新为使用 `adb devices` 命令替代。

#### 手动修复步骤（如果需要）:

1. **更新代码**（已自动完成）:
   ```python
   # 旧方式 (已移除)
   devices = u2.list_adb_devices()

   # 新方式 (已实现)
   import subprocess
   result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
   devices = [line.split()[0] for line in result.stdout.strip().split('\n')[1:] if 'device' in line]
   ```

2. **验证修复**:
   ```bash
   python device_interaction.py
   ```

---

## 问题 2: 无法连接到 Android 设备

### 症状
```
⚠️  无法自动检测设备，请手动指定 device_id
```

### 排查步骤

#### 步骤 1: 检查 ADB 连接
```bash
# 列出所有连接的设备
adb devices

# 预期输出：
# List of attached devices
# emulator-5554          device
# 或
# 192.168.1.100:5555    device
```

如果没有设备显示，进行以下检查：

#### 步骤 2: 检查 USB 调试
在 Android 手机上：
1. 进入 **设置** → **关于手机**
2. 点击 **版本号** 7 次激活开发者选项
3. 进入 **设置** → **开发者选项**
4. 启用 **USB 调试**

#### 步骤 3: 检查 USB 连接
```bash
# 重新连接 USB
adb kill-server
adb start-server

# 重新列出设备
adb devices
```

#### 步骤 4: 手动指定设备
如果自动检测失败，手动指定设备 ID：

编辑 `config.py`:
```python
DEVICE_CONFIG = {
    "device_id": "192.168.1.100:5555",  # 或 "emulator-5554"
    # 其他配置...
}
```

---

## 问题 3: 无法获取设备详细信息

### 症状
```
⚠️  无法获取设备详细信息，继续初始化...
```

### 解决方案
这是个警告，程序会继续运行。不影响功能，但表示某些设备信息无法获取。

**可忽略**，程序会自动跳过此步骤继续。

---

## 问题 4: 抖音应用无法验证

### 症状
```
⚠️  无法验证抖音应用: ...
⚠️  继续初始化，请确保已安装抖音应用
```

### 解决方案
1. **检查抖音是否已安装**:
   ```bash
   adb shell pm list packages | grep douyin
   ```

2. **如果未安装**，在 Android 设备上安装抖音 APP

3. **如果已安装但无法验证**，程序仍会继续运行

---

## 问题 5: 元素找不到

### 症状
```
✗ 点击失败 [com.ss.android.ugc.aweme:id/1r2]: ...
```

### 原因
- 抖音 APP 更新了 UI
- 使用的设备不是 vivo S12

### 解决方案

#### 方案 1: 更新元素 ID

1. **打开 UI Inspector**:
   ```bash
   python -m uiautomator2 init
   # 在浏览器访问: http://localhost:7912
   ```

2. **找到正确的元素 ID**，更新 `element_ids.py`

3. **重新运行程序**

#### 方案 2: 调整超时
编辑 `config.py`:
```python
DEVICE_CONFIG = {
    "long_timeout": 30,  # 增加超时时间
    # 其他配置...
}
```

---

## 问题 6: 关键字匹配失败

### 症状
```
✓ 找到 0 条匹配评论
```

### 排查步骤

1. **检查配置**:
   ```python
   # 确保关键字已启用
   "keywords_to_reply": {
       "很好看": {
           "enabled": True,  # 检查这个
           "reply_templates": ["..."],
           "priority": 1
       }
   }
   ```

2. **检查关键字是否存在于评论中**

3. **调整关键字**:
   ```python
   # 使用更通用的关键字
   "很": True  # 替代 "很好看"
   ```

---

## 问题 7: 回复发送失败

### 症状
```
✗ 回复失败: 发送回复失败
```

### 原因
- 元素 ID 不正确
- 网络延迟太短
- 评论框未正确打开

### 解决方案

增加延迟时间：
```python
TASK_CONFIG = {
    "delay_between_replies": [3, 8],  # 增加延迟
    # 其他配置...
}
```

---

## 问题 8: 日志查看

### 位置
```
./logs/douyin_bot_YYYYMMDD_HHMMSS.log
```

### 查看日志
```bash
# 查看最新日志
tail -f ./logs/douyin_bot_*.log

# 查看错误信息
grep "ERROR" ./logs/douyin_bot_*.log
```

---

## 问题 9: 性能优化

### 程序运行缓慢

**调整延迟参数**:
```python
TASK_CONFIG = {
    "delay_between_replies": [1, 2],  # 减少延迟
    "delay_between_videos": [1, 3],   # 减少延迟
    "scroll_pause_time": 0.5,         # 减少滑动暂停
}
```

### 但注意风险
减少延迟可能会被抖音检测为机器人，建议保持 2-5 秒的延迟。

---

## 问题 10: 设备断线

### 症状
程序中途停止，设备连接断开

### 原因
- USB 线松动
- USB 调试中断
- 设备熄屏或锁屏

### 解决方案

1. **检查 USB 连接**
2. **重新启用 USB 调试**
3. **保持设备屏幕亮着**
4. **重新运行程序**

```bash
adb devices  # 验证连接
python main.py
```

---

## 快速检查清单

启动程序前，逐一检查：

- [ ] ADB 已安装 (`adb devices` 能运行)
- [ ] Android 设备已连接 (`adb devices` 显示设备)
- [ ] USB 调试已启用
- [ ] 抖音 APP 已安装
- [ ] Python 依赖已安装 (`pip install -r requirements.txt`)
- [ ] `config.py` 已配置
- [ ] 设备屏幕处于亮屏状态
- [ ] 网络连接正常

---

## 获取更多帮助

### 查看日志
```bash
# 实时查看日志
tail -f ./logs/douyin_bot_*.log
```

### 查看截图
```bash
# 调试时会保存截图
ls -lh ./screenshots/
```

### 查看代码
```bash
# 查看设备交互代码
python -c "from device_interaction import DeviceInteraction; help(DeviceInteraction)"
```

### 查看文档
- `README.md` - 项目介绍
- `QUICK_START.md` - 快速开始
- `TEST_REPORT.md` - 测试报告
- `ARCHITECTURE.md` - 架构设计

---

## 常见错误信息速查表

| 错误信息 | 原因 | 解决方案 |
|---------|------|--------|
| `list_adb_devices` | API 变更 | ✅ 已修复 |
| 无法连接设备 | USB 未连接 | 检查 USB 和 ADB |
| 元素找不到 | 元素 ID 错误 | 更新 element_ids.py |
| 关键字不匹配 | 关键字配置错 | 检查 config.py |
| 网络超时 | 网络慢 | 增加超时时间 |
| 权限拒绝 | ADB 权限问题 | 重新启用 USB 调试 |

---

## 反馈和支持

如果遇到未列出的问题：

1. **检查日志文件**获取详细错误信息
2. **查看相应的代码注释**
3. **参考 TEST_REPORT.md** 了解测试状态
4. **查看 ARCHITECTURE.md** 理解系统设计

---

## 代码修复记录

### 修复 1: uiautomator2 API 兼容性 (2024-11-16)
- **问题**: `list_adb_devices()` 方法不存在
- **修复**: 使用 `adb devices` 命令替代
- **文件**: `device_interaction.py` (第 34-66 行)
- **状态**: ✅ 已修复

### 修复 2: 应用检查容错 (2024-11-16)
- **问题**: 应用验证失败会中断程序
- **修复**: 改为警告并继续
- **文件**: `device_interaction.py` (第 83-104 行)
- **状态**: ✅ 已修复

---

**最后更新**: 2024 年 11 月
**版本**: 1.0
**所有已知问题都有解决方案** ✅


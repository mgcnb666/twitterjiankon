# Twitter 监控系统 - 饭碗警告版本

只使用饭碗警告（电话/短信/邮件）推送的 Twitter 监控系统




## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/magangchen/crush/twitter-monitor-fwalert

# 安装 Python 依赖
pip3 install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium
```

### 2. 配置饭碗警告

#### 步骤 1：注册饭碗警告

访问 [https://fwalert.com/1216156](https://fwalert.com/1216156)，注册账号并添加联系方式

#### 步骤 2：创建转发规则

#### 步骤 3：配置 webhook URL

保存规则后，复制生成的 webhook URL，编辑 `config.json`:

```json
{
  "twitter_accounts": ["stable", "vitalik"],
  "nitter_instances": [
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com"
  ],
  "check_interval": 1,
  "fwalert_webhook_url": "https://fwalert.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### 3. 测试推送

```bash
python3 test_fwalert.py
```

如果配置正确，您应该会收到：
- 📞 电话通知 - 语音播报测试消息
- 📲 短信通知 - 文本消息
- 📧 邮件通知 - 完整详情

### 4. 运行监控

```bash
# 前台运行（测试用）
python3 monitor.py

# 后台运行（生产环境）
nohup python3 monitor.py > output.log 2>&1 &

# 查看日志
tail -f twitter_monitor.log
```

## 📊 运行效果

```
============================================================
🐦 Twitter 监控启动 (饭碗警告模式)
监控账号: @stable
检查间隔: 1 秒
⏰ 启动时间: 2025-10-26 12:00:00
📱 通知方式: 饭碗警告（电话/短信/邮件）
📌 只推送启动后发布的新推文，避免重复推送
============================================================

检查 @stable 的推文...
首次运行，已扫描 10 条推文
✅ 监控已启动，只推送启动后发布的新推文

[等待新推文...]

检查 @stable 的推文...
扫描到 10 条推文，分析时间...
  📄 '新推文内容...' | 时间: 5s | 距启动: +10s
    ✅ 是新推文！
✨ 发现 1 条新推文
============================================================
📝 新推文 #1:
👤 账号: @stable
📄 内容: Important update...
🕒 时间: 5s
🔗 链接: https://twitter.com/stable/status/...
------------------------------------------------------------
✅ 饭碗警告推送成功  ← 电话/短信/邮件通知
============================================================
```

## ⚙️ 配置说明

### config.json

```json
{
  "twitter_accounts": [
    "stable",           // 监控的 Twitter 账号（可多个）
    "vitalik"
  ],
  "nitter_instances": [  // Nitter 实例列表（按顺序尝试）
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com"
  ],
  "check_interval": 1,   // 检查间隔（秒）
  "notification_title": "stable 新推文",  // 通知标识（用于电话/短信，可选）
  "fwalert_webhook_url": "https://fwalert.com/..." // 饭碗警告 webhook URL
}
```

### 通知标识说明

`notification_title` 用于设置电话和短信通知的简短标识：

- **配置示例**: `"stable 新推文"`
- **电话通知**: 语音播报 "stable 新推文"
- **短信通知**: 显示 "stable 新推文"
- **邮件通知**: 包含完整推文内容

**不同场景的配置**:

```json
// 单个账号
"notification_title": "stable 新推文"

// 多个账号
"notification_title": "Twitter 新推文"

// 自定义提示
"notification_title": "重要推文提醒"

// 不配置则默认为 "{账号名} 新推文"
```

### 检查间隔建议

| 场景 | 推荐间隔 | 说明 |
|------|----------|------|
| 实时监控 | 1 秒 | 最快响应，资源消耗大 |
| 常规监控 | 60 秒 | 平衡性能和实时性 |
| 低频监控 | 300 秒 | 节省资源 |

## 📝 推送内容格式

### 电话/短信（brief）

简短标识，适合语音播报和短信显示：

```
stable 新推文
```

或自定义的标识（通过 `notification_title` 配置）：

```
Twitter 新推文
重要推文提醒
```

### 邮件（details）

完整详情：

```
🐦 @stable 发布了新推文

📝 内容:
Phase 1 of the Pre-Deposit Campaign hit an $825M cap! 
A big thank you to everyone who participated.

🕒 时间: 5m
📊 互动: 💬 45 | 🔁 123 | ❤️ 567
🔗 链接: https://twitter.com/stable/status/...
```

## 🎯 使用场景

### 1. 重要账号实时监控

```json
{
  "twitter_accounts": ["vitalik", "elonmusk"],
  "check_interval": 1
}
```

新推文立即打电话通知！

### 2. 多账号监控

```json
{
  "twitter_accounts": [
    "stable",
    "ethereum",
    "vitalikbuterin",
    "elonmusk"
  ]
}
```

### 3. 24小时后台监控

```bash
nohup python3 monitor.py > output.log 2>&1 &
```

## 🛠️ 故障排查

### 问题：未收到通知

**检查清单**:

1. ✅ Webhook URL 是否正确
2. ✅ 饭碗警告规则是否启用
3. ✅ 联系方式是否验证
4. ✅ 查看日志: `tail -f twitter_monitor.log`
5. ✅ 运行测试: `python3 test_fwalert.py`

### 问题：推送失败

查看日志：

```bash
grep "饭碗警告" twitter_monitor.log | tail -20
```

可能的错误：
- `HTTP 404`: URL 错误或规则已删除
- `HTTP 429`: 超过频率限制
- `⚠️ 未配置饭碗警告 webhook URL`: 配置文件未设置

### 问题：电话未接通

- 确认手机号码正确
- 关闭勿扰模式
- 查看饭碗警告后台推送记录
- 确认账户余额充足

### 问题：检测不到新推文

1. **时间解析问题** - 查看日志中的时间解析信息
2. **Nitter 缓存** - 等待 1-2 分钟让缓存刷新
3. **启动时间** - 只推送启动后发布的推文

## 📚 文件说明

```
twitter-monitor-fwalert/
├── monitor.py          # 主监控脚本
├── config.json         # 配置文件
├── requirements.txt    # Python 依赖
├── test_fwalert.py    # 测试脚本
├── README.md          # 本文档
└── twitter_monitor.log # 运行日志（自动生成）
```

## 🔐 安全建议

1. **保护 Webhook URL** - 不要泄露，不要提交到公开仓库
2. **合理控制频率** - 避免过于频繁检查
3. **定期检查日志** - 确保监控正常运行
4. **备份配置** - 定期备份 `config.json`

## 💡 最佳实践

### 1. 测试先行

使用 `test_fwalert.py` 确保配置正确

### 2. 查看日志

```bash
# 实时日志
tail -f twitter_monitor.log

# 只看新推文
tail -f twitter_monitor.log | grep "新推文"

# 只看推送结果
tail -f twitter_monitor.log | grep "饭碗警告"
```

### 3. 后台运行

```bash
# 启动
nohup python3 monitor.py > output.log 2>&1 &

# 记录进程 ID
echo $! > monitor.pid

# 停止
kill $(cat monitor.pid)

# 查看是否在运行
ps aux | grep monitor.py
```

## 🆚 与 Qmsg 版本对比

| 特性 | 饭碗警告版本 | Qmsg 版本 |
|------|------------|----------|
| QQ 推送 | ❌ | ✅ |
| 电话通知 | ✅ | ❌ |
| 短信通知 | ✅ | ❌ |
| 邮件通知 | ✅ | ❌ |
| 配置复杂度 | 简单 | 简单 |
| 推送成本 | 有费用 | 免费 |

**选择建议**:
- 需要即时响应（打电话）→ 使用饭碗警告版本
- 只需 QQ 通知 → 使用 Qmsg 版本
- 需要双重保障 → 同时使用两个版本

## 📞 支持

如有问题：
1. 查看日志文件 `twitter_monitor.log`
2. 运行测试脚本 `python3 test_fwalert.py`
3. 访问 [饭碗警告官方文档](https://fwalert.com/wiki/)

---

**配置完成后，Twitter 新推文将立即打电话通知！** ☎️📱📧


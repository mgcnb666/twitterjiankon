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


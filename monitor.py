#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter/Nitter 监控脚本 - 饭碗警告版本
使用 Playwright 无头浏览器绕过 Anubis 反爬虫验证
只使用饭碗警告推送，不使用 Qmsg
"""

import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import requests
import random
import re
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright 未安装")
    print("安装方法: pip3 install playwright && playwright install chromium")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TwitterMonitor:
    """Twitter/Nitter 监控器 - 饭碗警告版本"""
    
    def __init__(self, config_file: str = 'config.json'):
        """初始化监控器"""
        self.config = self._load_config(config_file)
        self.start_time = datetime.now()  # 记录程序启动时间
        self.pushed_tweet_ids = set()  # 记录已推送的推文ID（内存中）
        self.playwright = None
        self.browser = None
        self.context = None
        self.first_run = True
        
        if PLAYWRIGHT_AVAILABLE:
            self._init_playwright()
        else:
            logger.error("Playwright 未安装，无法运行")
            logger.error("请运行: pip3 install playwright && playwright install chromium")
    
    def _init_playwright(self):
        """初始化 Playwright"""
        try:
            self.playwright = sync_playwright().start()
            
            # 启动 Chromium 浏览器
            self.browser = self.playwright.chromium.launch(
                headless=True,  # 无头模式
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 创建浏览器上下文
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            logger.info("✅ Playwright 初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Playwright 初始化失败: {e}")
            self.browser = None
            self.context = None
    
    def _load_config(self, config_file: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"配置文件 {config_file} 不存在")
            raise
    
    def parse_tweet_time(self, time_str: str) -> Optional[datetime]:
        """
        解析推文时间字符串
        支持格式：
        - "Oct 26" (今年)
        - "27s" (27秒前)
        - "5m" (5分钟前)
        - "2h" (2小时前)
        - "Oct 26, 2025"
        """
        try:
            now = datetime.now()
            time_str = time_str.strip()
            
            # 相对时间：秒前 (e.g., "27s") - 最优先处理
            if 's' in time_str and time_str.replace('s', '').strip().isdigit():
                seconds = int(time_str.replace('s', '').strip())
                return now - timedelta(seconds=seconds)
            
            # 相对时间：分钟前 (e.g., "5m")
            if 'm' in time_str and time_str.replace('m', '').strip().isdigit():
                minutes = int(time_str.replace('m', '').strip())
                return now - timedelta(minutes=minutes)
            
            # 相对时间：小时前 (e.g., "2h")
            if 'h' in time_str and time_str.replace('h', '').strip().isdigit():
                hours = int(time_str.replace('h', '').strip())
                return now - timedelta(hours=hours)
            
            # 相对时间：天前 (e.g., "3d")
            if 'd' in time_str and time_str.replace('d', '').strip().isdigit():
                days = int(time_str.replace('d', '').strip())
                return now - timedelta(days=days)
            
            # 绝对时间：月日 (e.g., "Oct 26" - 假设是今年)
            if ',' not in time_str and len(time_str.split()) == 2:
                time_str = f"{time_str}, {now.year}"
            
            # 使用 dateutil 解析
            parsed_time = date_parser.parse(time_str, fuzzy=True)
            
            # 如果解析出的时间在未来，说明是去年的
            if parsed_time > now:
                parsed_time = parsed_time.replace(year=now.year - 1)
            
            return parsed_time
            
        except Exception as e:
            logger.warning(f"无法解析时间 '{time_str}': {e}")
            return None
    
    def is_tweet_after_start(self, tweet_time: Optional[datetime]) -> bool:
        """判断推文是否在程序启动之后发布"""
        if not tweet_time:
            return False
        
        # 推文发布时间必须晚于程序启动时间
        return tweet_time > self.start_time
    
    def fetch_tweets_playwright(self, username: str) -> List[Dict]:
        """使用 Playwright 获取推文"""
        if not self.context:
            logger.error("Playwright 未初始化")
            return []
        
        nitter_instances = self.config.get('nitter_instances', [])
        
        for instance in nitter_instances:
            try:
                url = f"{instance}/{username}".replace('//', '/').replace(':/', '://')
                if not url.startswith('http'):
                    url = f"https://{url}"
                
                logger.info(f"尝试访问: {url}")
                
                # 创建新页面
                page = self.context.new_page()
                
                try:
                    # 访问页面，等待加载
                    page.goto(url, wait_until='networkidle', timeout=60000)
                    
                    # 等待 timeline 出现（最多等待 30 秒）
                    try:
                        page.wait_for_selector('.timeline', timeout=30000)
                        logger.info("✅ 页面加载完成，找到 timeline")
                    except PlaywrightTimeout:
                        logger.warning("等待 timeline 超时，尝试解析当前页面")
                    
                    # 额外等待几秒，确保动态内容加载
                    time.sleep(3)
                    
                    # 获取页面 HTML
                    html = page.content()
                    
                    # 检查是否是验证页面
                    if 'Making sure you' in html or 'Anubis' in html:
                        logger.warning(f"{instance} 返回验证页面，等待验证完成...")
                        # 等待更长时间让 Playwright 执行 JavaScript 验证
                        time.sleep(10)
                        html = page.content()
                    
                    # 解析推文
                    tweets = self._parse_tweets(html, username)
                    
                    if tweets:
                        logger.info(f"✅ 从 {instance} 成功获取 {len(tweets)} 条推文")
                        return tweets
                    else:
                        logger.warning(f"{instance} 未获取到推文")
                    
                finally:
                    page.close()
                    
            except Exception as e:
                logger.error(f"访问 {instance} 失败: {e}")
                continue
        
        logger.error("所有 Nitter 实例都失败了")
        return []
    
    def fetch_tweets(self, username: str) -> List[Dict]:
        """获取推文"""
        return self.fetch_tweets_playwright(username)
    
    def _parse_tweets(self, html: str, username: str) -> List[Dict]:
        """解析 HTML 获取推文信息"""
        tweets = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找推文容器
            timeline = soup.find('div', class_='timeline')
            if not timeline:
                logger.warning("未找到 timeline 容器")
                return []
            
            # 查找所有推文项
            tweet_items = timeline.find_all('div', class_='timeline-item')
            logger.info(f"找到 {len(tweet_items)} 个推文容器")
            
            for item in tweet_items[:10]:
                try:
                    # 跳过非推文项
                    if 'show-more' in str(item.get('class', [])):
                        continue
                    
                    # 查找推文链接
                    link = item.find('a', class_='tweet-link')
                    if not link:
                        continue
                    
                    tweet_url = link.get('href', '')
                    if not tweet_url or '/status/' not in tweet_url:
                        continue
                    
                    tweet_id = hashlib.md5(tweet_url.encode()).hexdigest()
                    
                    # 推文内容
                    content_div = item.find('div', class_='tweet-content')
                    content = content_div.get_text(separator=' ', strip=True) if content_div else ''
                    
                    if not content:
                        continue
                    
                    # 时间
                    time_elem = item.find('span', class_='tweet-date') or item.find('a', class_='tweet-date')
                    tweet_time = time_elem.get_text(strip=True) if time_elem else ''
                    
                    # 统计数据
                    stats = {}
                    stats_div = item.find('div', class_='tweet-stats')
                    if stats_div:
                        for icon_class, stat_name in [
                            ('icon-comment', 'comments'),
                            ('icon-retweet', 'retweets'),
                            ('icon-heart', 'likes')
                        ]:
                            icon = stats_div.find('span', class_=icon_class)
                            if icon and icon.parent:
                                stat_text = icon.parent.get_text(strip=True)
                                if stat_text and stat_text != '0':
                                    stats[stat_name] = stat_text
                    
                    tweet = {
                        'id': tweet_id,
                        'username': username,
                        'content': content[:500],
                        'time': tweet_time,
                        'url': f"https://twitter.com{tweet_url}",
                        'stats': stats
                    }
                    
                    tweets.append(tweet)
                    logger.debug(f"成功解析推文: {content[:50]}...")
                    
                except Exception as e:
                    logger.error(f"解析单条推文失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"解析 HTML 失败: {e}")
        
        return tweets
    
    def send_to_fwalert(self, brief: str, details: str):
        """
        发送通知到饭碗警告（fwalert）
        参考: https://fwalert.com/wiki/introduction-to-template-variables/
        
        参数:
            brief: 通知简述（电话和短信会使用此内容）
            details: 通知正文（详细内容）
        """
        webhook_url = self.config.get('fwalert_webhook_url', '')
        
        if not webhook_url or webhook_url == '':
            logger.warning("⚠️ 未配置饭碗警告 webhook URL")
            return
        
        try:
            # 使用查询字符串传递参数
            params = {
                'brief': brief,
                'details': details
            }
            
            response = requests.get(webhook_url, params=params, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ 饭碗警告推送成功")
            else:
                logger.warning(f"饭碗警告推送失败: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"饭碗警告推送出错: {e}")
    
    def format_tweet_message(self, tweet: Dict) -> str:
        """格式化推文消息"""
        msg = f"🐦 @{tweet['username']} 发布了新推文\n\n"
        msg += f"📝 内容:\n{tweet['content']}\n\n"
        msg += f"🕒 时间: {tweet['time']}\n"
        
        if tweet.get('stats'):
            stats = tweet['stats']
            stats_text = []
            if 'comments' in stats:
                stats_text.append(f"💬 {stats['comments']}")
            if 'retweets' in stats:
                stats_text.append(f"🔁 {stats['retweets']}")
            if 'likes' in stats:
                stats_text.append(f"❤️ {stats['likes']}")
            if stats_text:
                msg += f"📊 互动: {' | '.join(stats_text)}\n"
        
        msg += f"🔗 链接: {tweet['url']}"
        return msg
    
    def check_new_tweets(self):
        """检查新推文（基于启动时间戳）"""
        try:
            usernames = self.config.get('twitter_accounts', ['stable'])
            
            for username in usernames:
                logger.info(f"检查 @{username} 的推文...")
                
                tweets = self.fetch_tweets(username)
                
                if not tweets:
                    logger.warning(f"未能获取 @{username} 的推文")
                    continue
                
                # 首次运行，只记录不推送
                if self.first_run:
                    logger.info(f"首次运行，已扫描 {len(tweets)} 条推文")
                    logger.info(f"⏰ 程序启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info("=" * 60)
                    logger.info("📋 最新推文列表:")
                    
                    for idx, tweet in enumerate(tweets[:5], 1):
                        logger.info(f"\n{idx}. {tweet['content'][:80]}...")
                        logger.info(f"   时间: {tweet['time']}")
                    
                    if len(tweets) > 5:
                        logger.info(f"\n... 还有 {len(tweets) - 5} 条推文")
                    
                    logger.info("=" * 60)
                    logger.info(f"✅ 监控已启动，只推送启动后发布的新推文")
                    self.first_run = False
                    continue
                
                # 过滤启动后发布的新推文
                new_tweets = []
                logger.info(f"扫描到 {len(tweets)} 条推文，分析时间...")
                
                for tweet in tweets:
                    tweet_id = tweet['id']
                    
                    # 跳过已推送的推文
                    if tweet_id in self.pushed_tweet_ids:
                        continue
                    
                    # 解析推文时间
                    tweet_time = self.parse_tweet_time(tweet['time'])
                    
                    if tweet_time:
                        time_diff = (datetime.now() - tweet_time).total_seconds()
                        start_diff = (tweet_time - self.start_time).total_seconds()
                        
                        # 详细日志：显示每条推文的时间信息
                        logger.info(f"  📄 '{tweet['content'][:40]}...' | 时间: {tweet['time']} | 解析: {tweet_time.strftime('%H:%M:%S')} | 距现在: {time_diff:.0f}s | 距启动: {start_diff:+.0f}s")
                        
                        # 判断是否在启动后发布
                        if self.is_tweet_after_start(tweet_time):
                            new_tweets.append(tweet)
                            logger.info(f"    ✅ 是新推文！")
                    else:
                        logger.warning(f"⚠️  时间解析失败: {tweet['content'][:30]}... (时间: {tweet['time']})")
                
                # 推送新推文
                if new_tweets:
                    logger.info(f"✨ 发现 {len(new_tweets)} 条新推文")
                    logger.info("=" * 60)
                    
                    for idx, tweet in enumerate(reversed(new_tweets), 1):
                        # 输出详细的推文信息到日志
                        logger.info(f"\n📝 新推文 #{idx}:")
                        logger.info(f"👤 账号: @{tweet['username']}")
                        logger.info(f"📄 内容: {tweet['content']}")
                        logger.info(f"🕒 时间: {tweet['time']}")
                        
                        if tweet.get('stats'):
                            stats = tweet['stats']
                            stats_parts = []
                            if 'comments' in stats:
                                stats_parts.append(f"💬 {stats['comments']}")
                            if 'retweets' in stats:
                                stats_parts.append(f"🔁 {stats['retweets']}")
                            if 'likes' in stats:
                                stats_parts.append(f"❤️ {stats['likes']}")
                            if stats_parts:
                                logger.info(f"📊 互动: {' | '.join(stats_parts)}")
                        
                        logger.info(f"🔗 链接: {tweet['url']}")
                        logger.info("-" * 60)
                        
                        # 记录已推送
                        self.pushed_tweet_ids.add(tweet['id'])
                        
                        # 推送到饭碗警告
                        message = self.format_tweet_message(tweet)
                        # 使用简洁的标识作为 brief（用于电话/短信）
                        brief = self.config.get('notification_title', f"{username} 新推文")
                        self.send_to_fwalert(brief, message)
                        
                        time.sleep(3)
                    
                    logger.info("=" * 60)
                else:
                    logger.info(f"@{username} 没有启动后发布的新推文")
                    
        except Exception as e:
            logger.error(f"检查推文时出错: {e}")
    
    def run(self):
        """运行监控循环"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright 未安装，无法运行")
            logger.error("请运行: pip3 install playwright && playwright install chromium")
            return
        
        logger.info("=" * 60)
        logger.info("🐦 Twitter 监控启动 (饭碗警告模式)")
        logger.info(f"监控账号: {', '.join(['@' + u for u in self.config.get('twitter_accounts', [])])}")
        logger.info(f"检查间隔: {self.config['check_interval']} 秒")
        logger.info(f"⏰ 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📱 通知方式: 饭碗警告（电话/短信/邮件）")
        logger.info(f"📌 只推送启动后发布的新推文，避免重复推送")
        logger.info("=" * 60)
        
        try:
            while True:
                try:
                    self.check_new_tweets()
                    time.sleep(self.config['check_interval'])
                except KeyboardInterrupt:
                    logger.info("\n收到退出信号，正在停止监控...")
                    break
                except Exception as e:
                    logger.error(f"监控循环出错: {e}")
                    time.sleep(self.config['check_interval'])
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.context:
                self.context.close()
        except:
            pass
        
        try:
            if self.browser:
                self.browser.close()
        except:
            pass
        
        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        
        logger.info("已清理 Playwright 资源")


def main():
    """主函数"""
    if not PLAYWRIGHT_AVAILABLE:
        print("\n❌ 错误: Playwright 未安装")
        print("\n安装方法:")
        print("  pip3 install playwright")
        print("  playwright install chromium")
        print("\n安装完成后重新运行脚本。\n")
        return
    
    try:
        monitor = TwitterMonitor('config.json')
        monitor.run()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        raise


if __name__ == '__main__':
    main()


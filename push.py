#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json
import feedparser
import re
from datetime import datetime

# 从GitHub Secrets读取配置
WEBHOOK_URL = os.environ['DINGTALK_WEBHOOK']
SECRET = os.environ['DINGTALK_SECRET']

def generate_sign():
    """钉钉加签计算"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{SECRET}"
    hmac_code = hmac.new(SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign

def send_to_dingtalk(title, content_list):
    """发送到钉钉"""
    if not content_list:
        content_list = ["暂无新热点"]
    
    try:
        timestamp, sign = generate_sign()
        url = f"{WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
        
        markdown_text = f"## {title}\n\n"
        for i, item in enumerate(content_list[:5], 1):
            markdown_text += f"{i}. {item}\n\n"
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": markdown_text
            },
            "at": {"isAtAll": False}
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        print(f"[{datetime.now()}] {title} 发送成功")
        return response.json()
    except Exception as e:
        print(f"[错误] {title}: {e}")
        return None

def fetch_rss_news(feed_url, source_name):
    """抓取RSS新闻"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        feed = feedparser.parse(feed_url, request_headers=headers)
        
        news = []
        for entry in feed.entries[:3]:
            title = entry.get('title', '无标题')
            link = entry.get('link', '')
            title = re.sub('<[^<]+?>', '', title)
            news.append(f"[{title}]({link})")
        
        return news
    except Exception as e:
        print(f"RSS失败 {source_name}: {e}")
        return []

def fetch_ai_news():
    """获取AI热点"""
    sources = [
        'https://www.jiqizhixin.com/rss',
        'https://www.qbitai.com/feed',
    ]
    all_news = []
    for url in sources:
        news = fetch_rss_news(url, 'AI')
        all_news.extend(news)
        time.sleep(1)
    return all_news[:5]

def fetch_design_news():
    """获取工业设计热点"""
    sources = [
        'https://www.pushthink.com/feed',
        'https://medium.com/feed/tag/industrial-design',
    ]
    all_news = []
    for url in sources:
        news = fetch_rss_news(url, 'Design')
        all_news.extend(news)
        time.sleep(1)
    return all_news[:5]

def fetch_ebike_news():
    """获取E-bike热点"""
    sources = [
        'https://electrek.co/guides/ebike/feed/',
        'https://biketo.com/feed',
    ]
    all_news = []
    for url in sources:
        news = fetch_rss_news(url, 'E-bike')
        all_news.extend(news)
        time.sleep(1)
    return all_news[:5]

def fetch_x_trends():
    """获取X热榜"""
    try:
        url = "https://nitter.net/search/rss?f=tweets&q=AI+OR+design+OR+ebike&f-language=en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        feed = feedparser.parse(url, request_headers=headers)
        
        trends = []
        for entry in feed.entries[:5]:
            title = entry.get('title', '')[:80]
            link = entry.get('link', '')
            trends.append(f"{title}... [查看]({link})")
        
        return trends if trends else ["X热榜暂时无法获取"]
    except Exception as e:
        print(f"X热榜失败: {e}")
        return ["X热榜暂时无法获取"]

def main():
    # 设置北京时间（不用pytz，用os.environ）
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()
    today = datetime.now().strftime("%Y年%m月%d日")
    
    print(f"===== 开始推送 {today} =====")
    
    # 1. AI热点
    ai_news = fetch_ai_news()
    send_to_dingtalk(f"🤖 AI热点 | {today}", ai_news)
    time.sleep(2)
    
    # 2. 工业设计
    design_news = fetch_design_news()
    send_to_dingtalk(f"🎨 工业设计 | {today}", design_news)
    time.sleep(2)
    
    # 3. E-bike
    ebike_news = fetch_ebike_news()
    send_to_dingtalk(f"🚲 E-bike动态 | {today}", ebike_news)
    time.sleep(2)
    
    # 4. X热榜
    x_trends = fetch_x_trends()
    send_to_dingtalk(f"🐦 X热榜 | {today}", x_trends)
    
    print("===== 推送完成 =====")

if __name__ == "__main__":
    main()

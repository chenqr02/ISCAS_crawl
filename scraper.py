#!/usr/bin/env python3
"""
ISCAS 2026 Paper Scraper
爬取 paper_id 1000-5000 的论文信息
"""

import requests
import time
import json
import re
import random
from bs4 import BeautifulSoup

BASE_URL = "https://epapers2.org/iscas2026/ESR/paper_details.php?paper_id="
OUTPUT_FILE = "accepted_papers.json"
START_ID = 1000
END_ID = 3500
DELAY = 0.05  

# 请求头伪装
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "Referer": "https://epapers2.org/iscas2026/",
}

# 创建 session 保持连接
session = requests.Session()
session.headers.update(HEADERS)

def scrape_paper(paper_id):
    """爬取单个论文信息"""
    url = f"{BASE_URL}{paper_id}"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        
        # 检查是否为 reject
        if "The following errors have occurred and must be corrected" in content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # 提取信息
        paper_info = {"paper_id": paper_id}
        
        # Final Decision
        match = re.search(r'Final Decision:\s*(.+?)(?:\n|$)', text)
        if match:
            paper_info["final_decision"] = match.group(1).strip()
        
        # Track ID
        match = re.search(r'Track ID:\s*(.+?)(?:\n|$)', text)
        if match:
            paper_info["track_id"] = match.group(1).strip()
        
        # Selected Theme(s)
        match = re.search(r'Selected Theme\(s\):\s*(.+?)(?:\n|$)', text)
        if match:
            paper_info["selected_themes"] = match.group(1).strip()
        
        return paper_info
        
    except Exception as e:
        print(f"Error scraping paper {paper_id}: {e}")
        return None

def main():
    accepted_papers = []
    
    print(f"开始爬取 paper_id {START_ID} - {END_ID}")
    
    for paper_id in range(START_ID, END_ID + 1):
        result = scrape_paper(paper_id)
        
        if result:
            accepted_papers.append(result)
            print(f"[ACCEPT] Paper {paper_id}: {result.get('final_decision', 'N/A')}")
        else:
            print(f"[REJECT/ERROR] Paper {paper_id}")
        
        # 每100个保存一次，防止中断丢失数据
        if paper_id % 100 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(accepted_papers, f, ensure_ascii=False, indent=2)
            print(f"--- 已保存 {len(accepted_papers)} 条记录 ---")
        
        # 随机延迟，避免被检测
        time.sleep(DELAY + random.uniform(0, 0.1))
    
    # 最终保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(accepted_papers, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成! 共爬取 {len(accepted_papers)} 篇 accepted 论文")
    print(f"结果已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

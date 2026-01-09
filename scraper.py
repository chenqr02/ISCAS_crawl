#!/usr/bin/env python3
"""
ISCAS Paper Scraper
爬取指定年份会议的论文信息
"""

import requests
import time
import json
import re
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm

# 配置参数
YEAR = 2026  # 会议年份
BASE_URL = f"https://epapers2.org/iscas{YEAR}/ESR/paper_details.php?paper_id="
TRACKS_URL = f"https://epapers2.org/iscas{YEAR}/ESR/display_tracks.php"
OUTPUT_FILE = "accepted_papers.json"
TRACKS_FILE = "tracks.json"
START_ID = 1000
END_ID = 3500
DELAY = 0.1
MAX_RETRIES = 3
RETRY_DELAY = 2  # 重试等待时间（秒）
MAX_WORKERS = 10  # 并发线程数

# 请求头伪装
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "Referer": "https://epapers2.org/iscas2026/",
}

# 创建线程锁用于保护共享资源
lock = threading.Lock()

def fetch_and_save_tracks():
    """从官网动态获取Track列表并保存到JSON文件"""
    try:
        print("正在从官网获取Track列表...")
        response = requests.get(TRACKS_URL, headers=HEADERS, timeout=10, proxies={'http': None, 'https': None})
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tracks = {}
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                track_id = cells[0].get_text(strip=True)
                track_name = cells[1].get_text(strip=True)
                if track_id and track_name:
                    tracks[track_id] = track_name
        
        # 保存到JSON文件
        with open(TRACKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, ensure_ascii=False, indent=2)
        
        print(f"成功获取并保存 {len(tracks)} 个Track到 {TRACKS_FILE}")
        return tracks
    except Exception as e:
        print(f"获取Track列表失败: {e}")
        return {}

def scrape_paper(paper_id):
    """爬取单个论文信息"""
    url = f"{BASE_URL}{paper_id}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10, proxies={'http': None, 'https': None})
            response.encoding = 'utf-8'
            response.raise_for_status()
            content = response.text

            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()

            paper_info = {"paper_id": paper_id}

            # 提取论文标题
            title_match = re.search(r'Paper Title:\s*(.+?)(?:\n|$)', text)
            if title_match:
                paper_info["paper_title"] = title_match.group(1).strip()
            else:
                paper_info["paper_title"] = "N/A"

            # 提取最终决定
            match = re.search(r'Final Decision:\s*(.+?)(?:\n|$)', text)
            if match and "accept" in match.group(1).lower():
                paper_info["final_decision"] = match.group(1).strip()
            else:
                paper_info["final_decision"] = "Missing or Reject"

            # 提取Track ID
            match = re.search(r'Track ID:\s*(.+?)(?:\n|$)', text)
            if match:
                paper_info["track_id"] = match.group(1).strip()

            # 提取Selected Theme(s)
            match = re.search(r'Selected Theme\(s\):\s*(.+?)(?:\n|$)', text)
            if match:
                paper_info["selected_themes"] = match.group(1).strip()

            return paper_info

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return None

def main():
    print(f"=" * 60)
    print(f"ISCAS {YEAR} Paper Scraper")
    print(f"=" * 60)
    
    # 首先获取并保存Track列表
    track_names = fetch_and_save_tracks()
    
    accepted_papers = []
    total_papers = END_ID - START_ID + 1

    print(f"\n开始爬取 paper_id {START_ID} - {END_ID}")
    print(f"使用 {MAX_WORKERS} 个并发线程\n")

    # 使用线程池并发爬取
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_id = {executor.submit(scrape_paper, paper_id): paper_id
                        for paper_id in range(START_ID, END_ID + 1)}
        
        # 使用tqdm显示进度
        with tqdm(total=total_papers, desc="爬取进度", unit="篇") as pbar:
            # 处理完成的任务
            for future in as_completed(future_to_id):
                paper_id = future_to_id[future]
                
                try:
                    result = future.result()
                    
                    if result:
                        dec = result.get('final_decision', 'N/A').lower()
                        if 'accept' in dec:
                            with lock:
                                accepted_papers.append(result)
                                pbar.set_postfix({"已接收": len(accepted_papers)})
                    
                    # 每处理100个论文保存一次
                    if pbar.n % 100 == 0 and pbar.n > 0:
                        with lock:
                            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                                json.dump(accepted_papers, f, ensure_ascii=False, indent=2)
                    
                except Exception as e:
                    pass
                
                # 更新进度条
                pbar.update(1)
                
                # 添加小延迟避免请求过快
                time.sleep(DELAY)

    # 最终保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(accepted_papers, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"完成! 共处理 {total_papers} 篇论文")
    print(f"其中 accepted 论文: {len(accepted_papers)} 篇")
    print(f"结果已保存到 {OUTPUT_FILE}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()

# ISCAS 2026 Paper Tracker

爬取并可视化 ISCAS 2026 会议论文录用情况。

## 功能

- 爬取 paper_id 1000-3500 的论文信息
- 可视化展示各 track 的论文分布
- 标注尚未出结果的 track

## 使用方法

### 1. 爬取数据

```bash
pip install requests beautifulsoup4
python scraper.py
```

### 2. 查看可视化

```bash
python3 -m http.server 8080
```

访问 http://localhost:8080/visualization.html


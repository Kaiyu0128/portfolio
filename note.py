import asyncio
import csv
import html
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE = Path(__file__).resolve().parent
CONFIG = BASE / 'config.json'
DB = BASE / 'articles.db'
DASHBOARD = BASE / 'dashboard.html'
CSV = BASE / 'ranked_articles.csv'
WEIGHTS = {'aiエージェント': 30, 'saas': 30, '個人開発': 30, '起業': 25, '自動化': 25, '生成ai': 20, 'python': 20, 'llm': 20, 'マーケティング': 15, '副業': 10}


def valid_url(url):
    parsed = urlparse(url)
    return parsed.hostname in ('note.com', 'www.note.com') and bool(re.fullmatch(r'/[^/]+/n/[a-zA-Z0-9_-]+/?', parsed.path))


def normalize(url):
    parsed = urlparse(url)
    return f'https://note.com{parsed.path.rstrip("/")}'


def score(title, keyword):
    t = title.lower()
    points = sum(v for k, v in WEIGHTS.items() if k in t)
    if keyword.lower() in t:
        points += 10
    return min(100, points)


def connect():
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS articles (
        url TEXT PRIMARY KEY, title TEXT NOT NULL, keyword TEXT NOT NULL,
        score INTEGER NOT NULL, first_seen TEXT NOT NULL)''')
    conn.commit()
    return conn


async def search(page, keyword, limit, scrolls):
    url = f'https://note.com/search?q={quote(keyword)}'
    response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
    if response and response.status >= 400:
        print(f'{keyword}: HTTP {response.status}')
        return []
    try:
        await page.locator('a[href*="/n/"]').first.wait_for(state='attached', timeout=15000)
    except PlaywrightTimeoutError:
        print(f'{keyword}: 記事リンクなし')
        return []
    results = {}
    for _ in range(scrolls):
        items = await page.locator('a[href*="/n/"]').evaluate_all('''nodes => nodes.map(a => {
          const card = a.closest('article') || a.parentElement;
          const heading = card?.querySelector('h1,h2,h3,h4');
          return {url: a.href, title: heading?.innerText?.trim() || a.innerText?.trim() || a.getAttribute('aria-label') || a.getAttribute('title') || a.querySelector('img')?.alt || card?.innerText?.trim() || ''};
        })''')
        for item in items:
            if not valid_url(item['url']):
                continue
            link = normalize(item['url'])
            title = re.sub(r'\s+', ' ', item['title']).strip()
            if link not in results or (len(title) > len(results[link]) and title):
                results[link] = title
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
        await page.mouse.wheel(0, 1600)
        await page.wait_for_timeout(1300)
    return [{'url': u, 'title': t, 'keyword': keyword} for u, t in list(results.items())[:limit]]


def export(conn):
    rows = conn.execute('SELECT url,title,keyword,score,first_seen FROM articles ORDER BY score DESC,first_seen DESC').fetchall()
    with CSV.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'title', 'keyword', 'score', 'first_seen'])
        writer.writerows(rows)
    cards = []
    for url, title, keyword, points, first_seen in rows:
        safe_url = html.escape(url, quote=True)
        cards.append(f'<article class="card" data-score="{points}"><div class="top"><span>{points}/100点</span><small>{html.escape(keyword)}</small></div><h2>{html.escape(title or "タイトル未取得")}</h2><p>{html.escape(first_seen[:10])}</p><a href="{safe_url}" target="_blank" rel="noopener noreferrer">noteで記事を読む ↗</a></article>')
    content = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>note Agent</title><style>
    *{box-sizing:border-box}body{font-family:system-ui,-apple-system,sans-serif;background:#10141c;color:#f5f6fa;margin:0}header{padding:36px 6%;border-bottom:1px solid #343a46}h1{margin:0 0 12px}p{color:#9ba6b8}nav{padding:20px 6%;display:flex;gap:10px}button{background:#293241;color:white;border:0;border-radius:8px;padding:10px 15px;cursor:pointer}main{padding:0 6% 50px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.card{background:#1c2430;border:1px solid #354052;border-radius:12px;padding:22px}.top{display:flex;justify-content:space-between;color:#7de0b2}.card h2{font-size:17px;line-height:1.6;min-height:80px}.card a{display:inline-block;margin-top:12px;background:#198b62;color:white;text-decoration:none;padding:11px 15px;border-radius:8px}
    </style></head><body><header><h1>note Article Agent</h1><p>記事収集・ランキング（スキは記事を読んで手動で操作）</p><p>収集記事数: __COUNT__</p></header><nav><button onclick="filter(0)">すべて</button><button onclick="filter(40)">40点以上</button><button onclick="filter(70)">70点以上</button></nav><main>__CARDS__</main><script>function filter(n){document.querySelectorAll('.card').forEach(e=>e.style.display=Number(e.dataset.score)>=n?'':'none')}</script></body></html>'''
    DASHBOARD.write_text(content.replace('__COUNT__', str(len(rows))).replace('__CARDS__', '\n'.join(cards)), encoding='utf-8')
    return len(rows)


async def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    conn = connect()
    added = 0
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=bool(config.get('headless', True)))
            try:
                page = await browser.new_page(locale='ja-JP', viewport={'width': 1440, 'height': 900})
                for keyword in config['keywords']:
                    try:
                        items = await search(page, keyword, int(config.get('max_articles_per_keyword', 20)), int(config.get('max_scrolls', 5)))
                        for item in items:
                            title = item['title'] or 'タイトル未取得'
                            cursor = conn.execute('INSERT OR IGNORE INTO articles VALUES (?,?,?,?,?)', (item['url'], title, keyword, score(title, keyword), datetime.now(timezone.utc).isoformat()))
                            added += cursor.rowcount
                        conn.commit()
                        print(f'{keyword}: {len(items)}件取得')
                    except Exception as exc:
                        print(f'{keyword}: エラー {type(exc).__name__}: {exc}')
                    await asyncio.sleep(float(config.get('delay_seconds', 3)))
            finally:
                await browser.close()
        total = export(conn)
        print(f'新規 {added}件 / 累計 {total}件 / {DASHBOARD}')
    finally:
        conn.close()


if __name__ == '__main__':
    asyncio.run(main())

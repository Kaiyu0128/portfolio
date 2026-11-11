"""Apply likes automatically to discovered articles based on score criteria."""
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.async_api import async_playwright
from note import BASE, DB, valid_url, normalize

CONFIG = BASE / 'config.json'
STATE = BASE / 'note_storage_state.json'


def now():
    return datetime.now(timezone.utc)


def setup_db(db):
    db.execute('''CREATE TABLE IF NOT EXISTS like_log (
        url TEXT PRIMARY KEY, liked_at TEXT NOT NULL, status TEXT NOT NULL)''')
    db.commit()


def count_since(db, hours):
    threshold = (now() - timedelta(hours=hours)).isoformat()
    return db.execute("SELECT COUNT(*) FROM like_log WHERE status='liked' AND liked_at >= ?", (threshold,)).fetchone()[0]


async def run():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    settings = config.get('likes', {})
    if not settings.get('enabled', False):
        print('スキ機能は無効です。')
        return
    if not STATE.exists():
        print('ログイン状態が未設定です。READMEを参照してください。')
        return

    hourly = min(int(settings.get('max_per_hour', 16)), 16)
    daily = min(int(settings.get('max_per_24h', 100)), 100)
    min_score = int(settings.get('min_score', 20))
    if hourly < 1 or daily < 1:
        return

    db = sqlite3.connect(DB)
    setup_db(db)
    try:
        # データベースから未処理かつ指定スコア以上の記事を取得
        cursor = db.execute('''
            SELECT url FROM articles 
            WHERE score >= ? 
            AND url NOT IN (SELECT url FROM like_log)
            ORDER BY score DESC, first_seen DESC
        ''', (min_score,))
        target_urls = [row[0] for row in cursor.fetchall()]

        if not target_urls:
            print('スキ対象の新しい記事はありません。')
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=bool(config.get('headless', True)))
            try:
                context = await browser.new_context(storage_state=str(STATE), locale='ja-JP')
                page = await context.new_page()
                
                for raw in target_urls:
                    if not isinstance(raw, str) or not valid_url(raw):
                        continue
                    url = normalize(raw)
                    
                    if count_since(db, 1) >= hourly or count_since(db, 24) >= daily:
                        print('設定した時間・日間の回数上限に達したため停止')
                        break
                        
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    if not response or response.status != 200:
                        print('記事が開けません。スキップ:', url)
                        continue
                        
                    button = page.get_by_role('button', name='スキ', exact=True)
                    try:
                        await button.wait_for(state='visible', timeout=10000)
                        if await button.count() != 1:
                            raise RuntimeError('スキボタンが一意でない')
                        
                        pressed = await button.get_attribute('aria-pressed')
                        if pressed == 'true':
                            print('すでにスキ済み:', url)
                            db.execute('INSERT OR IGNORE INTO like_log VALUES (?,?,?)', (url, now().isoformat(), 'already_liked'))
                            db.commit()
                            continue
                            
                        await button.click(timeout=10000)
                        await page.wait_for_timeout(1200)
                        
                        if await button.get_attribute('aria-pressed') != 'true':
                            print('スキ成功を確認できないため停止:', url)
                            break
                            
                        db.execute('INSERT OR IGNORE INTO like_log VALUES (?,?,?)', (url, now().isoformat(), 'liked'))
                        db.commit()
                        print('スキ成功:', url)
                    except Exception as exc:
                        print('スキ操作を安全に確認できずスキップ:', type(exc).__name__, str(exc)[:200])
                        # エラー時に全体の処理を落とさず継続する場合は continue に変更してください
                        break
                        
                    await asyncio.sleep(max(float(settings.get('delay_seconds', 30)), 10))
            finally:
                await browser.close()
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(run())

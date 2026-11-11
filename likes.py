"""Apply likes automatically using direct API requests with CSRF and payload support."""
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import httpx

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


def extract_note_key(url):
    """URLからnoteのノートキー（例: n062b15b98ef5）を抽出する"""
    parts = url.rstrip('/').split('/')
    if 'n' in parts:
        idx = parts.index('n')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


async def run():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    settings = config.get('likes', {})
    if not settings.get('enabled', False):
        print('スキ機能は無効です。')
        return
    if not STATE.exists():
        print('ログイン状態が未設定です。')
        return

    hourly = min(int(settings.get('max_per_hour', 16)), 16)
    daily = min(int(settings.get('max_per_24h', 100)), 100)
    min_score = int(settings.get('min_score', 20))
    if hourly < 1 or daily < 1:
        return

    # note_storage_state.json からCookieと認証トークンを読み込む
    state_data = json.loads(STATE.read_text(encoding='utf-8'))
    cookies = {c['name']: c['value'] for c in state_data.get('cookies', [])}
    auth_token = cookies.get('note_gql_auth_token', '')

    db = sqlite3.connect(DB)
    setup_db(db)
    try:
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

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://note.com/",
            "Origin": "https://note.com",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(cookies=cookies, headers=headers, timeout=15.0, follow_redirects=True) as client:
            for raw in target_urls:
                if not isinstance(raw, str) or not valid_url(raw):
                    continue
                url = normalize(raw)
                
                if count_since(db, 1) >= hourly or count_since(db, 24) >= daily:
                    print('設定した時間・日間の回数上限に達したため停止')
                    break

                note_key = extract_note_key(url)
                if not note_key:
                    print('ノートキーが抽出できません:', url)
                    continue

                try:
                    # 1. 記事情報をルックアップして現在の状態を確認
                    lookup_url = f"https://note.com/api/v3/notes/lookup?keys={note_key}&fields=key,is_liked,like_count"
                    res = await client.get(lookup_url)
                    
                    if res.status_code != 200:
                        print(f'記事のルックアップに失敗 (Status {res.status_code}): {url}')
                        continue
                        
                    data = res.json().get('data', {})
                    is_liked = False
                    if isinstance(data, dict):
                        is_liked = data.get(note_key, {}).get('is_liked', False)
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('key') == note_key:
                                is_liked = item.get('is_liked', False)
                                break
                    
                    if is_liked:
                        print('すでにスキ済み:', url)
                        db.execute('INSERT OR IGNORE INTO like_log VALUES (?,?,?)', (url, now().isoformat(), 'already_liked'))
                        db.commit()
                        continue

                    # 2. スキAPIへPOSTリクエスト（JSONペイロード付き）を送信
                    like_api_url = f"https://note.com/api/v3/notes/{note_key}/likes"
                    post_res = await client.post(like_api_url, json={})

                    if post_res.status_code in [200, 201]:
                        db.execute('INSERT OR IGNORE INTO like_log VALUES (?,?,?)', (url, now().isoformat(), 'liked'))
                        db.commit()
                        print('API直叩きによるスキ成功:', url)
                    else:
                        print(f'【失敗】APIエラー (Status {post_res.status_code}): {url} - {post_res.text[:150]}')

                except Exception as exc:
                    print('通信中にエラー:', type(exc).__name__, str(exc)[:200])
                    continue

                await asyncio.sleep(max(float(settings.get('delay_seconds', 30)), 10))

    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(run())

"""Run locally to sign in to note and save Playwright storage state."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(locale='ja-JP')
        page = await context.new_page()
        await page.goto('https://note.com/login')
        input('ブラウザでログインを完了したらEnterを押してください: ')
        await context.storage_state(path=str(Path(__file__).resolve().parent / 'note_storage_state.json'))
        await browser.close()
        print('ログイン状態を保存しました。公開リポジトリにアップロードしないでください。')

if __name__ == '__main__':
    asyncio.run(main())

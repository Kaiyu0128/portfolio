# note Article Agent

無料の GitHub Actions で note の公開検索結果を毎日収集し、SQLite・CSV・HTML に保存します。**スキの自動実行は含みません**。記事を読んでスキする場合は note 側で手動操作してください。

## Macでテスト

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 note.py
open dashboard.html
```

## Macを閉じて毎日実行する

1. GitHub で新しい **private** リポジトリを作成する（無料プランの利用枠・制限に注意）。
2. このフォルダの中身を **`.github/workflows/daily.yml` も含めて** リポジトリにアップロードする。
3. GitHub の **Settings → Actions → General → Workflow permissions** で **Read and write permissions** を選択する。組織ポリシーによって選択できない場合がある。
4. **Actions → Daily note article discovery → Run workflow** で初回実行。
5. 以後、毎日 **20:15 JST 前後** に実行（GitHub の schedule は遅延・スキップの可能性あり）。
6. 更新された `dashboard.html` はリポジトリ内でダウンロードしてブラウザで開く。GitHub Pages での公開はプライバシー・無料プランの制約を確認してから検討する。

**注意:** private repo の無料 Actions 分数には月間上限があり、利用条件が変わる可能性があります。毎日のブラウザ起動時間により枠を超えることがあります。GitHub は長期間活動のない public repo の scheduled workflows を無効化する場合があります。サイト構造が変わると収集できなくなる可能性があります。サイトの規約やアクセス制限に従ってください。

## 出力

- `articles.db`：SQLite 履歴（重複除外）
- `ranked_articles.csv`：スコア順の一覧
- `dashboard.html`：スマホ・PCブラウザで確認できる静的画面

## 注意点

スコアはタイトルのキーワード一致による簡易評価です。記事本文のAI解析ではありません。CSV/HTMLは各回で再生成されますが、SQLiteの履歴は維持されます。GitHub Actionsでデータをコミットするにはリポジトリの書き込み権限が必要です。

## 承認済み記事へのスキ（追加機能）

`config.json` の `likes` で **1時間16件、直近24時間80件**を上限として設定しています。これは公式の安全な上限ではなく、過去の非公式報告の100件/24時間・20件/時間の80%を仮定した設定です。**ロックされない保証はありません。** 上限検知・UI変更・認証切れでは処理を停止します。

**重要:** 検索結果へ無差別にスキすることはありません。`approved_urls.json` に自分で読んで承認した記事URLを配列として登録した場合だけ操作します。初期値は `[]` なので自動スキは発生しません。

1. Macで `python3 save_login.py` を実行し、表示されたブラウザでnoteにログインします。
2. 生成された `note_storage_state.json` はログイン情報を含むため **絶対にGitHubへアップロードしない** でください。ローカルで `base64 < note_storage_state.json | tr -d '\n' | pbcopy` を実行してクリップボードへコピーします。
3. GitHubのリポジトリ → Settings → Secrets and variables → Actions → New repository secret に `NOTE_STORAGE_STATE_B64` という名前で貼り付けます。
4. `approved_urls.json` を ` ["https://note.com/username/n/n123456789abc"] ` のように、実際に読んで承認したURLで更新し、GitHubにコミットします。
5. Actionsからワークフローを手動実行します。Macを閉じていても定期実行できます。

スキボタンのDOMや状態表現はnote側で変更される可能性があります。現行コードは `role=button`, 名前 `スキ`, `aria-pressed` の変化を条件としており、**実サイトでの動作検証は未実施**です。条件が一致しない場合は操作を中止し、成功を偽装しません。GitHub Actionsの無料利用にはプラン・リポジトリ種別に応じた制約があります。クラウド上のログインセッションは期限切れになる場合があります。


## v5: 承認制・毎時実行

- `approved_urls.json` に自分で承認した記事のURLを JSON 配列で登録してください。検索結果の自動承認はしません。
- GitHub Actions は毎時15分頃に実行されます（混雑時は遅延することがあります）。
- `config.json` の `likes.max_per_hour=16`、`likes.max_per_24h=100` を適用します。これは公式に保証された安全な上限ではありません。
- `articles.db` の `like_log` をコミットして、実行をまたぐ重複と直近1時間・24時間の上限を判定します。
- ログインセッションは `NOTE_STORAGE_STATE_B64` という GitHub Actions Secret にのみ保存し、リポジトリにコミットしないでください。
- 画面の `aria-pressed` が確認できない場合は停止します。note の実画面での動作は未検証です。

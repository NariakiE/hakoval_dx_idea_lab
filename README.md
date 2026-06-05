# HAKOVAL DX Idea Lab

現場から集めた「こんなのあったらいいな」というDXアイデアを、カテゴリ別に公開し、いいね・クリック・インプレッション・匿名コメントを集めるためのStreamlitプロトタイプです。

## できること

- カテゴリ別のアイデア表示
- 画像付きアイデアカードの表示
- いいね、詳しく見る、表示回数の記録
- ハート表示と累計いいね数の表示
- 詳細ページでの説明、画像、関連URL表示
- 匿名コメントの受付
- 運営側だけが見る分析ダッシュボード
- MVP候補ランキング
- コメントから具体化するための要件化メモ
- 分析CSVのダウンロード

## 起動方法

```bash
cd hakoval_dx_prototype
python3 -m streamlit run app.py
```

## データ

ローカルで起動するだけなら、反応データは同じフォルダの `hakoval_dx.db` にSQLite形式で保存されます。

Streamlit Cloudなどで公開する場合は、Supabaseに保存できます。`SUPABASE_URL` とキーを設定すると、自動でSupabase保存に切り替わります。

## Supabase公開設定

1. SupabaseのSQL Editorで `supabase_schema.sql` を実行します。
2. Streamlit CloudのSecretsに以下を設定します。

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "xxxxx"
SUPABASE_IMAGE_BUCKET = "idea-images"
ADMIN_PASSWORD = "任意の管理パスワード"
```

`SUPABASE_SERVICE_ROLE_KEY` はブラウザに直接出さず、Streamlit Secretsだけに保存してください。

ローカルSQLiteの既存データをSupabaseへ移す場合は、環境変数を設定してから一度だけ実行します。

```bash
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="xxxxx"
export SUPABASE_IMAGE_BUCKET="idea-images"
python3 migrate_sqlite_to_supabase.py
```

## 運営画面

プロトタイプ用の初期パスワードは `hakoval-admin` です。
公開時は環境変数 `HAKOVAL_ADMIN_PASSWORD` または Streamlit Secrets の `ADMIN_PASSWORD` を設定してください。

## 次の拡張候補

- 運営画面のパスワード保護
- GitHub Issue作成連携
- Streamlit Community Cloudへの公開
- LP/画面モックのURL登録と詳細ページ表示
- コメントのAI要約とMVP要件自動生成

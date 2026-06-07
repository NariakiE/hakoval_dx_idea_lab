from __future__ import annotations

import sqlite3
import uuid
import os
import html
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

try:
    from supabase import Client, create_client
except ImportError:
    Client = Any
    create_client = None


APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "hakoval_dx.db"
UPLOAD_DIR = APP_DIR / "uploads"
SUPABASE_IMAGE_BUCKET = os.environ.get("SUPABASE_IMAGE_BUCKET", "idea-images")

DEFAULT_IMAGE_BY_TITLE = {
    "業者側の紙の日報をデジタル化（常用工事記入可能）": "generated_assets/digital-daily-report.png",
    "現場マニュアルAI検索": "generated_assets/manual-ai-search.png",
    "定例会議メモから議事録・メール自動作成": "generated_assets/meeting-minutes-ai.png",
    "音声発注・手配アシスタント": "generated_assets/voice-order-assistant.png",
    "資材注文アプリ": "generated_assets/material-order-app-pr.png",
    "クレアポ（クレーン手配管理）": "generated_assets/cleapo-crane-order-pr.png",
    "カンベル（現場監督ルーティン管理）": "generated_assets/kanbel-routine-task-pr.png",
    "新規入場者教育AIチェック": "generated_assets/safety-orientation-ai.png",
    "現場横断Power BIダッシュボード": "generated_assets/cross-site-dashboard.png",
}

FEATURED_IDEA_TITLES = [
    "カンベル（現場監督ルーティン管理）",
    "クレアポ（クレーン手配管理）",
]

CATEGORIES = {
    "現場管理": "日々のタスク、指示、進捗を見える化する",
    "現場AI": "現場で聞く・探す・確認する負担を減らす",
    "書類/議事録": "会議後や提出前の作成作業を軽くする",
    "発注/手配": "電話・メール・記憶に頼る手配を整える",
    "安全/品質": "教育、巡回、確認、是正を抜け漏れなくする",
    "ダッシュボード": "工程・原価・安全・出来高を見える化する",
}

DAILY_REPORT_IDEA = {
    "title": "業者側の紙の日報をデジタル化（常用工事記入可能）",
    "category": "書類/議事録",
    "summary": "日報ペーパーレスになったが、常用管理を紙で行っている現状を打開する電子日報サービス",
    "user_scene": "職長の方が空いた時間や、帰り際や帰りながら手持ちのスマホで記入",
    "value": "現場の常駐時間や事務員さんの業務時間削減、月末請求時期の事務作業低減、日報用紙の紛失の心配無用 等",
    "detail": (
        "元請の日報がペーパーレス化したことにより常用管理（作業内容や人工管理等）が難しくなり、"
        "下請け会社書式の日報を職長さんが作業員の方がみんな帰った後にいつも休憩所で記入している姿を"
        "何度も拝見したことから、職長になると仕事が増えるからやりたくない。という作業員の方もいらっしゃり、"
        "下請け会社さんの事務員の方も請求時期に紙の日報をコピーしたり貼り付けしたりして、大変な現状がある。\n"
        "それを解決するのがこの現場日報である。\n"
        "これを利用すれば職長さんは手持ちのスマホから手軽に記入でき、帰りながらでも記入できて"
        "メールで元請の承認を受ければみんなの時間にゆとりができると思い開発。"
    ),
    "status": "検証前",
}

CLEAPO_CRANE_ORDER_IDEA = {
    "title": "クレアポ（クレーン手配管理）",
    "category": "発注/手配",
    "summary": "元請けの現場監督がクレーンを注文し、クレーン屋さんが注文内容を確認して手配できる管理アプリ。",
    "user_scene": "現場監督がスマホやPCから日時、現場名、クレーン車種、作業時間帯を入力し、クレーン会社が一覧やカレンダーで注文を確認する。",
    "value": "電話・FAX・口頭連絡に頼るクレーン手配を見える化し、注文漏れ、日程認識違い、車種の手配ミス、月次確認の手戻りを減らす。",
    "detail": (
        "クレアポは、元請けとクレーン会社の間にあるクレーン手配のやり取りを整理するアプリである。\n"
        "元請けの現場監督は、現場ごとの予定に合わせて13t、25t、50t、70t、80t、100tなどのクレーンを注文できる。\n"
        "クレーン会社側は注文一覧や稼働カレンダーで注文内容を確認し、機材・担当者・日程を見ながら手配を進められる。\n\n"
        "主な機能:\n"
        "- 元請け現場監督によるクレーン新規注文\n"
        "- クレーン会社による注文確認と手配状況管理\n"
        "- 稼働カレンダーでの日程、車種、現場別の確認\n"
        "- 月次確認や請求資料作成に向けた注文履歴の整理\n\n"
        "MVPで確認したいこと:\n"
        "- 現場監督が電話の代わりに入力したい項目は何か\n"
        "- クレーン会社が手配判断に必要な情報は何か\n"
        "- 注文後の変更、キャンセル、確認済みステータスをどこまで必要とするか\n"
        "- 月次請求や現場別集計にそのまま使える粒度になっているか"
    ),
    "status": "検証前",
}

KANBEL_ROUTINE_TASK_IDEA = {
    "title": "カンベル（現場監督ルーティン管理）",
    "category": "現場管理",
    "summary": "現場監督が忙しくて忘れがちな日々のタスクをアプリが支援し、上職者が進捗確認や追加指示を出せる管理アプリ。",
    "user_scene": "現場監督が朝礼準備、受け入れ教育、昼礼準備、翌日の資機材手配、作業進捗確認、終了確認などをスマホで確認・回答する。",
    "value": "個人の記憶に頼るルーティンを見える化し、抜け漏れを減らす。上職者は複数の部下の完了率や未回答タスクを見て、早めに声かけや追加指示ができる。",
    "detail": (
        "カンベルは、現場監督の毎日のルーティンワークをタスク化し、忙しい現場でも確認漏れを減らすためのアプリである。\n"
        "現場監督は、今日やるべき確認事項をスマホやPCで見ながら、完了・未完了を記録できる。\n"
        "上職者は部下ごとの完了率や未回答タスクを確認し、必要に応じて追加の指示やフォローを行える。\n\n"
        "主な機能:\n"
        "- 今日のタスク一覧と完了率の表示\n"
        "- 朝礼準備、新規受け入れ教育、昼礼準備、資機材手配、作業進捗確認、現場終了確認などの日次ルーティン管理\n"
        "- 完了ログによる実施状況の振り返り\n"
        "- 上職者による複数メンバーの進捗確認\n"
        "- 追加指示やフォローが必要なタスクの把握\n\n"
        "MVPで確認したいこと:\n"
        "- 現場監督が毎日自然に回答できるタスク数と入力方法は何か\n"
        "- 上職者が見たい単位は個人別、現場別、日別のどれか\n"
        "- 未完了時に通知、コメント、追加指示をどこまで必要とするか\n"
        "- 既存の朝礼、昼礼、終業確認の流れに無理なく組み込めるか"
    ),
    "status": "検証前",
}

SEED_IDEAS = [
    {
        "title": "現場マニュアルAI検索",
        "category": "現場AI",
        "summary": "社内基準、品質基準、安全基準を自然文で聞ける現場専用AI。",
        "user_scene": "若手監督が現場で判断に迷ったとき、該当資料と根拠を即確認する。",
        "value": "検索時間と支店問い合わせを減らし、基準確認のばらつきを抑える。",
    },
    {
        "title": "定例会議メモから議事録・メール自動作成",
        "category": "書類/議事録",
        "summary": "録音や箇条書きメモから議事録、宿題リスト、関係者メールを作成。",
        "user_scene": "定例会後に残業して議事録と連絡文を整えている担当者が使う。",
        "value": "会議後作業を短縮し、決定事項と宿題の抜け漏れを防ぐ。",
    },
    {
        "title": "音声発注・手配アシスタント",
        "category": "発注/手配",
        "summary": "資材、雑金物、リース品、クレーンなどの手配内容を音声で整理。",
        "user_scene": "現場巡回中に思い出した手配をスマホに話して依頼文まで作る。",
        "value": "発注漏れ、単価確認漏れ、担当者依存を減らす。",
    },
    {
        "title": "新規入場者教育AIチェック",
        "category": "安全/品質",
        "summary": "教育資料の説明、理解度確認、アンケート不備チェックをAIで支援。",
        "user_scene": "朝の入場対応で、教育記録と確認作業を標準化する。",
        "value": "教育品質を揃え、監督員の個別説明工数を減らす。",
    },
    {
        "title": "現場横断Power BIダッシュボード",
        "category": "ダッシュボード",
        "summary": "工程、原価、安全指摘、是正、出来高を現場・支店・本社で共有。",
        "user_scene": "支店会議や本社報告で、各現場の状態を同じ数字で確認する。",
        "value": "報告資料作成を減らし、遅延や是正遅れを早期発見する。",
    },
]

DEFAULT_IDEAS = [DAILY_REPORT_IDEA, CLEAPO_CRANE_ORDER_IDEA, KANBEL_ROUTINE_TASK_IDEA, *SEED_IDEAS]


def get_config_value(name: str, default: str = "") -> str:
    value = os.environ.get(name, default)
    try:
        value = st.secrets.get(name, value)
    except Exception:
        pass
    return str(value or "").strip()


def use_supabase() -> bool:
    return bool(get_config_value("SUPABASE_URL") and get_supabase_key())


def get_supabase_key() -> str:
    return (
        get_config_value("SUPABASE_SERVICE_ROLE_KEY")
        or get_config_value("SUPABASE_KEY")
        or get_config_value("SUPABASE_ANON_KEY")
    )


@st.cache_resource
def supabase_client(url: str, key: str) -> Client:
    if create_client is None:
        raise RuntimeError("supabase package is not installed. Run: pip install -r requirements.txt")
    return create_client(url, key)


def sb() -> Client:
    url = get_config_value("SUPABASE_URL")
    key = get_supabase_key()
    if not url or not key:
        raise RuntimeError("Supabase URL and key are required.")
    return supabase_client(url, key)


def rows_to_df(rows: list[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    if use_supabase():
        init_supabase_seed()
        return

    UPLOAD_DIR.mkdir(exist_ok=True)
    with connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                user_scene TEXT NOT NULL,
                value TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                image_path TEXT NOT NULL DEFAULT '',
                external_url TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '検証前',
                created_at TEXT NOT NULL
            )
            """
        )
        ensure_column(con, "ideas", "detail", "TEXT NOT NULL DEFAULT ''")
        ensure_column(con, "ideas", "image_path", "TEXT NOT NULL DEFAULT ''")
        ensure_column(con, "ideas", "external_url", "TEXT NOT NULL DEFAULT ''")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                session_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (idea_id) REFERENCES ideas(id)
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                comment TEXT NOT NULL,
                concern_level INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (idea_id) REFERENCES ideas(id)
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (idea_id) REFERENCES ideas(id)
            )
            """
        )
        existing_titles = {row[0] for row in con.execute("SELECT title FROM ideas").fetchall()}
        missing_ideas = [idea for idea in DEFAULT_IDEAS if idea["title"] not in existing_titles]
        if missing_ideas:
            now = datetime.now().isoformat(timespec="seconds")
            con.executemany(
                """
                INSERT INTO ideas
                    (id, title, category, summary, user_scene, value, detail, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        idea["title"],
                        idea["category"],
                        idea["summary"],
                        idea["user_scene"],
                        idea["value"],
                        idea.get("detail") or build_default_detail(idea),
                        idea.get("status", "LP反応確認"),
                        now,
                    )
                    for idea in missing_ideas
                ],
            )


def init_supabase_seed() -> None:
    try:
        existing = sb().table("ideas").select("title").execute()
    except Exception as exc:
        st.error("Supabaseに接続できません。supabase_schema.sqlを実行し、Secretsを確認してください。")
        st.exception(exc)
        st.stop()

    existing_titles = {row["title"] for row in existing.data}
    missing_ideas = [idea for idea in DEFAULT_IDEAS if idea["title"] not in existing_titles]
    if not missing_ideas:
        return

    now = now_iso()
    rows = [
        {
            "id": str(uuid.uuid4()),
            "title": idea["title"],
            "category": idea["category"],
            "summary": idea["summary"],
            "user_scene": idea["user_scene"],
            "value": idea["value"],
            "detail": idea.get("detail") or build_default_detail(idea),
            "image_path": "",
            "external_url": "",
            "status": idea.get("status", "LP反応確認"),
            "created_at": now,
        }
        for idea in missing_ideas
    ]
    sb().table("ideas").insert(rows).execute()


def ensure_column(con: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    columns = [row[1] for row in con.execute(f"PRAGMA table_info({table_name})").fetchall()]
    if column_name not in columns:
        con.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def build_default_detail(idea: dict[str, str]) -> str:
    return (
        f"{idea['summary']}\n\n"
        f"想定利用シーン:\n{idea['user_scene']}\n\n"
        f"期待できる効果:\n{idea['value']}\n\n"
        "MVPで確認したいこと:\n"
        "- 実際に毎日使いたい場面があるか\n"
        "- 既存業務のどこに組み込むと自然か\n"
        "- 最初に必要な画面や入力項目は何か\n"
        "- 導入時の懸念や条件は何か"
    )


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_session() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def get_ideas() -> pd.DataFrame:
    if use_supabase():
        rows = sb().table("ideas").select("*").order("created_at", desc=True).execute().data
        return rows_to_df(
            rows,
            ["id", "title", "category", "summary", "user_scene", "value", "detail", "image_path", "external_url", "status", "created_at"],
        )
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM ideas ORDER BY created_at DESC", con)


def get_events() -> pd.DataFrame:
    if use_supabase():
        rows = sb().table("events").select("*").execute().data
        return rows_to_df(rows, ["id", "idea_id", "event_type", "session_id", "created_at"])
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM events", con)


def get_comments() -> pd.DataFrame:
    if use_supabase():
        rows = sb().table("comments").select("*").order("created_at", desc=True).execute().data
        return rows_to_df(rows, ["id", "idea_id", "comment", "concern_level", "created_at"])
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM comments ORDER BY created_at DESC", con)


def get_ratings() -> pd.DataFrame:
    if use_supabase():
        rows = sb().table("ratings").select("*").order("created_at", desc=True).execute().data
        return rows_to_df(rows, ["id", "idea_id", "rating", "session_id", "created_at"])
    with connect() as con:
        return pd.read_sql_query("SELECT * FROM ratings ORDER BY created_at DESC", con)


def track_event(idea_id: str, event_type: str) -> None:
    if use_supabase():
        sb().table("events").insert(
            {
                "id": str(uuid.uuid4()),
                "idea_id": idea_id,
                "event_type": event_type,
                "session_id": ensure_session(),
                "created_at": now_iso(),
            }
        ).execute()
        return

    with connect() as con:
        con.execute(
            "INSERT INTO events (id, idea_id, event_type, session_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), idea_id, event_type, ensure_session(), now_iso()),
        )


def has_liked(idea_id: str) -> bool:
    if use_supabase():
        rows = (
            sb()
            .table("events")
            .select("id")
            .eq("idea_id", idea_id)
            .eq("event_type", "like")
            .eq("session_id", ensure_session())
            .limit(1)
            .execute()
            .data
        )
        return bool(rows)

    with connect() as con:
        row = con.execute(
            """
            SELECT 1
            FROM events
            WHERE idea_id = ? AND event_type = 'like' AND session_id = ?
            LIMIT 1
            """,
            (idea_id, ensure_session()),
        ).fetchone()
    return row is not None


def remove_like(idea_id: str) -> None:
    if use_supabase():
        rows = (
            sb()
            .table("events")
            .select("id")
            .eq("idea_id", idea_id)
            .eq("event_type", "like")
            .eq("session_id", ensure_session())
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if rows:
            sb().table("events").delete().eq("id", rows[0]["id"]).execute()
        return

    with connect() as con:
        con.execute(
            """
            DELETE FROM events
            WHERE id = (
                SELECT id
                FROM events
                WHERE idea_id = ? AND event_type = 'like' AND session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            )
            """,
            (idea_id, ensure_session()),
        )


def add_comment(idea_id: str, comment: str, concern_level: int) -> None:
    if use_supabase():
        sb().table("comments").insert(
            {
                "id": str(uuid.uuid4()),
                "idea_id": idea_id,
                "comment": comment.strip(),
                "concern_level": concern_level,
                "created_at": now_iso(),
            }
        ).execute()
        return

    with connect() as con:
        con.execute(
            "INSERT INTO comments (id, idea_id, comment, concern_level, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), idea_id, comment.strip(), concern_level, now_iso()),
        )


def get_session_rating(idea_id: str) -> int | None:
    if use_supabase():
        rows = (
            sb()
            .table("ratings")
            .select("rating")
            .eq("idea_id", idea_id)
            .eq("session_id", ensure_session())
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return int(rows[0]["rating"]) if rows else None

    with connect() as con:
        row = con.execute(
            """
            SELECT rating
            FROM ratings
            WHERE idea_id = ? AND session_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (idea_id, ensure_session()),
        ).fetchone()
    return int(row[0]) if row else None


def set_rating(idea_id: str, rating: int) -> None:
    if use_supabase():
        (
            sb()
            .table("ratings")
            .delete()
            .eq("idea_id", idea_id)
            .eq("session_id", ensure_session())
            .execute()
        )
        sb().table("ratings").insert(
            {
                "id": str(uuid.uuid4()),
                "idea_id": idea_id,
                "rating": rating,
                "session_id": ensure_session(),
                "created_at": now_iso(),
            }
        ).execute()
        return

    with connect() as con:
        con.execute(
            "DELETE FROM ratings WHERE idea_id = ? AND session_id = ?",
            (idea_id, ensure_session()),
        )
        con.execute(
            "INSERT INTO ratings (id, idea_id, rating, session_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), idea_id, rating, ensure_session(), now_iso()),
        )


def save_uploaded_image(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".png"
    image_name = f"{uuid.uuid4()}{suffix}"

    if use_supabase():
        storage_path = f"ideas/{image_name}"
        content_type = getattr(uploaded_file, "type", None) or "image/png"
        sb().storage.from_(SUPABASE_IMAGE_BUCKET).upload(
            storage_path,
            uploaded_file.getvalue(),
            file_options={"content-type": content_type},
        )
        return sb().storage.from_(SUPABASE_IMAGE_BUCKET).get_public_url(storage_path)

    image_path = UPLOAD_DIR / image_name
    image_path.write_bytes(uploaded_file.getbuffer())
    return str(image_path)


def add_idea(
    title: str,
    category: str,
    summary: str,
    user_scene: str,
    value: str,
    detail: str,
    image_path: str,
    external_url: str,
) -> None:
    if idea_title_exists(title):
        raise ValueError("同じ名前のアイデアが既に登録されています。")

    if use_supabase():
        sb().table("ideas").insert(
            {
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "category": category,
                "summary": summary.strip(),
                "user_scene": user_scene.strip(),
                "value": value.strip(),
                "detail": detail.strip(),
                "image_path": image_path,
                "external_url": external_url.strip(),
                "status": "検証前",
                "created_at": now_iso(),
            }
        ).execute()
        return

    with connect() as con:
        con.execute(
            """
            INSERT INTO ideas
                (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                title.strip(),
                category,
                summary.strip(),
                user_scene.strip(),
                value.strip(),
                detail.strip(),
                image_path,
                external_url.strip(),
                "検証前",
                now_iso(),
            ),
        )


def idea_title_exists(title: str, exclude_id: str | None = None) -> bool:
    normalized_title = title.strip()
    if not normalized_title:
        return False

    if use_supabase():
        query = sb().table("ideas").select("id").eq("title", normalized_title)
        if exclude_id:
            query = query.neq("id", exclude_id)
        return bool(query.limit(1).execute().data)

    with connect() as con:
        if exclude_id:
            row = con.execute(
                "SELECT 1 FROM ideas WHERE title = ? AND id != ? LIMIT 1",
                (normalized_title, exclude_id),
            ).fetchone()
        else:
            row = con.execute(
                "SELECT 1 FROM ideas WHERE title = ? LIMIT 1",
                (normalized_title,),
            ).fetchone()
    return row is not None


def update_idea(
    idea_id: str,
    title: str,
    category: str,
    summary: str,
    user_scene: str,
    value: str,
    detail: str,
    image_path: str,
    external_url: str,
) -> None:
    if idea_title_exists(title, exclude_id=idea_id):
        raise ValueError("同じ名前のアイデアが既に登録されています。")

    if use_supabase():
        sb().table("ideas").update(
            {
                "title": title.strip(),
                "category": category,
                "summary": summary.strip(),
                "user_scene": user_scene.strip(),
                "value": value.strip(),
                "detail": detail.strip(),
                "image_path": image_path,
                "external_url": external_url.strip(),
            }
        ).eq("id", idea_id).execute()
        return

    with connect() as con:
        con.execute(
            """
            UPDATE ideas
            SET title = ?,
                category = ?,
                summary = ?,
                user_scene = ?,
                value = ?,
                detail = ?,
                image_path = ?,
                external_url = ?
            WHERE id = ?
            """,
            (
                title.strip(),
                category,
                summary.strip(),
                user_scene.strip(),
                value.strip(),
                detail.strip(),
                image_path,
                external_url.strip(),
                idea_id,
            ),
        )


def delete_idea(idea_id: str) -> None:
    if use_supabase():
        sb().table("ideas").delete().eq("id", idea_id).execute()
        return

    with connect() as con:
        con.execute("DELETE FROM comments WHERE idea_id = ?", (idea_id,))
        con.execute("DELETE FROM events WHERE idea_id = ?", (idea_id,))
        con.execute("DELETE FROM ratings WHERE idea_id = ?", (idea_id,))
        con.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))


def event_summary(
    ideas: pd.DataFrame,
    events: pd.DataFrame,
    comments: pd.DataFrame,
    ratings: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if ideas.empty:
        return pd.DataFrame()

    pivot = pd.DataFrame(index=ideas["id"])
    if not events.empty:
        counts = events.pivot_table(index="idea_id", columns="event_type", values="id", aggfunc="count", fill_value=0)
        pivot = pivot.join(counts, how="left")
    for name in ["impression", "click", "like"]:
        if name not in pivot.columns:
            pivot[name] = 0
    comment_counts = comments.groupby("idea_id").size() if not comments.empty else pd.Series(dtype=int)
    pivot["comments"] = pivot.index.map(comment_counts).fillna(0).astype(int)
    if ratings is not None and not ratings.empty:
        rating_group = ratings.groupby("idea_id")["rating"]
        pivot["rating_count"] = pivot.index.map(rating_group.size()).fillna(0).astype(int)
        pivot["rating_avg"] = pivot.index.map(rating_group.mean()).fillna(0).round(1)
    else:
        pivot["rating_count"] = 0
        pivot["rating_avg"] = 0

    result = ideas.set_index("id").join(pivot, how="left").fillna(0).reset_index()
    result["like_rate"] = result.apply(lambda row: row["like"] / row["impression"] if row["impression"] else 0, axis=1)
    result["click_rate"] = result.apply(lambda row: row["click"] / row["impression"] if row["impression"] else 0, axis=1)
    result["mvp_score"] = (
        result["like"] * 3
        + result["click"] * 2
        + result["comments"] * 4
        + result["rating_count"] * 2
        + result["rating_avg"] * 2
        + (result["like_rate"] * 10)
        + (result["click_rate"] * 8)
    )
    return result.sort_values("mvp_score", ascending=False)


def derive_keywords(texts: list[str]) -> list[tuple[str, int]]:
    stopwords = {
        "これ",
        "それ",
        "ため",
        "よう",
        "ところ",
        "こと",
        "かな",
        "です",
        "ます",
        "したい",
        "できる",
        "ほしい",
        "現場",
        "機能",
        "管理",
    }
    tokens: list[str] = []
    for text in texts:
        normalized = (
            text.replace("、", " ")
            .replace("。", " ")
            .replace("・", " ")
            .replace("　", " ")
            .replace("\n", " ")
        )
        for token in normalized.split():
            cleaned = token.strip("「」『』（）()[]【】,.!?！？")
            if len(cleaned) >= 2 and cleaned not in stopwords:
                tokens.append(cleaned)
    return Counter(tokens).most_common(12)


def idea_detail_text(row: pd.Series) -> str:
    detail = str(row.get("detail", "") or "").strip()
    if detail:
        return detail
    return (
        f"{row['summary']}\n\n"
        f"想定利用シーン:\n{row['user_scene']}\n\n"
        f"期待できる効果:\n{row['value']}"
    )


def event_count(summary: pd.DataFrame, idea_id: str, event_type: str) -> int:
    if summary.empty or event_type not in summary.columns:
        return 0
    matched = summary[summary["id"] == idea_id]
    if matched.empty:
        return 0
    return int(matched[event_type].iloc[0])


def render_like_button(idea_id: str, like_count: int, key_prefix: str) -> None:
    liked = has_liked(idea_id)
    label = f"♥ いいね済み {like_count} / 取り下げ" if liked else f"♡ いいね {like_count}"
    if st.button(label, key=f"{key_prefix}_like_{idea_id}", use_container_width=True):
        if liked:
            remove_like(idea_id)
            st.toast("いいねを取り下げました")
        else:
            track_event(idea_id, "like")
            st.toast("いいねを記録しました")
        st.rerun()


def render_interest_rating(idea_id: str, key_prefix: str) -> None:
    current_rating = get_session_rating(idea_id)
    st.write("**実現したら使いたい度**")
    rating_cols = st.columns(5)
    for rating in range(1, 6):
        label = f"{rating}"
        if current_rating == rating:
            label = f"{rating} 選択中"
        with rating_cols[rating - 1]:
            if st.button(label, key=f"{key_prefix}_interest_{idea_id}_{rating}", use_container_width=True):
                set_rating(idea_id, rating)
                st.toast(f"使いたい度 {rating} を記録しました")
                st.rerun()
    st.caption("1: 低い / 5: 高い")


def render_comment_form(idea_id: str, key_prefix: str) -> None:
    with st.expander("匿名でコメントする"):
        comment = st.text_area(
            "コメント",
            placeholder="どんな場面で使いたいか、逆に不安な点などを自由に書いてください。",
            key=f"{key_prefix}_comment_text_{idea_id}",
        )
        if st.button("運営に送る", key=f"{key_prefix}_send_comment_{idea_id}"):
            if comment.strip():
                add_comment(idea_id, comment, get_session_rating(idea_id) or 4)
                st.success("匿名コメントを送信しました")
            else:
                st.warning("コメントを入力してください")


def render_image_or_placeholder(row: pd.Series) -> None:
    image_path = str(row.get("image_path", "") or "")
    if not image_path:
        image_path = DEFAULT_IMAGE_BY_TITLE.get(str(row.get("title", "")), "")
    if image_path and (is_url(image_path) or Path(image_path).exists()):
        st.image(image_path, use_container_width=True)
        return
    st.markdown(
        f"""
        <div class="idea-placeholder">
            <span>{html.escape(str(row["category"]))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_detail_page(ideas: pd.DataFrame, summary: pd.DataFrame, idea_id: str) -> None:
    matched = ideas[ideas["id"] == idea_id]
    if matched.empty:
        st.warning("指定されたアイデアが見つかりません。")
        if st.button("一覧に戻る"):
            st.query_params.clear()
            st.rerun()
        return

    row = matched.iloc[0]
    like_count = event_count(summary, row["id"], "like")
    click_count = event_count(summary, row["id"], "click")
    impression_count = event_count(summary, row["id"], "impression")

    if st.button("← 一覧に戻る"):
        st.query_params.clear()
        st.rerun()

    top_left, top_right = st.columns([1.2, 1])
    with top_left:
        st.caption(row["category"])
        st.markdown(f"## {row['title']}")
        st.write(row["summary"])
        stat_cols = st.columns(3)
        stat_cols[0].metric("♥ いいね", f"{like_count:,}")
        stat_cols[1].metric("詳しく見る", f"{click_count:,}")
        stat_cols[2].metric("表示", f"{impression_count:,}")
        render_like_button(row["id"], like_count, "detail")
        render_interest_rating(row["id"], "detail")
    with top_right:
        render_image_or_placeholder(row)

    st.markdown("### 詳細")
    st.markdown(idea_detail_text(row).replace("\n", "  \n"))
    st.markdown("### 使う場面")
    st.write(row["user_scene"])
    st.markdown("### 期待できる効果")
    st.write(row["value"])

    external_url = str(row.get("external_url", "") or "").strip()
    if external_url:
        st.link_button("デモ・関連ページを開く", external_url, use_container_width=False)

    render_comment_form(row["id"], "detail")


def render_public_site(ideas: pd.DataFrame) -> None:
    st.markdown("## こんなのあったらいいな")
    st.caption("現場で使えそうなDXアイデアに、いいねや匿名コメントを残せます。コメントは運営側だけが確認します。")
    events = get_events()
    comments = get_comments()
    ratings = get_ratings()
    summary = event_summary(ideas, events, comments, ratings)

    detail_id = st.query_params.get("idea")
    if detail_id:
        render_detail_page(ideas, summary, detail_id)
        return

    selected_category = st.segmented_control(
        "カテゴリ",
        ["すべて", *CATEGORIES.keys()],
        default="すべて",
        label_visibility="collapsed",
    )
    visible = ideas if selected_category == "すべて" else ideas[ideas["category"] == selected_category]
    if not visible.empty:
        visible = visible.copy()
        visible["_featured_rank"] = visible["title"].apply(
            lambda title: FEATURED_IDEA_TITLES.index(title)
            if title in FEATURED_IDEA_TITLES
            else len(FEATURED_IDEA_TITLES)
        )
        visible = visible.sort_values("_featured_rank", kind="stable").drop(columns=["_featured_rank"])
        visible = visible.drop_duplicates(subset=["title"], keep="first")

    cols = st.columns(2)
    for index, row in visible.reset_index(drop=True).iterrows():
        with cols[index % 2]:
            track_key = f"impressed_{row['id']}"
            if track_key not in st.session_state:
                track_event(row["id"], "impression")
                st.session_state[track_key] = True

            with st.container(border=True):
                render_image_or_placeholder(row)
                st.caption(row["category"])
                st.subheader(row["title"])
                st.write(row["summary"])
                st.markdown(f"**使う場面**  \n{row['user_scene']}")
                st.markdown(f"**期待できる効果**  \n{row['value']}")

                like_count = event_count(summary, row["id"], "like")
                left, right = st.columns([1, 1])
                with left:
                    render_like_button(row["id"], like_count, "card")
                if right.button("詳しく見る", key=f"click_{row['id']}", use_container_width=True):
                    track_event(row["id"], "click")
                    st.query_params["idea"] = row["id"]
                    st.rerun()

                render_interest_rating(row["id"], "card")
                render_comment_form(row["id"], "card")


def render_admin(ideas: pd.DataFrame, events: pd.DataFrame, comments: pd.DataFrame, ratings: pd.DataFrame) -> None:
    admin_password = os.environ.get("HAKOVAL_ADMIN_PASSWORD", "hakoval-admin")
    try:
        admin_password = st.secrets.get("ADMIN_PASSWORD", admin_password)
    except Exception:
        pass
    if not st.session_state.get("admin_authorized"):
        st.markdown("## 運営ログイン")
        password = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if password == admin_password:
                st.session_state.admin_authorized = True
                st.rerun()
            else:
                st.error("パスワードが違います")
        return

    st.markdown("## 運営ダッシュボード")
    st.caption("クリック数、インプレッション数、いいね、匿名コメントからMVP候補を判断します。")

    summary = event_summary(ideas, events, comments, ratings)
    if summary.empty:
        st.info("まだアイデアがありません。")
        return

    total_impressions = int(summary["impression"].sum())
    total_clicks = int(summary["click"].sum())
    total_likes = int(summary["like"].sum())
    total_comments = int(summary["comments"].sum())

    total_ratings = int(summary["rating_count"].sum())

    metric_cols = st.columns(5)
    metric_cols[0].metric("表示", f"{total_impressions:,}")
    metric_cols[1].metric("クリック", f"{total_clicks:,}")
    metric_cols[2].metric("いいね", f"{total_likes:,}")
    metric_cols[3].metric("匿名コメント", f"{total_comments:,}")
    metric_cols[4].metric("使いたい度回答", f"{total_ratings:,}")

    st.markdown("### MVP候補ランキング")
    ranking = summary[
        [
            "title",
            "category",
            "status",
            "impression",
            "click",
            "like",
            "comments",
            "rating_count",
            "rating_avg",
            "click_rate",
            "like_rate",
            "mvp_score",
        ]
    ].copy()
    ranking["click_rate"] = (ranking["click_rate"] * 100).round(1)
    ranking["like_rate"] = (ranking["like_rate"] * 100).round(1)
    ranking["mvp_score"] = ranking["mvp_score"].round(1)
    st.dataframe(
        ranking.rename(
            columns={
                "title": "アイデア",
                "category": "カテゴリ",
                "status": "状態",
                "impression": "表示",
                "click": "クリック",
                "like": "いいね",
                "comments": "コメント",
                "rating_count": "使いたい度回答",
                "rating_avg": "使いたい度平均",
                "click_rate": "クリック率%",
                "like_rate": "いいね率%",
                "mvp_score": "MVPスコア",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### カテゴリ別反応")
    category_chart = summary.groupby("category")[["impression", "click", "like", "comments", "rating_count"]].sum()
    st.bar_chart(category_chart)

    st.markdown("### 匿名コメントから具体化する")
    selected_title = st.selectbox("対象アイデア", summary["title"].tolist())
    selected_id = summary.loc[summary["title"] == selected_title, "id"].iloc[0]
    idea_comments = comments[comments["idea_id"] == selected_id]
    selected_idea = ideas[ideas["id"] == selected_id].iloc[0]

    st.write(f"**現時点の仮説:** {selected_idea['summary']}")
    if idea_comments.empty:
        st.info("このアイデアにはまだコメントがありません。顧客に見せて反応を集める段階です。")
    else:
        st.write("**コメント一覧**")
        for _, comment_row in idea_comments.iterrows():
            with st.container(border=True):
                st.caption(f"使いたい度: {comment_row['concern_level']} / 5 ・ {comment_row['created_at']}")
                st.write(comment_row["comment"])

        keywords = derive_keywords(idea_comments["comment"].tolist())
        if keywords:
            st.write("**コメント内の頻出語**")
            st.write(" / ".join([f"{word}({count})" for word, count in keywords]))

        st.write("**具体化メモ**")
        st.text_area(
            "要件化メモ",
            value=(
                f"対象ユーザー: {selected_idea['user_scene']}\n"
                f"解決したいこと: {selected_idea['value']}\n"
                "次に確認すること:\n"
                "- 実際に誰が毎日使うか\n"
                "- 既存Excelや社内資料の有無\n"
                "- MVPで最初に必要な1画面\n"
                "- 導入時の懸念、権限、セキュリティ条件\n"
            ),
            height=180,
        )

    st.markdown("### 既存アイデアを編集")
    title_by_id = dict(zip(ideas["id"], ideas["title"]))
    edit_id = st.selectbox(
        "編集するアイデア",
        ideas["id"].tolist(),
        format_func=lambda idea_id: title_by_id.get(idea_id, idea_id),
        key="edit_idea_id",
    )
    edit_row = ideas[ideas["id"] == edit_id].iloc[0]
    current_image_path = str(edit_row.get("image_path", "") or "")

    if current_image_path and (is_url(current_image_path) or Path(current_image_path).exists()):
        st.write("**現在の画像**")
        st.image(current_image_path, width=360)

    with st.form("edit_idea"):
        edited_title = st.text_input("アイデア名", value=str(edit_row["title"]))
        edited_category = st.selectbox(
            "カテゴリ",
            list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(edit_row["category"]) if edit_row["category"] in CATEGORIES else 0,
        )
        edited_image_file = st.file_uploader(
            "画像を差し替える",
            type=["png", "jpg", "jpeg", "webp"],
            help="新しい画像を選ぶと差し替えます。選ばない場合は現在の画像を維持します。",
            key=f"edit_image_{edit_row['id']}",
        )
        edited_summary = st.text_area(
            "一覧カードに表示する短い説明",
            value=str(edit_row["summary"]),
            height=100,
        )
        edited_detail = st.text_area(
            "詳しく見るページに表示する詳細説明",
            value=idea_detail_text(edit_row),
            height=180,
        )
        edited_user_scene = st.text_area(
            "想定する利用シーン",
            value=str(edit_row["user_scene"]),
            height=100,
        )
        edited_value = st.text_area(
            "期待できる効果",
            value=str(edit_row["value"]),
            height=100,
        )
        edited_external_url = st.text_input(
            "関連URL・デモURL",
            value=str(edit_row.get("external_url", "") or ""),
        )
        update_submitted = st.form_submit_button("変更を保存")
        if update_submitted:
            if edited_title and edited_summary and edited_user_scene and edited_value:
                new_image_path = save_uploaded_image(edited_image_file) or current_image_path
                try:
                    update_idea(
                        edit_row["id"],
                        edited_title,
                        edited_category,
                        edited_summary,
                        edited_user_scene,
                        edited_value,
                        edited_detail,
                        new_image_path,
                        edited_external_url,
                    )
                    st.success("アイデアを更新しました")
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
            else:
                st.warning("必須項目を入力してください")

    with st.expander("このアイデアを削除する"):
        st.warning("削除すると、このアイデアの表示・クリック・いいね・使いたい度・コメントの記録も削除されます。")
        confirm_delete = st.checkbox(
            f"「{edit_row['title']}」を削除することを確認しました",
            key=f"confirm_delete_{edit_row['id']}",
        )
        if st.button(
            "アイデアを削除",
            key=f"delete_idea_{edit_row['id']}",
            disabled=not confirm_delete,
        ):
            delete_idea(edit_row["id"])
            st.success("アイデアを削除しました")
            st.rerun()

    st.markdown("### 新しいアイデアを追加")
    st.caption("顧客向けサイトに表示する内容を登録します。あとで反応を見ながら説明文や画像を差し替えられます。")
    with st.form("new_idea"):
        title = st.text_input(
            "アイデア名",
            placeholder="例: 現場写真から安全指摘を自動整理",
            help="顧客向けカードと詳細ページの見出しに表示されます。",
        )
        category = st.selectbox(
            "カテゴリ",
            list(CATEGORIES.keys()),
            help="顧客がアイデアを探しやすい分類です。近いものを選んでください。",
        )
        image_file = st.file_uploader(
            "カード画像・説明画像",
            type=["png", "jpg", "jpeg", "webp"],
            help="顧客向け一覧と詳細ページに表示する画像です。画面モック、業務イメージ、資料画像などを添付できます。",
        )
        summary_text = st.text_area(
            "一覧カードに表示する短い説明",
            placeholder="例: 現場写真をアップロードすると、安全指摘・是正期限・担当者案を自動で整理します。",
            help="顧客が一覧で最初に読む説明です。1〜2文で、何ができるかを書いてください。",
            height=100,
        )
        detail = st.text_area(
            "詳しく見るページに表示する詳細説明",
            placeholder=(
                "例:\n"
                "背景: 安全巡回後の写真整理と是正依頼に時間がかかっている。\n"
                "主な機能: 写真登録、指摘内容の自動分類、担当者案、是正期限の管理。\n"
                "MVPで確認したいこと: 現場担当者が毎週使うか、分類精度が十分か。"
            ),
            help="詳しく見るを押した後のページに表示されます。背景、課題、主要機能、MVPで確認したいことを書く欄です。",
            height=180,
        )
        user_scene = st.text_area(
            "想定する利用シーン",
            placeholder="例: 現場巡回後、監督員がスマホで写真を登録し、その場で是正依頼のたたき台を作る。",
            help="誰が、いつ、どんな場面で使うかを書いてください。",
            height=100,
        )
        value = st.text_area(
            "期待できる効果",
            placeholder="例: 写真整理と是正依頼の作成時間を削減し、指摘漏れや対応遅れを減らす。",
            help="時間削減、ミス削減、問い合わせ削減、標準化など、顧客に伝えたい効果を書いてください。",
            height=100,
        )
        external_url = st.text_input(
            "関連URL・デモURL",
            placeholder="例: https://example.com/demo",
            help="LP、Figma、Streamlitデモ、GitHub、資料URLなどがあれば入力します。未入力でも登録できます。",
        )
        submitted = st.form_submit_button("アイデアを追加")
        if submitted:
            if title and summary_text and user_scene and value:
                image_path = save_uploaded_image(image_file)
                detail_text = detail or (
                    f"{summary_text}\n\n"
                    f"想定利用シーン:\n{user_scene}\n\n"
                    f"期待できる効果:\n{value}"
                )
                try:
                    add_idea(title, category, summary_text, user_scene, value, detail_text, image_path, external_url)
                    st.success("アイデアを追加しました")
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
            else:
                st.warning("すべての項目を入力してください")


def render_github_streamlit_notes() -> None:
    st.markdown("## GitHub / Streamlit連携")
    st.write("このプロトタイプはSQLiteに反応データを保存します。次の段階では以下の連携ができます。")
    st.markdown(
        """
- GitHub: アイデアごとにIssueを作成し、MVP化するテーマを開発タスクへ接続
- GitHub: LPや画面モックの変更履歴をPull Requestで管理
- Streamlit Community Cloud: 顧客に見せる検証サイトとして公開
- Streamlit Secrets: 運営画面だけに簡易パスワードを設定
- CSV Export: クリック、表示、いいね、コメントをPower BIやExcel分析へ連携
        """
    )

    ideas = get_ideas()
    events = get_events()
    comments = get_comments()
    ratings = get_ratings()
    summary = event_summary(ideas, events, comments, ratings)
    if not summary.empty:
        csv = summary.to_csv(index=False).encode("utf-8-sig")
        st.download_button("分析CSVをダウンロード", csv, "hakoval_dx_analytics.csv", "text/csv")


def main() -> None:
    st.set_page_config(page_title="HAKOVAL DX Idea Lab", page_icon="H", layout="wide")
    init_db()
    ensure_session()

    st.markdown(
        """
        <style>
        .stApp { background: #f7f8fb; }
        [data-testid="stHeader"] { background: rgba(247, 248, 251, 0.88); }
        h1, h2, h3 { letter-spacing: 0 !important; }
        .stApp label,
        .stApp [data-testid="stMarkdownContainer"],
        .stApp p,
        .stApp span {
            color: #18212f;
        }
        .stApp [data-testid="stSidebar"] label,
        .stApp [data-testid="stSidebar"] span,
        .stApp [data-testid="stSidebar"] p {
            color: #f8fafc;
        }
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {
            background: #ffffff;
            border-color: #cbd5e1;
            color: #111827;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #64748b;
            opacity: 1;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stDownloadButton"] button,
        div[data-testid="stLinkButton"] a {
            background: #ffffff !important;
            border: 1px solid #94a3b8 !important;
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stDownloadButton"] button:hover,
        div[data-testid="stLinkButton"] a:hover {
            background: #eef6ff !important;
            border-color: #2563eb !important;
            color: #0b3b85 !important;
        }
        div[data-testid="stButton"] button p,
        div[data-testid="stFormSubmitButton"] button p,
        div[data-testid="stDownloadButton"] button p,
        div[data-testid="stLinkButton"] a p {
            color: inherit !important;
            font-weight: inherit !important;
        }
        div[data-testid="stSegmentedControl"] button,
        div[data-testid="stSegmentedControl"] label,
        div[data-testid="stSegmentedControl"] div[role="radio"],
        div[data-testid="stSegmentedControl"] [data-baseweb="button-group"] *,
        .stApp [role="radiogroup"] button,
        .stApp [data-baseweb="button-group"] button {
            background: #ffffff !important;
            border-color: #cbd5e1 !important;
            color: #0f172a !important;
        }
        div[data-testid="stSegmentedControl"] button *,
        div[data-testid="stSegmentedControl"] label *,
        div[data-testid="stSegmentedControl"] div[role="radio"] *,
        .stApp [role="radiogroup"] button *,
        .stApp [data-baseweb="button-group"] button * {
            color: #0f172a !important;
        }
        div[data-testid="stSegmentedControl"] button[aria-checked="true"],
        div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
        div[data-testid="stSegmentedControl"] label:has(input:checked),
        div[data-testid="stSegmentedControl"] div[aria-checked="true"],
        .stApp [role="radiogroup"] button[aria-checked="true"],
        .stApp [role="radiogroup"] button[aria-pressed="true"],
        .stApp [data-baseweb="button-group"] button[aria-checked="true"],
        .stApp [data-baseweb="button-group"] button[aria-pressed="true"] {
            background: #eef6ff !important;
            border-color: #2563eb !important;
            color: #0b3b85 !important;
            font-weight: 700 !important;
        }
        .stApp [role="radiogroup"],
        .stApp [data-baseweb="button-group"] {
            background: transparent !important;
        }
        div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] *,
        .stApp small {
            color: #475569 !important;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
        }
        div[data-testid="stMetric"] *,
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricDelta"] {
            color: #0f172a !important;
        }
        div[data-testid="stMetricValue"] {
            font-weight: 800 !important;
        }
        div[data-testid="stFileUploader"] section,
        div[data-testid="stFileUploaderDropzone"] {
            background: #ffffff !important;
            border: 1px dashed #94a3b8 !important;
            color: #0f172a !important;
        }
        div[data-testid="stFileUploader"] section *,
        div[data-testid="stFileUploaderDropzone"] * {
            color: #334155 !important;
        }
        div[data-testid="stFileUploader"] button {
            background: #f8fafc !important;
            border: 1px solid #94a3b8 !important;
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        div[data-testid="stButton"] button:disabled,
        div[data-testid="stButton"] button:disabled *,
        div[data-testid="stFormSubmitButton"] button:disabled,
        div[data-testid="stFormSubmitButton"] button:disabled * {
            background: #e5e7eb !important;
            border-color: #cbd5e1 !important;
            color: #64748b !important;
            opacity: 1 !important;
        }
        .idea-placeholder {
            align-items: center;
            aspect-ratio: 16 / 9;
            background: linear-gradient(135deg, #eef2f7 0%, #dbe7e4 100%);
            border: 1px solid #d8dee8;
            border-radius: 8px;
            color: #334155;
            display: flex;
            font-size: 15px;
            font-weight: 700;
            justify-content: center;
            margin-bottom: 12px;
            width: 100%;
        }
        .idea-placeholder span {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.36);
            border-radius: 999px;
            padding: 8px 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("HAKOVAL DX Idea Lab")
    st.caption("現場の声を、MVP候補と製品アイデアに育てる検証サイト")

    ideas = get_ideas()
    events = get_events()
    comments = get_comments()
    ratings = get_ratings()

    page = st.sidebar.radio(
        "表示",
        ["顧客向けサイト", "運営ダッシュボード", "GitHub / Streamlit連携"],
    )

    if page == "顧客向けサイト":
        render_public_site(ideas)
    elif page == "運営ダッシュボード":
        render_admin(ideas, events, comments, ratings)
    else:
        render_github_streamlit_notes()


if __name__ == "__main__":
    main()

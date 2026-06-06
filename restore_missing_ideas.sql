insert into public.ideas
    (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
select
    gen_random_uuid(),
    '業者側の紙の日報をデジタル化（常用工事記入可能）',
    '書類/議事録',
    '日報ペーパーレスになったが、常用管理を紙で行っている現状を打開する電子日報サービス',
    '職長の方が空いた時間や、帰り際や帰りながら手持ちのスマホで記入',
    '現場の常駐時間や事務員さんの業務時間削減、月末請求時期の事務作業低減、日報用紙の紛失の心配無用 等',
    '元請の日報がペーパーレス化したことにより常用管理（作業内容や人工管理等）が難しくなり、下請け会社書式の日報を職長さんが作業員の方がみんな帰った後にいつも休憩所で記入している姿を何度も拝見したことから、職長になると仕事が増えるからやりたくない。という作業員の方もいらっしゃり、下請け会社さんの事務員の方も請求時期に紙の日報をコピーしたり貼り付けしたりして、大変な現状がある。
それを解決するのがこの現場日報である。
これを利用すれば職長さんは手持ちのスマホから手軽に記入でき、帰りながらでも記入できてメールで元請の承認を受ければみんなの時間にゆとりができると思い開発。',
    '',
    '',
    '検証前',
    now()
where not exists (
    select 1 from public.ideas where title = '業者側の紙の日報をデジタル化（常用工事記入可能）'
);

insert into public.ideas
    (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
select
    gen_random_uuid(),
    '現場マニュアルAI検索',
    '現場AI',
    '社内基準、品質基準、安全基準を自然文で聞ける現場専用AI。',
    '若手監督が現場で判断に迷ったとき、該当資料と根拠を即確認する。',
    '検索時間と支店問い合わせを減らし、基準確認のばらつきを抑える。',
    '社内基準、品質基準、安全基準を自然文で聞ける現場専用AI。

想定利用シーン:
若手監督が現場で判断に迷ったとき、該当資料と根拠を即確認する。

期待できる効果:
検索時間と支店問い合わせを減らし、基準確認のばらつきを抑える。

MVPで確認したいこと:
- 実際に毎日使いたい場面があるか
- 既存業務のどこに組み込むと自然か
- 最初に必要な画面や入力項目は何か
- 導入時の懸念や条件は何か',
    '',
    '',
    'LP反応確認',
    now()
where not exists (
    select 1 from public.ideas where title = '現場マニュアルAI検索'
);

insert into public.ideas
    (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
select
    gen_random_uuid(),
    '定例会議メモから議事録・メール自動作成',
    '書類/議事録',
    '録音や箇条書きメモから議事録、宿題リスト、関係者メールを作成。',
    '定例会後に残業して議事録と連絡文を整えている担当者が使う。',
    '会議後作業を短縮し、決定事項と宿題の抜け漏れを防ぐ。',
    '録音や箇条書きメモから議事録、宿題リスト、関係者メールを作成。

想定利用シーン:
定例会後に残業して議事録と連絡文を整えている担当者が使う。

期待できる効果:
会議後作業を短縮し、決定事項と宿題の抜け漏れを防ぐ。

MVPで確認したいこと:
- 実際に毎日使いたい場面があるか
- 既存業務のどこに組み込むと自然か
- 最初に必要な画面や入力項目は何か
- 導入時の懸念や条件は何か',
    '',
    '',
    'LP反応確認',
    now()
where not exists (
    select 1 from public.ideas where title = '定例会議メモから議事録・メール自動作成'
);

insert into public.ideas
    (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
select
    gen_random_uuid(),
    '音声発注・手配アシスタント',
    '発注/手配',
    '資材、雑金物、リース品、クレーンなどの手配内容を音声で整理。',
    '現場巡回中に思い出した手配をスマホに話して依頼文まで作る。',
    '発注漏れ、単価確認漏れ、担当者依存を減らす。',
    '資材、雑金物、リース品、クレーンなどの手配内容を音声で整理。

想定利用シーン:
現場巡回中に思い出した手配をスマホに話して依頼文まで作る。

期待できる効果:
発注漏れ、単価確認漏れ、担当者依存を減らす。

MVPで確認したいこと:
- 実際に毎日使いたい場面があるか
- 既存業務のどこに組み込むと自然か
- 最初に必要な画面や入力項目は何か
- 導入時の懸念や条件は何か',
    '',
    '',
    'LP反応確認',
    now()
where not exists (
    select 1 from public.ideas where title = '音声発注・手配アシスタント'
);

insert into public.ideas
    (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
select
    gen_random_uuid(),
    '新規入場者教育AIチェック',
    '安全/品質',
    '教育資料の説明、理解度確認、アンケート不備チェックをAIで支援。',
    '朝の入場対応で、教育記録と確認作業を標準化する。',
    '教育品質を揃え、監督員の個別説明工数を減らす。',
    '教育資料の説明、理解度確認、アンケート不備チェックをAIで支援。

想定利用シーン:
朝の入場対応で、教育記録と確認作業を標準化する。

期待できる効果:
教育品質を揃え、監督員の個別説明工数を減らす。

MVPで確認したいこと:
- 実際に毎日使いたい場面があるか
- 既存業務のどこに組み込むと自然か
- 最初に必要な画面や入力項目は何か
- 導入時の懸念や条件は何か',
    '',
    '',
    'LP反応確認',
    now()
where not exists (
    select 1 from public.ideas where title = '新規入場者教育AIチェック'
);

insert into public.ideas
    (id, title, category, summary, user_scene, value, detail, image_path, external_url, status, created_at)
select
    gen_random_uuid(),
    '現場横断Power BIダッシュボード',
    'ダッシュボード',
    '工程、原価、安全指摘、是正、出来高を現場・支店・本社で共有。',
    '支店会議や本社報告で、各現場の状態を同じ数字で確認する。',
    '報告資料作成を減らし、遅延や是正遅れを早期発見する。',
    '工程、原価、安全指摘、是正、出来高を現場・支店・本社で共有。

想定利用シーン:
支店会議や本社報告で、各現場の状態を同じ数字で確認する。

期待できる効果:
報告資料作成を減らし、遅延や是正遅れを早期発見する。

MVPで確認したいこと:
- 実際に毎日使いたい場面があるか
- 既存業務のどこに組み込むと自然か
- 最初に必要な画面や入力項目は何か
- 導入時の懸念や条件は何か',
    '',
    '',
    'LP反応確認',
    now()
where not exists (
    select 1 from public.ideas where title = '現場横断Power BIダッシュボード'
);

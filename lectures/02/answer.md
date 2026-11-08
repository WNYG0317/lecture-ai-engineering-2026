# 第2回 解答

## 演習

- 使ったモデル・設定（`result.json` の `config` から）：
- "config": {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "seed": 42,
    "num_train_epochs": 20,
    "warmup_steps": 6,
    "lr": 0.0002,
    "lora_r": 16,
    "lora_alpha": 32,
    "max_seq_len": 512,
    "max_new_tokens": 96,
    "gen": {
      "do_sample": false
    }
- 自分で学習を実行したか（`executed_training_myself`）：はい / いいえ（実行できた範囲：　）
- はい
- 学習前：`format_rate` = 0.09523809523809523　 / `content_rate` =　0.0
- 学習後：`format_rate` =　1.0 / `content_rate` =　0.9047619047619048
※まとめ：
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 43.9  
- 退行した質問：
  []
- 学習後に残った失敗と、その型（根拠なしの質問に断定した / 根拠ありの質問に確認要求で逃げた / 形式の崩れ）：
    - {"answer": "質問は毎週火曜 17:00〜18:00 のオフィスアワーで受け付けます。", "needs_review": false}→形式崩れ
    - 学習前；{"answer": "確認が必要"}　学習後：{"answer": "提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}
    - 成績はいつ出ますか➡{"answer": "提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}	形式エラー
- 知識を問う質問（セクション 6）の結果（学習前の分類 → 学習後の分類）と気づいたこと：
    ・似たような項目を抽出して、解決済みとして誤ってneeds_reviewにする例
    ・
` 質問	FAQ にある	学習前の分類	学習前の出力	学習後の分類	学習後の出力
0	この講座の最終課題の締切はいつですか	False	format_error	{"answer": "9 月 30 日 23:59"}	asserted	{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}
1	担当教員の名前は何ですか	False	format_error	{"answer": "確認が必要"}	needs_review	{"answer": "この FAQ には記載がありません。運営に確認が必要です。", "needs_review": true}
2	次回の講義のテーマは何ですか	False	format_error	{"answer": "次回の講義のテーマは「学習ポータル」の「課題」欄で提出する PDF 1 ファイルを提出します。"}	needs_review	{"answer": "この FAQ には記載がありません。運営に確認が必要です。", "needs_review": true}
3	課題の提出期限はいつですか	False	format_error	{"answer": "9 月 30 日 23:59"}	asserted	{"answer": "課題の提出期限は 9 月 30 日 23:59（日本時間）です。", "needs_review": false}
`
- 学習で変わったこと・変わらなかったこと：

## 宿題
- 取り組んだレベル： 基礎
- 変えた設定やデータ：
      "lora_r": 14➡"lora_r": 16
- 結果（比較表や数字）：
"lora_r": 14➡"lora_r": 16の時：　
_    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 44.9_
以前の設定：
    "format_rate": 1.0,
    "content_rate": 0.9047619047619048,
    "both_rate": 0.9047619047619048,
    "seconds": 43.9
  (Note:結果変わらない？)
- ファインチューニングが向く場面・向かない場面についての考察：
  今回のタスクにおいてファインチューニングによって多少のコストがかかったものの、フォーマット適応などはコストのわりに改善が大きく、そのような微調整の改善を目標とした際にファインチューニングの意義は大きいのではないかと考えた。

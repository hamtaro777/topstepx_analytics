# TopstepX Analytics

TopstepX のトレードデータを取得・分析し、パフォーマンスをダッシュボードで可視化する Python アプリケーションです。

## 機能

- **データ同期** - TopstepX API からトレードデータを自動取得し SQLite に保存
- **パフォーマンス分析** - 損益、勝率、プロフィットファクター、リスクリワード比など 15 以上の KPI を算出
- **インタラクティブダッシュボード** - Streamlit + Plotly による 3 つのビュー
  - **Overview** - KPI カード、エクイティカーブ、日別損益、トレード時間分析
  - **Calendar** - 月別カレンダー形式の損益表示
  - **Trades** - フィルタ付きトレード履歴一覧
- **手数料計算** - CME 先物 30 以上の銘柄に対応した正確な手数料計算（取引所手数料 + NFA $0.04/枚）
- **CME セッション対応** - 日本時間ベースの取引日判定（冬時間 08:00 JST / 夏時間 07:00 JST）

## プロジェクト構成

```
topstepx_analytics/
├── main.py                 # エントリーポイント (CLI)
├── requirements.txt        # Python 依存パッケージ
├── .env.example.txt        # 環境変数テンプレート
├── config/
│   ├── settings.py         # 設定 (API URL, DB パス)
│   └── fees.py             # 銘柄別手数料・ポイント値
├── api/
│   └── client.py           # TopstepX API クライアント
├── database/
│   ├── schema.py           # DB スキーマ定義・初期化
│   └── repository.py       # データアクセス層
├── services/
│   ├── data_collector.py   # データ収集・同期
│   └── analytics.py        # パフォーマンス指標算出
├── dashboard/
│   ├── app.py              # Streamlit ダッシュボード
│   └── components/         # UI コンポーネント
└── data/                   # DB・エクスポートデータ (自動生成)
```

## セットアップ

### 必要環境

- Python 3.10+
- TopstepX アカウント（API キー）

### インストール

```bash
pip install -r requirements.txt
```

### 環境変数の設定

`.env.example.txt` を `.env` にコピーし、認証情報を設定してください。

```bash
cp .env.example.txt .env
```

```env
TOPSTEPX_USERNAME=your_username
TOPSTEPX_API_KEY=your_api_key
DATABASE_PATH=./data/trades.db
```

## 使い方

### データ同期 + ダッシュボード起動

```bash
python main.py --sync --days 30 --dashboard
```

### データ同期のみ

```bash
python main.py --sync --days 90
```

### ダッシュボードのみ起動

```bash
python main.py --dashboard
```

または直接 Streamlit で起動:

```bash
streamlit run dashboard/app.py
```

## 技術スタック

| カテゴリ | ライブラリ |
|---------|-----------|
| Web フレームワーク | Streamlit >=1.28.0 |
| データ処理 | pandas >=2.0.0, numpy >=1.24.0 |
| 可視化 | Plotly >=5.18.0 |
| HTTP クライアント | requests >=2.31.0 |
| 設定管理 | python-dotenv >=1.0.0 |
| データバリデーション | pydantic >=2.0.0 |
| 日付処理 | python-dateutil >=2.8.2 |

## ライセンス

Private

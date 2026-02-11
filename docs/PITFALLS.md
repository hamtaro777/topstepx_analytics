# TopstepX (ProjectX) API 開発の落とし穴

TopstepX Analytics の開発中に遭遇した問題と解決策をまとめています。
ProjectX Gateway API を使ってトレードデータを扱う際の参考にしてください。

---

## 1. contractId が同一銘柄でも一貫しない

**影響度: 致命的**

同一銘柄の注文でも、API が返す `contractId` の形式が異なる場合がある。

```json
// 同じ E-mini Nasdaq (ENQ) の注文なのに...
{ "contractId": "CON.F.US.ENQ.H26", "symbolId": "F.US.ENQ" }  // 通常
{ "contractId": "F.US.ENQ",          "symbolId": "F.US.ENQ" }  // 短縮形が混在！
```

`contractId` をキーにポジションを管理（FIFO マッチング）すると、一部の決済注文が別銘柄として扱われ、ポジションが未決済のまま残る。以降の全てのマッチングがカスケード的に狂い、P&L が大幅に間違う。

**対策**: ポジションのグルーピングには `symbolId` を使う。`symbolId` は全注文で一貫している。

```python
# NG: contractId でグルーピング
pos = positions[order.get('contractId', '')]

# OK: symbolId でグルーピング
symbol_key = order.get('symbolId') or order.get('contractId', '')
pos = positions[symbol_key]
```

fee やポイント値の計算には `CON.F.` 形式が必要なので、最初に見つかった `CON.F.` 形式の contractId を保持しておく。

---

## 2. Trade/search と Order/search の使い分け

**影響度: 高**

| エンドポイント | 用途 | P&L | タイムスタンプ |
|---|---|---|---|
| `/Trade/search` | 約定データ | プラットフォーム計算済み (`profitAndLoss`) | `creationTimestamp` = 約定時刻 |
| `/Order/search` | 注文データ | 自前で計算が必要 | `updateTimestamp` = 約定時刻（想定） |

- LIVE 口座では Trade/search が空を返すことがある。その場合は Order/search にフォールバックする
- Trade/search が**データを返すが `profitAndLoss` が null** のケースもある。`raw_data` の有無ではなく、**変換後の roundtrip 件数**でフォールバックを判断する

```python
# NG: raw_data が非空なら roundtrip 0件でもフォールバックしない
if raw_data:
    roundtrips = convert(raw_data)
elif is_live:
    # ← Trade/search がデータを返すとここに到達しない

# OK: roundtrip 件数で判断
roundtrips = convert(raw_data) if raw_data else []
if not roundtrips and is_live:
    raw_data = get_order_history(...)  # フォールバック
```

---

## 3. dict.get() は None をフォールバックしない

**影響度: 高**

Python の `dict.get(key, default)` はキーが**辞書に存在しない**場合のみ default を返す。
キーが存在して値が `None` の場合は `None` がそのまま返される。

```python
order = {"updateTimestamp": None, "creationTimestamp": "2026-02-05T14:41:16+00:00"}

# NG: updateTimestamp が None なので fallback されず None が返る
ts = order.get('updateTimestamp', order.get('creationTimestamp', ''))
# ts = None  ← ソート時に TypeError

# OK: or 演算子で falsy な値（None, ""）を正しくフォールバック
ts = order.get('updateTimestamp') or order.get('creationTimestamp') or ''
# ts = "2026-02-05T14:41:16+00:00"
```

特にソートキーで `None` と文字列が混在すると Python 3 では `TypeError` になる。

---

## 4. Order/search でのP&L手動計算にはポイント値が必須

**影響度: 高**

先物の P&L は価格差だけでは計算できない。各銘柄の**ポイント値（契約乗数）** を掛ける必要がある。

```
P&L = (exit_price - entry_price) * quantity * point_value
```

| 銘柄 | ポイント値 | 1ポイント動いた場合の損益 |
|------|-----------|------------------------|
| ES   | $50       | $50                    |
| NQ   | $20       | $20                    |
| MES  | $5        | $5                     |
| MNQ  | $2        | $2                     |
| RTY  | $50       | $50                    |
| CL   | $1,000    | $1,000                 |
| GC   | $100      | $100                   |

ポイント値を適用しないと、例えば ES で 1 ポイント動いた場合に $50 ではなく $1 と計算されてしまう。

---

## 5. INSERT が既存レコードを更新しない

**影響度: 中**

SQLite の `INSERT` は UNIQUE 制約違反時に `IntegrityError` を出す。
これを catch して `return False` するだけだと、ロジック修正後の再同期でデータが更新されない。

```python
# NG: 既存レコードがあると何もせず False
try:
    conn.execute("INSERT INTO trades (...) VALUES (?)")
except IntegrityError:
    return False

# OK: ON CONFLICT DO UPDATE で再同期時に既存レコードも更新
conn.execute("""
    INSERT INTO trades (...) VALUES (?)
    ON CONFLICT(account_id, symbol, entry_time) DO UPDATE SET
        pnl = excluded.pnl,
        fees = excluded.fees,
        exit_price = excluded.exit_price,
        ...
""")
```

---

## 6. extract_base_symbol が F.US.XXX 形式に未対応

**影響度: 中**

contractId には 2 つの形式が存在する:
- `CON.F.US.ENQ.H26` — 通常の Rithmic 形式
- `F.US.ENQ` — 短縮形（symbolId と同じ形式）

`extract_base_symbol()` は `CON.F.` プレフィックスのみ対応していると、短縮形からシンボルを抽出できず、fee やポイント値の lookup が失敗する。

```python
# CON.F.US.XXX.XXX 形式
if symbol.startswith('CON.F.'):
    base = symbol.split('.')[3]

# F.US.XXX 形式も対応が必要
if symbol.startswith('F.US.'):
    base = symbol.split('.')[2]
```

---

## 7. Order のタイムスタンプフィールドの使い分け

**影響度: 中**

| フィールド | 意味 |
|---|---|
| `creationTimestamp` | 注文が作成された時刻（指値注文は約定より前になる） |
| `updateTimestamp` | 注文が最後に更新された時刻（約定済み注文では約定時刻） |

FIFO マッチングでは**約定順**にソートする必要がある。`creationTimestamp` でソートすると、早くに発注された指値注文が実際の約定時刻より前に処理されてしまう。

```python
# 約定時刻でソート
sorted_orders = sorted(orders,
    key=lambda x: x.get('updateTimestamp') or x.get('creationTimestamp') or '')
```

---

## デバッグのヒント

### 生データの保存

API からの生レスポンスを JSON ファイルに保存しておくと、変換ロジックの問題を特定しやすい。

```python
# sync 実行時に data/raw_orders_{account_id}.json に自動保存される
python main.py --sync
```

### 確認すべきポイント

1. **contractId の一貫性**: 同一 symbolId で contractId が異なるオーダーがないか
2. **ソート順**: updateTimestamp でソートした結果が実際の約定順と一致するか
3. **ポジション残高**: 全オーダー処理後に未決済ポジションが残っていないか
4. **価格の妥当性**: filledPrice がティックサイズの倍数か（平均約定価格の場合は非標準の価格になりうる）

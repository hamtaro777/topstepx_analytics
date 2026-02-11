# 開発ノート - つまずきポイントと対策

本プロジェクト開発中に遭遇した問題と解決策をまとめたドキュメントです。

---

## 1. Streamlit が `$` を LaTeX として解釈する

### 問題

`st.markdown()` 内で通貨記号の `$` を使うと、Streamlit が LaTeX 数式のデリミタとして解釈し、意図しないフォント・色でレンダリングされる。

```python
# NG: $-5,516.00 | Fees: $ がLaTeX数式として描画される
st.markdown(f"**Gross P/L: ${pnl:,.2f} | Fees: ${fees:,.2f}**")
```

### 対策

`$` を `\$` でエスケープする。

```python
# OK
st.markdown(f"**Gross P/L: \\${pnl:,.2f} | Fees: \\${fees:,.2f}**")
```

---

## 2. インライン HTML/CSS のスタイリング戦略

### 問題

Streamlit のネイティブコンポーネントだけではダークテーマのカード UI やフォントサイズの細かな制御が困難。

### 対策

`st.markdown(..., unsafe_allow_html=True)` でインライン HTML/CSS を使用する。

```python
def _card_html(label: str, body: str, min_h: int = 120) -> str:
    return (
        f'<div style="background:{CARD_BG};padding:16px 20px;border-radius:8px;'
        f'border:1px solid {CARD_BORDER};min-height:{min_h}px;">'
        f'<div style="color:{LABEL_COLOR};font-size:12px;">{label}</div>'
        f'{body}'
        f'</div>'
    )
```

**ポイント:**

- カラー定数はモジュール上部で定義して統一管理する
- `_card_html()` のようなラッパー関数で HTML 生成を共通化する
- flexbox を活用してカード内のレイアウトを制御する

---

## 3. カード内レイアウト：縦積み vs 横並び

### 問題

メトリクスカードで数値とサブ情報を縦に積むと、カードの高さが増し、サブ情報のフォントが小さくなりすぎて視認性が低下する。

### 対策

`display: flex` で横並びにし、サブ情報のフォントサイズを大きくする。

```python
# 横並びレイアウト例（Avg Win / Avg Loss）
body = (
    f'<div style="display:flex;align-items:center;gap:16px;">'
    f'<div style="font-size:28px;font-weight:700;">{rr:.2f}</div>'
    f'<div style="flex:1;min-width:0;">'
    f'  <!-- バーグラフ + 損益数値 -->'
    f'</div></div>'
)
```

**適用箇所:** Trade Win %, Avg Win / Avg Loss, Profit Factor

---

## 4. Streamlit ネイティブ CSS の上書き

### 問題

Streamlit の内部スタイルが `!important` や `-webkit-` プレフィックスで適用されるため、通常の CSS では上書きできない。

### 対策

`data-testid` セレクタと `!important` を併用する。

```css
/* ヘッダーを透明化 */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* タブの文字色 - webkit対応が必須 */
.stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] {
    color: #8A8D98 !important;
    -webkit-text-fill-color: #8A8D98 !important;
}
```

---

## 5. カレンダーのフォントサイズバランス

### 問題

カレンダーセル内の損益とトレード数のフォントが小さすぎて読みにくい。セルの高さ（70px）に対して適切なバランスが必要。

### 対策

| 要素 | 調整前 | 調整後 |
|------|--------|--------|
| 損益（P/L） | 13px | 17px |
| トレード数 | 9px | 12px |

セルの `height: 70px` を維持しつつ、フォントサイズを上げて視認性を確保した。

---

## 6. 配布用リポジトリの作成

### 問題

開発リポジトリの git 履歴をそのまま公開したくない。

### 対策

orphan ブランチで履歴なしの初期コミットを作成して配布する。

```bash
git clone -b <branch> <dev-repo-url> temp-dist
cd temp-dist
git checkout --orphan main-clean
git add -A
git commit -m "Initial release"
git remote add dist <dist-repo-url>
git push dist main-clean:main
```

---

## 7. PowerShell と bash のコマンド差異

### 問題

Linux/macOS の bash コマンドが Windows PowerShell で動かない。

### よくある差異

| bash | PowerShell |
|------|-----------|
| `rm -rf dir` | `Remove-Item -Recurse -Force dir` |
| `export VAR=val` | `$env:VAR = "val"` |
| `source venv/bin/activate` | `.\venv\Scripts\Activate` |

---

## 8. 配布先での依存パッケージ不足

### 問題

クローンしたリポジトリで `python main.py --dashboard` を実行すると `streamlit` が見つからない。

### 対策

README やセットアップ手順に仮想環境の作成と依存インストールを明記する。

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python main.py --dashboard
```

---

## 9. カラーパレット定数の重複定義

### 現状

`metrics.py` と `calendar_view.py` で同じカラー定数を個別に定義している。

### 推奨改善

共通の `config/theme.py` に集約し、各コンポーネントからインポートする形にすると保守性が向上する。

```python
# config/theme.py
GREEN = "#00C853"
RED = "#FF5252"
CARD_BG = "#1A1D2E"
CARD_BORDER = "#2A2D3E"
LABEL_COLOR = "#8A8D98"
VALUE_COLOR = "#FFFFFF"
```

---

## 10. セッション状態の初期化

### 問題

`st.session_state` のキーに初期化なしでアクセスするとエラーになる。

### 対策

アプリ起動時にすべてのキーを初期化する。

```python
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'collector' not in st.session_state:
        st.session_state.collector = None
```

---

*最終更新: 2026-02-11*

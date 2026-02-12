# Raspberry Pi 動作改善レポート

## 目的
- Raspberry Pi 3 Model B 上での体感速度と安定性を継続改善する。
- 改善内容を「事例単位」で記録し、追加施策を追記しやすくする。

## 現在の問題認識
- ブラウザ、CLI、マウス操作を含め、全体的に挙動が重い。

## 計測メモ（共通）
- 計測日時:
- 計測者:
- 端末状態: （再起動直後 / 長時間稼働後 など）
- 観測指標:
  - 画面表示までの時間
  - 操作レスポンス（クリック、画面遷移）
  - CPU/メモリ使用率（必要に応じて）

## 改善事例ログ

### No.1 フロントエンドを `npm run dev` から `build` 配信に変更
- ステータス: 完了
- 実施日: 2026-02-12
- 対象:
  - `frontend/Dockerfile`
  - `docker-compose.yml`
- 背景:
  - `npm run dev`（Vite dev server）は開発向けで、Raspberry Pi では実行負荷が高くなりやすい。
- 実施内容:
  - `frontend/Dockerfile` を multi-stage build 化。
  - build ステージで `npm ci` と `npm run build` を実行。
  - runtime ステージを `nginx:alpine` にして `dist` を静的配信。
  - `docker-compose.yml` の `frontend` から `command: npm run dev -- --host` を削除。
  - `frontend` のコードマウント（`volumes`）を削除。
  - ポートを `5173:80` に変更（ホスト側は `5173` のまま）。
- 確認結果:
  - `free -h` 比較（Swap）

    | 指標 | 改善前 | 改善後 | 差分 |
    | --- | ---: | ---: | ---: |
    | Swap total | 905Mi | 905Mi | 0Mi |
    | Swap used | 454Mi | 6.2Mi | -447.8Mi |
    | Swap free | 451Mi | 899Mi | +448Mi |

  - 改善判断:
    - `Swap used` が **454Mi → 6.2Mi** まで減少し、swap 使用量は大幅に低下。
    - `Swap free` が **451Mi → 899Mi** まで増加し、メモリ逼迫時の退避領域に余裕が戻った。
    - 以上より、`npm run dev` 常駐をやめて `build + nginx` 配信にした効果として、メモリ圧迫（swap依存）が改善したと判断できる。
  - `docker compose config` で構成の整合性を確認済み。
  - 体感速度の定量比較は次回計測で追記予定。

### No.2 低スペック端末向けに hover/描画エフェクトを軽量化
- ステータス: 完了
- 実施日: 2026-02-12
- 対象:
  - `frontend/src/App.jsx`
  - `frontend/src/App.css`
- 背景:
  - ブラウザ内でカーソル移動時に重くなる症状が残っていた。
  - 原因候補のうち「高頻度イベント時の再描画負荷」は実装コストが低く、即効性が期待できる。
- 実施内容:
  - `navigator.hardwareConcurrency` / `navigator.deviceMemory` を使って低スペック端末を判定。
  - 低スペック端末では `app-lite` クラスを有効化し、以下を軽量化:
    - `tile:hover` と履歴行 hover の `transform` 無効化
    - 重い `box-shadow` の削減
    - タイル装飾（疑似要素）の無効化
    - 背景を単純化
  - あわせて `prefers-reduced-motion: reduce` 時の transition/transform を停止。
- 期待効果:
  - カーソル移動時の再描画コストを下げ、ブラウザ操作の引っ掛かりを減らす。
  - 低スペック環境でのフレーム落ちを抑制する。
- 確認結果:
  - フロントエンドの `npm run build` が成功（`vite build` 完了）。
- 備考:
  - UI演出は少し弱まるが、Raspberry Pi 3 環境では応答性を優先。

### 中間まとめ（2026-02-12時点）
- 実施済み改善:
  - No.1 `npm run dev` から `build + nginx` 配信へ変更
  - No.2 低スペック端末で hover/描画エフェクトを軽量化
- 確認できた効果:
  - `Swap used` が `454Mi -> 6.2Mi` に減少し、メモリ圧迫は大幅に改善
  - マウスポインタの動作は改善
- 残課題:
  - ブラウザ内でカーソル移動時に重くなる場面があるため、引き続き描画/入力イベント起因を優先調査する

---

## 追加調査（2026-02-12）
### 症状
- メモリ改善後、マウスポインタ自体は改善したが、ブラウザ上でカーソル移動時に重くなる。

### 原因候補（Web調査ベース）
- 1. 高頻度入力イベントの処理負荷
  - 根拠:
    - `mousemove` / `pointermove` は非常に高頻度で発火しうる（MDN）。
    - 入力ハンドラが重いとフレームをブロックし、カクつきの原因になる（web.dev）。
  - 想定:
    - カーソル移動に紐づくJS処理やDOM更新がメインスレッドを占有している。

- 2. メインスレッドの長時間タスク（Long Task）
  - 根拠:
    - 50ms超のタスクは応答性問題を起こしうる（Chrome公式）。
    - TBT（Total Blocking Time）は入力応答ブロック時間の指標（Lighthouse）。
  - 想定:
    - カーソル移動時のイベント処理でLong Taskが発生し、操作遅延が出ている。

- 3. CSS再計算・レイアウト再計算の負荷
  - 根拠:
    - `Recalculate Style` が長いとメインスレッド負荷になる（Chrome DevTools公式）。
    - Performance monitor で `Layouts/sec` や `style recalculations` を監視可能（Chrome DevTools公式）。
  - 想定:
    - hover時のスタイル変更やDOM更新が多く、再計算コストが高い。

- 4. 描画スタック/コンポジタ構成の影響（Wayland/X11, compositor）
  - 根拠:
    - Raspberry Pi公式はWayland/labwc移行を性能観点で説明している。
    - Chromiumはコンポジタ/レンダラの設計上、メインスレッド停滞が体感劣化に直結しやすい。
  - 想定:
    - OS側の描画バックエンドやブラウザ描画経路の相性で遅延が増幅している。

- 5. 低電圧・サーマルによるスロットリング
  - 根拠:
    - Raspberry Pi公式 `vcgencmd get_throttled` は undervoltage / throttling 判定ビットを提供。
    - 公式 `config.txt` 文書で、電圧低下時にCPU/GPUがスロットリングされる旨が明記。
  - 想定:
    - メモリ以外に、電源品質または温度でクロック低下が起きている。

- 6. GPUアクセラレーション経路の未活用・制限
  - 根拠:
    - Chromium設計文書では、GPU compositing により描画効率向上が期待できると説明されている。
    - Chromium公式の flags 文書では、起動オプションによってGPU挙動が変わるため、`chrome://version` で実際の command line 確認が推奨されている。
  - 想定:
    - GPU関連フラグ設定や環境要因により、描画負荷がCPU側に寄っている可能性がある。

### 調査からの判断（推定）
- 現状の症状は、`swap` 改善後も「ブラウザ内カーソル移動時」に限定して重い点から、
  - 最有力: `mousemove/pointermove` に伴うJS/CSS処理負荷
  - 次点: 描画経路（Wayland/X11・コンポジタ）または低電圧/熱スロットリング

### 参考リンク（一次情報中心）
- MDN mousemove:
  - https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event
- MDN pointermove:
  - https://developer.mozilla.org/en-US/docs/Web/Events/pointermove
- web.dev 入力ハンドラ最適化:
  - https://web.dev/articles/debounce-your-input-handlers
- Chrome DevTools Performance monitor:
  - https://developer.chrome.com/docs/devtools/performance-monitor
- Chrome DevTools Recalculate Style:
  - https://developer.chrome.com/docs/devtools/performance/selector-stats
- Chrome Long Animation Frames / Long task関連:
  - https://developer.chrome.com/docs/web-platform/long-animation-frames
- Lighthouse TBT:
  - https://developer.chrome.com/docs/lighthouse/performance/lighthouse-total-blocking-time
- Chromium compositor architecture:
  - https://www.chromium.org/developers/design-documents/compositor-thread-architecture/
- Chromium GPU accelerated compositing:
  - https://www.chromium.org/developers/design-documents/gpu-accelerated-compositing-in-chrome/
- Chromium run with flags:
  - https://www.chromium.org/developers/how-tos/run-chromium-with-flags
- Raspberry Pi `vcgencmd`:
  - https://www.raspberrypi.com/documentation/raspbian/applications/vcgencmd.md
- Raspberry Pi `config.txt`:
  - https://www.raspberrypi.com/documentation/computers/config_txt.html
- Raspberry Pi OS (Bookworm):
  - https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/
- Raspberry Pi OS (labwc移行):
  - https://www.raspberrypi.com/news/a-new-release-of-raspberry-pi-os/

---

## 追記用テンプレート

### No.X タイトル
- ステータス: 未着手 / 実施中 / 完了
- 実施日:
- 対象:
  - `path/to/file`
- 背景:
- 実施内容:
  - 
- 期待効果:
  - 
- 確認結果:
  - 
- 備考:
  - 

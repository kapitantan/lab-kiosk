## 1. システム概要

研究室内での物品購入・在庫管理を半自動化するシステム。

ラズベリーパイを用いた「オールインワン構成」で運用し、利用者はバーコードスキャンによるセルフ形式で購入を行う。

将来的なデータ分析を見据え、トランザクションベースのデータ設計を採用する。

## 2. アーキテクチャ構成

### 2.1 ハードウェア構成 (All-in-One)

- **サーバー端末:** Raspberry Pi 4 Model B (4GB以上) または Pi 5
- **ストレージ (要件A):** USB接続 SSD (OSブート および DBデータ保存用)
    - *理由:* SDカードの破損を防ぎ、長期運用に耐えるため必須。
- **入力デバイス:** USBバーコードリーダー (HIDモード/キーボードとして認識)
- **表示デバイス:** ラズパイに接続したモニター（キオスクモードで常時表示）

### 2.2 ネットワーク構成 (要件C)

- **内部アクセス:** `http://localhost` (ラズパイ自身のブラウザで表示)
- **外部アクセス:** **Tailscale** を利用
    - 研究室外や自宅からでも、Tailscale IP (`http://100.x.y.z`) 経由で在庫確認や管理画面へアクセス可能。
    - ポート開放が不要なため、大学のネットワークポリシーに抵触しにくい。

### 2.3 ソフトウェアスタック

すべて **Docker Compose** 上で稼働させます。

| **レイヤー** | **技術** | **備考** |
| --- | --- | --- |
| **Frontend** | **React + Vite** | AIエージェントにより生成。Tailwind CSSでスタイリング。 |
| **Backend** | **Django + DRF** | APIサーバー兼、管理画面（Admin）提供。 |
| **Database** | **PostgreSQL** | データ永続化。SSD上のDocker Volumeに保存。 |
| **Web Server** | **Nginx** | フロントエンドの静的配信 兼 リバースプロキシ。 |
| **Infra** | **Docker Compose** | コンテナオーケストレーション。 |

---

## 3. 機能要件

### 3.1 購買機能（キオスク端末）

- **常時待機画面:** 商品スキャン待ち状態。
- **カート機能:** 商品バーコードを連続スキャンしてリスト化。
- **購入確定:** 学生証（バーコード）をスキャンして購入完了。
    - *未登録学生証の場合:* エラーまたは新規登録画面へ誘導。

### 3.2 在庫管理機能（管理画面/PCブラウザ）

- **在庫一覧表示:** 現在の在庫数をリアルタイム表示。
- **入荷処理 (CSVインポート):**
    - 商品名、JANコード、入荷数などが記載されたCSVをDjango Adminからアップロード。
    - 自動的に `StockTransaction` (入荷) レコードを作成し、在庫を増やす。
- **商品マスタ管理:** 商品名、単価、閾値（通知ライン）の編集。

### 3.3 通知機能

- **~~Slack連携:~~**
    - ~~購入処理完了時、当該商品の在庫数が `threshold` (閾値) を下回った場合、指定したSlackチャンネルにWebhookで通知。~~

**Discord通知:**

- 購入処理完了時、当該商品の在庫数が `alert_threshold`（通知閾値）を下回った場合、指定したDiscordチャンネルの **Webhook URL** に通知する。

### 3.4 バックアップと保全 (要件A)

- **日次バックアップ:**
    - Cronで毎日深夜に `pg_dump` を実行。
    - ダンプファイルを外部ストレージ（Google Drive 等へrcloneで転送、または学内NASへ転送）に退避するスクリプトを稼働。

---

## 4. データベース設計 (Schema Draft)

DjangoのModelとして定義する設計案です。

```python
# 商品マスタ
class Product(models.Model):
    name = models.CharField("商品名")
    jan_code = models.CharField("JANコード", unique=True)
    price = models.IntegerField("単価")
    alert_threshold = models.IntegerField("通知閾値", default=3)
    # 現在在庫はTransactionからの計算、またはキャッシュフィールドとして保持

# 利用者
class User(models.Model):
    student_id_code = models.CharField("学生証番号", unique=True, db_index=True)
    name = models.CharField("氏名")
    #slack_id = models.CharField("Slack Member ID", blank=True)

# 入出庫履歴 (在庫計算の核心)
class StockTransaction(models.Model):
    TYPE_CHOICES = (
        ('IN', '入荷'),
        ('OUT', '購入'),
        ('ADJ', '棚卸調整'), # 在庫が合わない時の修正用
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    user = models.ForeignKey(User, null=True, blank=True) # 購入時のみ必須
    delta = models.IntegerField("変動数") # 入荷なら +10, 購入なら -1
    transaction_type = models.CharField(choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
```

---
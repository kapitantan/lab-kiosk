# 入荷（RESTOCK）API 仕様書

本ドキュメントは、商品入荷を扱う API（単品入荷・CSV一括入荷）の仕様を定義する。

---

## 1. 全体方針

- 商品の入荷は **StockTransaction** として管理する
- 入荷（RESTOCK）は購入（PURCHASE）や修正（CORRECTION）とは別のユースケースとして扱う
- **単品入荷 API** と **CSV 一括入荷 API** は分離する
- CSV 一括入荷では、**未登録商品が 1 件でも存在した場合は全体をエラーとしてロールバック**する
- 仕入単価（unit_cost）は販売価格（Product.price）とは別概念として扱う

---

## 2. データモデル

### StockTransaction の拡張

- `unit_cost` フィールドを追加する

例：
- 型：`IntegerField` または `DecimalField`
- 用途：仕入単価（原価）
- 備考：`Product.price`（販売価格）とは独立した概念

---

## 3. API 一覧

### 3.1 単品入荷 API

- **Method**：`POST`
- **Path**：`/transactions/restock`
- **実装方式**：`StockTransactionViewSet` の `@action`

#### Request Body

```json
{
  "jan_code": "4901234567890",
  "quantity": 10,
  "unit_cost": 120,
  "description": "初回入荷"
}

| フィールド | 必須 | 説明 |
|------------|------|------|
| jan_code | 必須 | 商品の JAN コード |
| quantity | 必須 | 入荷数量（0以上の整数） |
| unit_cost | 任意 | 仕入単価 |
| description | 任意 | 備考 |
```

---

## 3.2 CSV 一括入荷 API

- **Method**：`POST`
- **Path**：`/restocks/import`

---

## 4. CSV フォーマット仕様

### 4.1 必須カラム

- `jan_code`
- `quantity`（0以上の整数）

### 4.2 任意カラム

- `unit_cost`（int、仕入単価）
- `name`（商品名、確認用）

### 4.3 CSV 仕様上の注意

- 商品の特定および登録可否の判定は **jan_code のみ**で行う
- `name` は確認用途とし、DB 上の商品名と不一致の場合でもエラーにはしない
- 商品名不一致の場合は **warning** としてレスポンスに含める
- `quantity` が 0 未満の場合はエラーとする

---

## 5. CSV 一括入荷の処理ルール

- CSV 内に **未登録の商品（jan_code）が 1 件でも存在した場合**
  - 処理全体を失敗とする
  - **DB への書き込みは一切行わない（全体ロールバック）**
- バリデーションエラー（数量不正、型不正など）も同様に全体失敗とする
- トランザクション境界は **CSV 全体**

---

## 6. CSV 一括入荷 API レスポンス仕様

### 6.1 成功時（200 OK）

- 全行の取り込みに成功
- warning が存在する場合がある

```json
{
  "status": "ok",
  "import": {
    "created_count": 12,
    "skipped_count": 0
  },
  "warnings": [
    {
      "row": 5,
      "code": "NAME_MISMATCH",
      "jan_code": "4901234567890",
      "field": "name",
      "message": "CSVの商品名とDBの商品名が一致しません（CSV:AAA / DB:BBB）"
    }
  ]
}
```

### 6.2 エラー時

#### 400 Bad Request
- CSV の形式不正
- 型不正
- バリデーション不正（数値でない、必須カラム不足など）

#### 422 Unprocessable Entity
- CSV は読めるが業務ルール上受け付けられない場合
  - 未登録 JAN コード
  - 数量ルール違反など
  
```json
{
  "status": "error",
  "import": {
    "created_count": 0,
    "skipped_count": 1
  },
  "errors": [
    {
      "row": 3,
      "code": "UNKNOWN_JAN",
      "jan_code": "4900000000000",
      "field": "jan_code",
      "message": "未登録の商品です。先に商品登録してください"
    },
    {
      "row": 8,
      "code": "INVALID_QUANTITY",
      "jan_code": "4901234567890",
      "field": "quantity",
      "message": "quantityは正の整数で指定してください"
    }
  ]
}
```

### 6.3 その他ステータスコード

- 413 Payload Too Large
  - アップロードされた CSV ファイルが大きすぎる場合
- 415 Unsupported Media Type
  - CSV 以外のファイルが送信された場合

### 8. CSV の取り込み方法
- Content-Type：multipart/form-data
- 入力フィールド
  - file：CSV ファイル
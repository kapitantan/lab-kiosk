import { useEffect, useMemo, useState } from 'react'
import './App.css'

const PAGES = {
  home: 'home',
  register: 'register',
  purchase: 'purchase',
  entry: 'entry',
  correction: 'correction',
}

const NAV_ITEMS = [
  {
    key: PAGES.register,
    title: 'ユーザー登録',
    subtitle: 'USER REGISTRATION',
    color: 'tile-navy',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm7 9v-1a6 6 0 0 0-6-6H11a6 6 0 0 0-6 6v1Z" />
        <path d="M19 9h-2V7h-2V5h2V3h2v2h2v2h-2Z" />
      </svg>
    ),
  },
  {
    key: PAGES.purchase,
    title: '商品購入',
    subtitle: 'PRODUCT PURCHASE',
    color: 'tile-blue',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 6h13l-1.3 7.5a2 2 0 0 1-2 1.6H9.3a2 2 0 0 1-2-1.6L6 6Z" />
        <path d="M9 6a3 3 0 1 1 6 0" />
        <circle cx="9" cy="20" r="1.5" />
        <circle cx="17" cy="20" r="1.5" />
      </svg>
    ),
  },
  {
    key: PAGES.entry,
    title: '商品登録',
    subtitle: 'PRODUCT ENTRY',
    color: 'tile-teal',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 4h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
        <path d="M8 8h8M8 12h8M8 16h5" />
        <path d="M16 15h5v5h-5z" />
      </svg>
    ),
  },
  {
    key: PAGES.correction,
    title: '取消・修正',
    subtitle: 'CORRECTION',
    color: 'tile-slate',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 5h12a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9l-4 3v-3H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
        <path d="M9 10h6M9 14h4" />
      </svg>
    ),
  },
]

const formatDate = (value) =>
  value.toLocaleDateString('ja-JP', {
    month: 'short',
    day: 'numeric',
    weekday: 'short',
  })

const formatTime = (value) =>
  value.toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  })

function App() {
  const [page, setPage] = useState(PAGES.home)
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000 * 30)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    fetch(`${API_BASE}/csrf`, { credentials: 'include' }).catch(() => {})
  }, [])

  const dateLabel = useMemo(() => formatDate(now), [now])
  const timeLabel = useMemo(() => formatTime(now), [now])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">KM</div>
          <div>
            <div className="brand-title">Kiosk Manager</div>
            <div className="brand-sub">INTERNATIONAL ACADEMY CLUB</div>
          </div>
        </div>
        <div className="topbar-right">
          <div className="status">
            <span className="status-dot" />
            System Online
          </div>
          <div className="date">{dateLabel}</div>
          <div className="time-pill">{timeLabel}</div>
        </div>
      </header>

      {page === PAGES.home ? (
        <main className="home">
          <div className="hero">
            <h1>在庫・販売 キオスク</h1>
            <p>操作を選択してください。タッチ操作でも利用できます。</p>
          </div>
          <section className="tiles">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                className={`tile ${item.color}`}
                onClick={() => setPage(item.key)}
              >
                <span className="tile-icon">{item.icon}</span>
                <span className="tile-title">{item.title}</span>
                <span className="tile-sub">{item.subtitle}</span>
              </button>
            ))}
          </section>
          <footer className="footer">
            <button className="ghost">ヘルプセンター</button>
            <button className="ghost">システム設定</button>
            <span className="footer-status">SYSTEM READY</span>
          </footer>
        </main>
      ) : (
        <main className="screen">
          <div className="screen-header">
            <button className="back" onClick={() => setPage(PAGES.home)}>
              ← 戻る
            </button>
            <div>
              <div className="screen-title">{getTitle(page)}</div>
              <div className="screen-sub">バックエンド仕様に合わせた入力項目のみ表示します</div>
            </div>
            <button className="support">サポート</button>
          </div>
          <div className="screen-body">
            {page === PAGES.register && <UserRegistration />}
            {page === PAGES.purchase && <ProductPurchase />}
            {page === PAGES.entry && <ProductEntry />}
            {page === PAGES.correction && <Correction />}
          </div>
        </main>
      )}
    </div>
  )
}

const Field = ({ label, placeholder, type = 'text' }) => (
  <label className="field">
    <span>{label}</span>
    <input type={type} placeholder={placeholder} />
  </label>
)

const Section = ({ title, children }) => (
  <section className="card">
    <div className="card-title">{title}</div>
    <div className="grid">{children}</div>
  </section>
)

const Notice = ({ children }) => <div className="notice">{children}</div>

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

const getCookie = (name) => {
  const match = document.cookie.match(new RegExp(`(^|;)\\s*${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

const apiPostJson = async (path, body) => {
  const csrfToken = getCookie('csrftoken')
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    credentials: 'include',
    body: JSON.stringify(body),
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = data.error || data.message || 'request_failed'
    throw new Error(message)
  }
  return data
}

const apiGetJson = async (path) => {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    credentials: 'include',
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = data.error || data.message || 'request_failed'
    throw new Error(message)
  }
  return data
}

const UserRegistration = () => (
  <div className="stack">
    <Section title="ユーザー登録">
      <Notice>
        この画面の登録APIは現在バックエンド未実装です。管理画面での登録が必要です。
      </Notice>
    </Section>
  </div>
)

const ProductPurchase = () => {
  const [studentId, setStudentId] = useState('')
  const [janCode, setJanCode] = useState('')
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState(false)

  const onSubmit = async () => {
    if (!studentId || !janCode) {
      setStatus({ type: 'error', message: '学生証番号とJANコードは必須です。' })
      return
    }
    setBusy(true)
    setStatus(null)
    try {
      const data = await apiPostJson('/purchases', {
        student_id: studentId,
        jan_code: janCode,
      })
      setStatus({
        type: 'success',
        message: `購入完了: ${data.product} / 残数 ${data.remaining}`,
      })
    } catch (error) {
      setStatus({ type: 'error', message: `エラー: ${error.message}` })
    } finally {
      setBusy(false)
    }
  }

  const onClear = () => {
    setStudentId('')
    setJanCode('')
    setStatus(null)
  }

  return (
    <div className="stack">
      <Section title="購入情報">
        <label className="field">
          <span>学生証番号</span>
          <input
            value={studentId}
            onChange={(event) => setStudentId(event.target.value)}
            placeholder="student_id"
          />
        </label>
        <label className="field">
          <span>JANコード</span>
          <input
            value={janCode}
            onChange={(event) => setJanCode(event.target.value)}
            placeholder="jan_code"
          />
        </label>
      </Section>
      {status && <StatusBadge status={status} />}
      <div className="actions">
        <button className="primary" onClick={onSubmit} disabled={busy}>
          購入確定
        </button>
        <button className="secondary" onClick={onClear} disabled={busy}>
          クリア
        </button>
      </div>
    </div>
  )
}

const ProductEntry = () => {
  const [janCode, setJanCode] = useState('')
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [alertThreshold, setAlertThreshold] = useState('')
  const [status, setStatus] = useState(null)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [busy, setBusy] = useState(false)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [csvFile, setCsvFile] = useState(null)

  const onSubmit = async () => {
    if (!studentId || !janCode) {
      setStatus({ type: 'error', message: '学生証番号とJANコードは必須です。' })
      return
    }
    setBusy(true)
    setStatus(null)
    try {
      const payload = {
        jan_code: janCode,
        name,
        price: Number(price),
      }
      if (imageUrl) {
        payload.image_url = imageUrl
      }
      if (alertThreshold !== '') {
        payload.alert_threshold = Number(alertThreshold)
      }

      await apiPostJson('/products/register', payload)
      setStatus({ type: 'success', message: '商品を登録しました。' })
    } catch (error) {
      setStatus({ type: 'error', message: `エラー: ${error.message}` })
    } finally {
      setBusy(false)
    }
  }

  const onClear = () => {
    setJanCode('')
    setName('')
    setPrice('')
    setImageUrl('')
    setAlertThreshold('')
    setStatus(null)
  }

  const onUpload = async () => {
    if (!csvFile) {
      setUploadStatus({ type: 'error', message: 'CSVファイルを選択してください。' })
      return
    }

    setUploadBusy(true)
    setUploadStatus(null)
    try {
      const csrfToken = getCookie('csrftoken')
      const formData = new FormData()
      formData.append('file', csvFile)
      const response = await fetch(`${API_BASE}/restocks/import`, {
        method: 'POST',
        headers: {
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
        credentials: 'include',
        body: formData,
      })

      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        const message = data.message || data.error || 'upload_failed'
        throw new Error(message)
      }

      setUploadStatus({
        type: 'success',
        message: `一括入荷完了: ${data.import?.created_count ?? 0}件`,
      })
    } catch (error) {
      setUploadStatus({ type: 'error', message: `エラー: ${error.message}` })
    } finally {
      setUploadBusy(false)
    }
  }

  return (
    <div className="stack">
      <Section title="商品登録">
        <label className="field">
          <span>JANコード</span>
          <input
            value={janCode}
            onChange={(event) => setJanCode(event.target.value)}
            placeholder="jan_code"
          />
        </label>
        <label className="field">
          <span>商品名</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="name"
          />
        </label>
        <label className="field">
          <span>単価</span>
          <input
            type="number"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
            placeholder="price"
          />
        </label>
        <label className="field">
          <span>商品画像URL</span>
          <input
            value={imageUrl}
            onChange={(event) => setImageUrl(event.target.value)}
            placeholder="image_url"
          />
        </label>
        <label className="field">
          <span>通知閾値</span>
          <input
            type="number"
            value={alertThreshold}
            onChange={(event) => setAlertThreshold(event.target.value)}
            placeholder="alert_threshold"
          />
        </label>
      </Section>
      {status && <StatusBadge status={status} />}
      <div className="actions">
        <button className="primary" onClick={onSubmit} disabled={busy}>
          登録する
        </button>
        <button className="secondary" onClick={onClear} disabled={busy}>
          クリア
        </button>
      </div>

      <Section title="CSV一括入荷">
        <div className="grid upload-grid">
          <label className="field">
            <span>CSVファイル</span>
            <input
              type="file"
              accept=".csv"
              onChange={(event) => setCsvFile(event.target.files?.[0] || null)}
            />
          </label>
          <div className="upload-help">
            <p>必須カラム: jan_code, quantity</p>
            <p>任意カラム: unit_cost, name</p>
          </div>
        </div>
      </Section>
      {uploadStatus && <StatusBadge status={uploadStatus} />}
      <div className="actions">
        <button className="primary" onClick={onUpload} disabled={uploadBusy}>
          CSVを取り込む
        </button>
      </div>
    </div>
  )
}

const Correction = () => {
  const [transactionId, setTransactionId] = useState('')
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState(false)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [historyError, setHistoryError] = useState(null)

  const loadHistory = async () => {
    setLoading(true)
    setHistoryError(null)
    try {
      const data = await apiGetJson('/transactions')
      const items = Array.isArray(data.results) ? data.results : data
      setHistory(Array.isArray(items) ? items : [])
    } catch (error) {
      setHistoryError(`エラー: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const onSubmit = async () => {
    if (!transactionId) {
      setStatus({ type: 'error', message: '取引IDを入力してください。' })
      return
    }

    setBusy(true)
    setStatus(null)
    try {
      await apiPostJson(`/transactions/${transactionId}/amend`, {})
      setStatus({ type: 'success', message: '修正を適用しました。' })
    } catch (error) {
      setStatus({ type: 'error', message: `エラー: ${error.message}` })
    } finally {
      setBusy(false)
    }
  }

  const onClear = () => {
    setTransactionId('')
    setStatus(null)
  }

  return (
    <div className="stack">
      <Section title="取消・修正">
        <label className="field">
          <span>取引ID</span>
          <input
            value={transactionId}
            onChange={(event) => setTransactionId(event.target.value)}
            placeholder="transaction id"
          />
        </label>
      </Section>
      <Section title="取引履歴">
        <div className="history-block">
          <div className="history-header">
            <button className="ghost" onClick={loadHistory} disabled={loading}>
              更新
            </button>
            {loading && <span className="history-meta">読み込み中…</span>}
            {historyError && <span className="history-error">{historyError}</span>}
          </div>
          <div className="history-table">
            <div className="history-row head">
              <span>ID</span>
              <span>商品</span>
              <span>利用者</span>
              <span>種別</span>
              <span>数量</span>
              <span>日時</span>
            </div>
            {history.length === 0 ? (
              <div className="history-empty">履歴がありません。</div>
            ) : (
              history.map((item) => {
                const isSelected = String(item.id) === String(transactionId)
                return (
                  <button
                    type="button"
                    key={item.id}
                    className={`history-row selectable ${isSelected ? 'selected' : ''}`}
                    onClick={() => setTransactionId(String(item.id))}
                  >
                    <span>{item.id}</span>
                    <span>{item.product ?? '-'}</span>
                    <span>{item.user ?? '-'}</span>
                    <span>{item.transaction_type}</span>
                    <span>{item.delta}</span>
                    <span>{new Date(item.created_at).toLocaleString('ja-JP')}</span>
                  </button>
                )
              })
            )}
          </div>
        </div>
      </Section>
      {status && <StatusBadge status={status} />}
      <div className="actions">
        <button className="primary" onClick={onSubmit} disabled={busy}>
          修正を適用
        </button>
        <button className="secondary" onClick={onClear} disabled={busy}>
          クリア
        </button>
      </div>
    </div>
  )
}

const StatusBadge = ({ status }) => (
  <div className={`status-badge ${status.type}`}>
    {status.message}
  </div>
)

const getTitle = (page) => {
  switch (page) {
    case PAGES.register:
      return 'ユーザー登録'
    case PAGES.purchase:
      return '商品購入'
    case PAGES.entry:
      return '商品登録'
    case PAGES.correction:
      return '取消・修正'
    default:
      return ''
  }
}

export default App

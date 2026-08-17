import { useEffect, useRef, useState } from 'react'
import { analyzeResume } from './api/client'

const STEP_LABELS = ['Upload & confirm', 'Job description', 'Report']
const PROCESS_STAGES = [
  'Uploading resume…',
  'Parsing document & extracting sections…',
  'Extracting JD requirements…',
  'Scoring matches…',
  'Building report…',
]
const ACCEPTED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]
const ACCEPTED_EXTS = /\.(pdf|docx)$/i
const STAGE_INTERVAL_MS = 1100

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function getInitialTheme() {
  try {
    const saved = localStorage.getItem('theme')
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    /* localStorage unavailable — fall through to system preference */
  }
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function isSupportedFile(file) {
  return ACCEPTED_EXTS.test(file.name) || ACCEPTED_TYPES.includes(file.type)
}

function isPdfFile(file) {
  return file.type === 'application/pdf' || /\.pdf$/i.test(file.name)
}

export default function App() {
  const [theme, setTheme] = useState(getInitialTheme)
  const [step, setStep] = useState('upload')
  const [resumeFile, setResumeFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [confirmed, setConfirmed] = useState(false)
  const [jd, setJd] = useState('')
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [stageIndex, setStageIndex] = useState(0)
  const [error, setError] = useState(null)

  // --- Theme -------------------------------------------------------------
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      localStorage.setItem('theme', theme)
    } catch {
      /* non-fatal */
    }
  }, [theme])

  function toggleTheme() {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'))
  }

  // --- File upload / preview --------------------------------------------
  useEffect(() => {
    if (resumeFile && isPdfFile(resumeFile)) {
      const url = URL.createObjectURL(resumeFile)
      setPreviewUrl(url)
      return () => URL.revokeObjectURL(url)
    }
    setPreviewUrl(null)
  }, [resumeFile])

  function handleFile(file) {
    setError(null)
    if (!isSupportedFile(file)) {
      setFileError('Unsupported file. Please choose a PDF or DOCX resume.')
      return
    }
    setFileError(null)
    setResumeFile(file)
    setConfirmed(false) // a new file always needs a fresh confirmation
  }

  function clearFile() {
    setResumeFile(null)
    setPreviewUrl(null)
    setFileError(null)
    setConfirmed(false)
  }

  function confirmImport() {
    if (!resumeFile || fileError) return
    setConfirmed(true)
    setStep('jd')
  }

  // --- Analysis ----------------------------------------------------------
  useEffect(() => {
    if (!loading) return undefined
    const id = setInterval(
      () => setStageIndex((i) => Math.min(i + 1, PROCESS_STAGES.length - 1)),
      STAGE_INTERVAL_MS,
    )
    return () => clearInterval(id)
  }, [loading])

  // The backend is only ever called from runAnalysis, which is unreachable
  // until the user confirms the imported resume on the upload step.
  async function runAnalysis() {
    if (!confirmed || !resumeFile || !jd.trim() || loading) return
    setLoading(true)
    setError(null)
    setStageIndex(0)
    try {
      const result = await analyzeResume(resumeFile, jd)
      setReport(result)
      setStep('report')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  function startOver() {
    clearFile()
    setJd('')
    setReport(null)
    setError(null)
    setLoading(false)
    setStep('upload')
  }

  const stepIndex = step === 'upload' ? 0 : step === 'jd' ? 1 : 2

  return (
    <main className="app">
      <header className="app-header">
        <div>
          <h1>AI Placement Readiness Analyzer</h1>
          <p>Resume-to-JD grounded gap analysis &amp; interview preparation</p>
        </div>
        <button
          type="button"
          className="icon-btn"
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </header>

      <nav className="steps" aria-label="Analysis steps">
        {STEP_LABELS.map((label, i) => (
          <span
            key={label}
            className={
              i === stepIndex ? 'step active' : i < stepIndex ? 'step done' : 'step'
            }
          >
            {i + 1}. {label}
          </span>
        ))}
      </nav>

      {step === 'upload' && (
        <section className="card">
          <h2>Upload your resume</h2>
          <p className="muted">PDF or DOCX, up to ~5 pages. Preview it below, then confirm the import.</p>

          {fileError && <div className="error banner">{fileError}</div>}

          {!resumeFile ? (
            <Dropzone onFile={handleFile} />
          ) : (
            <PreviewCard
              file={resumeFile}
              previewUrl={previewUrl}
              confirmed={confirmed}
              onReplace={clearFile}
              onConfirm={confirmImport}
            />
          )}
        </section>
      )}

      {step === 'jd' && (
        <section className="card">
          <div className="jd-resume-bar">
            <span className={`file-chip ${isPdfFile(resumeFile) ? 'pdf' : 'docx'}`}>
              {resumeFile ? `✓ ${resumeFile.name}` : 'No resume'}
            </span>
            <button className="link-btn" onClick={() => setStep('upload')}>
              Change resume
            </button>
          </div>

          <h2>Paste the job description</h2>
          <textarea
            rows={10}
            value={jd}
            placeholder="Paste the target JD here (up to ~1,500 words)..."
            onChange={(e) => setJd(e.target.value)}
          />

          {error && (
            <div className="error banner">
              <div>
                <strong>Analysis failed</strong>
                <p>{error}</p>
              </div>
              <div className="actions">
                <button onClick={() => setError(null)}>Dismiss</button>
                <button className="primary" onClick={runAnalysis} disabled={loading}>
                  Retry
                </button>
              </div>
            </div>
          )}

          {loading && <ProgressPanel stage={PROCESS_STAGES[stageIndex]} />}

          <div className="actions">
            <button onClick={() => setStep('upload')} disabled={loading}>
              Back
            </button>
            <button
              className="primary"
              disabled={loading || !confirmed || !jd.trim()}
              onClick={runAnalysis}
            >
              {loading ? 'Analyzing…' : 'Run analysis'}
            </button>
          </div>
        </section>
      )}

      {step === 'report' && (
        <section className="card">
          <h2>Analysis report</h2>
          {report?.latency_ms != null && (
            <p className="muted">Completed in {Math.round(report.latency_ms)} ms</p>
          )}
          {report?.warnings?.map((warning) => (
            <p key={warning} className="warning banner">
              ⚠️ {warning}
            </p>
          ))}
          <h3>Extracted requirements ({report?.requirements.length ?? 0})</h3>
          <ul className="requirements">
            {report?.requirements.map((req) => (
              <li key={req.requirement_id}>
                <span className={req.category === 'nice-to-have' ? 'tag nice' : 'tag must'}>
                  {req.category}
                </span>{' '}
                {req.requirement_text}
              </li>
            ))}
          </ul>
          <h3>Interview questions</h3>
          {report?.interview_questions.length ? (
            <ol className="questions">
              {report.interview_questions.map((q) => (
                <li key={q.question_id}>{q.question_text}</li>
              ))}
            </ol>
          ) : (
            <p className="muted">Interview questions will appear once analysis is wired up.</p>
          )}
          <div className="actions">
            <button onClick={startOver}>Start new analysis</button>
          </div>
        </section>
      )}
    </main>
  )
}

// --- Upload primitives ----------------------------------------------------

function Dropzone({ onFile }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function pickFile(file) {
    if (file) onFile(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  return (
    <div
      className={`dropzone${dragging ? ' dragging' : ''}`}
      role="button"
      tabIndex={0}
      aria-label="Upload resume — drag and drop or browse files"
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false)
      }}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        hidden
        onChange={(e) => {
          pickFile(e.target.files?.[0])
          e.target.value = ''
        }}
      />
      <div className="dropzone-icon" aria-hidden="true">
        📄
      </div>
      <p>
        <strong>Drag &amp; drop</strong> your resume here, or <span className="link">browse files</span>
      </p>
      <p className="muted">PDF or DOCX · up to ~5 pages</p>
    </div>
  )
}

function PreviewCard({ file, previewUrl, confirmed, onReplace, onConfirm }) {
  const isPdf = isPdfFile(file)
  return (
    <div className="preview-card">
      <div className="preview-info">
        <div className="file-row">
          <span className={`file-icon ${isPdf ? 'pdf' : 'docx'}`} aria-hidden="true">
            {isPdf ? '📕' : '📘'}
          </span>
          <div className="file-meta">
            <p className="file-name" title={file.name}>
              {file.name}
            </p>
            <p className="muted">
              {formatBytes(file.size)} · {isPdf ? 'PDF' : 'DOCX'} document
            </p>
          </div>
        </div>

        {confirmed ? (
          <p className="confirmed-note">✓ Resume confirmed — analysis will run against this file.</p>
        ) : (
          !isPdf && (
            <p className="muted">
              DOCX files can't be rendered in-browser — the server extracts the text when you run the
              analysis.
            </p>
          )
        )}

        <div className="actions">
          {/* Replacing the file resets the confirmation (handleFile does), so it
              must stay available even after confirming, or "Change resume" on
              the JD step would lead to a dead end. */}
          <button onClick={onReplace}>Choose another</button>
          <button className="primary" onClick={onConfirm}>
            {confirmed ? 'Continue to job description' : 'Confirm import'}
          </button>
        </div>
      </div>

      {isPdf && previewUrl && (
        <div className="preview-frame">
          <iframe title="Resume preview" src={previewUrl} />
        </div>
      )}
    </div>
  )
}

function ProgressPanel({ stage }) {
  return (
    <div className="progress-panel" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <div className="progress-text">
        <p className="progress-stage">{stage}</p>
        <p className="muted">This usually takes under 15 seconds. Keep this tab open.</p>
      </div>
      <div className="progress-bar" aria-hidden="true">
        <div className="progress-bar-fill" />
      </div>
    </div>
  )
}

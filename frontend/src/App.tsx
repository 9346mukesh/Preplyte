import { useState } from 'react'
import { analyzeResume, type AnalysisReport } from './api/client'

type Step = 'upload' | 'jd' | 'report'

const STEP_LABELS = ['Upload resume', 'Paste job description', 'View report']

export default function App() {
  const [step, setStep] = useState<Step>('upload')
  const [resume, setResume] = useState<File | null>(null)
  const [jd, setJd] = useState('')
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runAnalysis() {
    if (!resume) return
    setLoading(true)
    setError(null)
    try {
      setReport(await analyzeResume(resume, jd))
      setStep('report')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const stepIndex = step === 'upload' ? 0 : step === 'jd' ? 1 : 2

  return (
    <main className="app">
      <header className="app-header">
        <h1>AI Placement Readiness Analyzer</h1>
        <p>Resume-to-JD grounded gap analysis &amp; interview preparation</p>
      </header>

      <nav className="steps" aria-label="Analysis steps">
        {STEP_LABELS.map((label, i) => (
          <span
            key={label}
            className={i === stepIndex ? 'step active' : i < stepIndex ? 'step done' : 'step'}
          >
            {i + 1}. {label}
          </span>
        ))}
      </nav>

      {error && <p className="error">{error}</p>}

      {step === 'upload' && (
        <section className="card">
          <h2>Upload your resume</h2>
          <p>PDF or DOCX, up to ~5 pages.</p>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) {
                setResume(file)
                setError(null)
              }
            }}
          />
          {resume && <p className="muted">Selected: {resume.name}</p>}
          <button
            className="primary"
            disabled={!resume}
            onClick={() => setStep('jd')}
          >
            Next: paste job description
          </button>
        </section>
      )}

      {step === 'jd' && (
        <section className="card">
          <h2>Paste the job description</h2>
          <textarea
            rows={10}
            value={jd}
            placeholder="Paste the target JD here (up to ~1,500 words)..."
            onChange={(e) => setJd(e.target.value)}
          />
          <div className="actions">
            <button onClick={() => setStep('upload')}>Back</button>
            <button className="primary" disabled={loading || !jd.trim()} onClick={runAnalysis}>
              {loading ? 'Analyzing...' : 'Run analysis'}
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
            <p key={warning} className="warning">
              ⚠️ {warning}
            </p>
          ))}
          <h3>Extracted requirements ({report?.requirements.length ?? 0})</h3>
          <ul>
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
            <ol>
              {report.interview_questions.map((q) => (
                <li key={q.question_id}>{q.question_text}</li>
              ))}
            </ol>
          ) : (
            <p className="muted">Interview questions will appear once analysis is wired up.</p>
          )}
          <div className="actions">
            <button onClick={() => setStep('jd')}>Analyze another</button>
          </div>
        </section>
      )}
    </main>
  )
}

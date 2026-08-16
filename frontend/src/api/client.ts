export interface JDRequirement {
  requirement_id: string
  requirement_text: string
  category: 'must-have' | 'nice-to-have'
}

export interface AnalysisResult {
  requirement_id: string
  classification: 'present' | 'partial' | 'missing' | 'insufficient_evidence'
  evidence_citation?: string
  confidence_note?: string
}

export interface InterviewQuestion {
  question_id: string
  question_text: string
  question_type: 'technical' | 'behavioral'
}

export interface AnalysisReport {
  job_title?: string
  requirements: JDRequirement[]
  analyses: AnalysisResult[]
  interview_questions: InterviewQuestion[]
  warnings: string[]
  latency_ms?: number
}

export async function analyzeResume(
  resume: File,
  jobDescription: string,
): Promise<AnalysisReport> {
  const form = new FormData()
  form.append('resume', resume)
  form.append('job_description', jobDescription)

  const res = await fetch('/api/analyze', {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Analysis failed (${res.status})`)
  }
  return res.json()
}

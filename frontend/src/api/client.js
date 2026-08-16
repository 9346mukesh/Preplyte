export async function analyzeResume(resume, jobDescription) {
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

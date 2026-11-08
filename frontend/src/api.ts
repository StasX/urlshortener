export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export function csrfToken(cookie = document.cookie) {
  const item = cookie.split('; ').find(value => value.startsWith('csrf_access_token='))
  return item ? decodeURIComponent(item.slice('csrf_access_token='.length)) : ''
}

interface RequestOptions { method?: string; body?: unknown; signal?: AbortSignal }

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}

export async function api<T = unknown>(path: string, { method = 'GET', body, signal }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (!['GET', 'HEAD'].includes(method)) {
    const token = csrfToken()
    if (token) headers['X-CSRF-TOKEN'] = token
  }
  let response
  try {
    response = await fetch(`/api${path}`, {
      method, headers, credentials: 'same-origin', signal,
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
    throw new ApiError('Could not reach Shorty. Check your connection and try again.', 0)
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('auth-expired'))
    throw new ApiError(data?.error || 'Something went wrong. Please try again.', response.status)
  }
  return data as T
}

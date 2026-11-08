import { afterEach, beforeEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { api, ApiError, csrfToken } from '../src/api.ts'

const originalFetch = globalThis.fetch
beforeEach(() => {
  globalThis.document = { cookie: '' }
  globalThis.window = new EventTarget()
})
afterEach(() => { globalThis.fetch = originalFetch })

test('reads the double-submit CSRF cookie without reading the JWT', () => {
  assert.equal(csrfToken('other=a; csrf_access_token=token%2Dvalue'), 'token-value')
  assert.equal(csrfToken('other=a'), '')
})

test('authenticated deletes send CSRF and cookies and accept an empty response', async () => {
  document.cookie = 'csrf_access_token=csrf-test'
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/links/link-id')
    assert.equal(options.method, 'DELETE')
    assert.equal(options.headers['X-CSRF-TOKEN'], 'csrf-test')
    assert.equal(options.credentials, 'same-origin')
    return new Response(null, { status: 204 })
  }
  assert.equal(await api('/links/link-id', { method: 'DELETE' }), null)
})

test('guest link creation sends JSON without an authorization header', async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers.Authorization, undefined)
    assert.deepEqual(JSON.parse(options.body), { url: 'https://example.com' })
    return Response.json({ url: 'https://short.example/abc123' })
  }
  assert.equal((await api('/links', { method: 'POST', body: { url: 'https://example.com' } })).url, 'https://short.example/abc123')
})

test('a rejected sign-in clears frontend authentication state', async () => {
  let expired = false
  window.addEventListener('auth-expired', () => { expired = true })
  globalThis.fetch = async () => Response.json({ error: 'Your sign-in has expired.' }, { status: 401 })
  await assert.rejects(api('/links'), error => error instanceof ApiError && error.status === 401)
  assert.equal(expired, true)
})

test('rate-limit and connectivity failures provide useful error messages', async () => {
  globalThis.fetch = async () => Response.json({ error: 'Please wait a minute.' }, { status: 429 })
  await assert.rejects(api('/links'), /Please wait a minute/)
  globalThis.fetch = async () => { throw new TypeError('Network error') }
  await assert.rejects(api('/links'), /Check your connection/)
})

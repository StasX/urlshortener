import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const member = { id: '507f1f77bcf86cd799439012', first_name: 'Test', last_name: 'Member', email: 'test@example.com' }
async function mockSession(page: Page, signedIn = false) {
  await page.route('**/api/auth/me', route => route.fulfill({ json: { user: signedIn ? member : null } }))
}

test('guests can create links and see styled rate-limit errors', async ({ page }) => {
  await mockSession(page)
  let requests = 0
  await page.route('**/api/links', route => route.fulfill(++requests === 1
    ? { json: { url: 'http://localhost:5000/abc123' } }
    : { status: 429, json: { error: 'Too many requests. Please wait a minute and try again.' } }))
  await page.goto('/')
  await expect(page.getByText('Guest links expire after 24 hours', { exact: false })).toBeVisible()
  await page.getByLabel('Your destination URL').fill('https://example.com')
  await page.getByRole('button', { name: 'Create short link' }).click()
  await expect(page.locator('output')).toContainText('http://localhost:5000/abc123')
  await page.getByRole('button', { name: 'Create short link' }).click()
  await expect(page.getByRole('alert')).toContainText('Please wait a minute')
})

test('protected navigation signs in without a document reload and restores identity after reload', async ({ page }) => {
  let signedIn = false
  await page.route('**/api/auth/me', route => route.fulfill({ json: { user: signedIn ? member : null } }))
  await page.route('**/api/auth/login', route => { signedIn = true; return route.fulfill({ json: { user: member } }) })
  await page.route('**/api/links', route => route.fulfill({ json: [] }))
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/login/)
  await page.getByLabel('Email address').fill(member.email)
  await page.getByLabel('Password', { exact: true }).fill('test-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL('/dashboard')
  await expect(page.getByText('No links yet.', { exact: false })).toBeVisible()
  await page.reload()
  await expect(page.getByText('Hi, Test')).toBeVisible()
})

test('registration keeps password confirmation and creates an account', async ({ page }) => {
  await mockSession(page)
  await page.route('**/api/auth/register', route => route.fulfill({ status: 201, json: { user: member } }))
  await page.goto('/register')
  await page.getByLabel('First name').fill('Test')
  await page.getByLabel('Last name').fill('Member')
  await page.getByLabel('Email address').fill(member.email)
  await page.getByLabel('Password', { exact: true }).fill('test-password')
  await page.getByLabel('Repeat password').fill('different')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByRole('alert')).toHaveText('Passwords must match.')
  await page.getByLabel('Repeat password').fill('test-password')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByText('Hi, Test')).toBeVisible()
})

test('dashboard deletes update the view, send CSRF, and recover from errors', async ({ page, context }) => {
  await mockSession(page, true)
  await context.addCookies([{ name: 'csrf_access_token', value: 'test-csrf', domain: 'localhost', path: '/' }])
  await page.route('**/api/links', route => route.fulfill({ json: [{ id: 'link-id', shortUrl: 'http://localhost:5000/abc123', fullUrl: 'https://example.com/<script>', visits: 3 }] }))
  let requests = 0
  await page.route('**/api/links/link-id', route => {
    expect(route.request().headers()['x-csrf-token']).toBe('test-csrf')
    return route.fulfill(++requests === 1 ? { status: 500, json: { error: 'Could not remove the link.' } } : { status: 204 })
  })
  await page.goto('/dashboard')
  await expect(page.getByRole('img', { name: 'Visits per short link' })).toBeVisible()
  await page.getByRole('button', { name: 'Remove link' }).click()
  await expect(page.getByRole('alert')).toContainText('Could not remove')
  await expect(page.getByRole('button', { name: 'Remove link' })).toBeEnabled()
  await page.getByRole('button', { name: 'Remove link' }).click()
  await expect(page.getByText('No links yet.', { exact: false })).toBeVisible()
})

test('an expired sign-in returns to login and mobile navigation remains available', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await mockSession(page, true)
  await page.route('**/api/links', route => route.fulfill({ status: 401, json: { error: 'Your sign-in has expired.' } }))
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/login/)
  await expect(page.getByRole('link', { name: 'Link tools' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})

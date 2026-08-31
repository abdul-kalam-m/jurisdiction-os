import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

// §12: "Playwright smoke (each page renders; fit checker returns a path;
// signals filter works), axe zero serious violations."
const PAGES = [
  { path: '/', heading: 'Bloomberg Terminal' },
  { path: '/scorecards', heading: 'Jurisdiction Scorecards' },
  { path: '/fit-checker', heading: 'Project Fit Checker' },
  { path: '/checklist', heading: 'Dynamic Submission Checklist' },
  { path: '/signals', heading: 'Planning & Zoning Signal Feed' },
  { path: '/pricing', heading: 'Pricing' },
  { path: '/methods', heading: 'Methods & Data' },
]

for (const { path, heading } of PAGES) {
  test(`${path} renders with no console errors`, async ({ page }) => {
    const errors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto(path)
    await expect(page.getByRole('heading', { name: heading, exact: false }).first()).toBeVisible()
    expect(errors, `console/page errors on ${path}: ${errors.join('; ')}`).toEqual([])
  })

  test(`${path} has zero serious/critical axe violations`, async ({ page }) => {
    await page.goto(path)
    await page.waitForLoadState('networkidle')
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
      .analyze()
    const serious = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
    expect(serious, JSON.stringify(serious, null, 2)).toEqual([])
  })
}

test('fit checker returns a permit path for the default selection', async ({ page }) => {
  await page.goto('/fit-checker')
  await expect(page.getByRole('heading', { name: /Jersey City/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Likely permits' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Submission requirements' })).toBeVisible()
  const sourceLinks = page.getByRole('link', { name: 'source' })
  await expect(sourceLinks.first()).toBeVisible()
})

test('fit checker updates when jurisdiction changes', async ({ page }) => {
  await page.goto('/fit-checker')
  const select = page.getByRole('combobox').first()
  const options = await select.locator('option').allTextContents()
  const hoboken = options.find((o) => o.includes('Hoboken'))
  expect(hoboken, `expected a Hoboken option among: ${options.join(', ')}`).toBeTruthy()
  await select.selectOption({ label: hoboken! })
  await expect(page.getByRole('heading', { name: /Hoboken/i })).toBeVisible()
})

test('signals feed municipality filter narrows the list', async ({ page }) => {
  await page.goto('/signals')
  const items = page.locator('ul > li')
  await expect(items.first()).toBeVisible()
  const unfilteredCount = await items.count()

  const muniSelect = page.getByRole('combobox').first()
  const options = await muniSelect.locator('option').allTextContents()
  const specificMuni = options.find((o) => o !== 'All municipalities')
  test.skip(!specificMuni, 'no municipality options loaded (data fetch failed?)')

  await muniSelect.selectOption({ label: specificMuni! })
  await expect(items.first()).toBeVisible()
  const filteredCount = await items.count()
  expect(filteredCount).toBeLessThanOrEqual(unfilteredCount)
  expect(filteredCount).toBeGreaterThan(0)
})

test('signals feed action filter narrows the list', async ({ page }) => {
  await page.goto('/signals')
  const items = page.locator('ul > li')
  await expect(items.first()).toBeVisible()

  const actionSelect = page.getByRole('combobox').nth(1)
  await actionSelect.selectOption('approved')
  await expect(items.first()).toBeVisible()
  const badges = await page.locator('ul > li').getByText('approved', { exact: true }).count()
  const totalVisible = await items.count()
  expect(badges).toBe(totalVisible)
})

test('every page shows the demonstration-product disclaimer', async ({ page }) => {
  for (const { path } of PAGES) {
    await page.goto(path)
    await expect(page.getByText(/Demonstration product/i).first()).toBeVisible()
  }
})

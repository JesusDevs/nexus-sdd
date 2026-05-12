---
name: playwright
description: Playwright para E2E testing cross-browser con fixtures, trazabilidad, y CI
category: testing
stack: [playwright, typescript, javascript, e2e, browser, chromium, firefox, webkit]
triggers: [playwright, e2e, browser, page, locator, chromium, firefox, webkit]
---

# Playwright Skill

## Agent Attitude
Eres un QA Automation Engineer especializado en E2E.
Tests deterministas. NUNCA `waitForTimeout` sin razon.
Locators basados en rol/texto, no en CSS fragil.
Cada flujo critico del spec tiene su test E2E.

## Rules
- `page.getByRole()` y `page.getByLabel()` sobre selectores CSS.
- `page.waitForResponse()` para esperar APIs. NO `waitForTimeout`.
- Fixtures para datos de prueba (login, seeds).
- `test.describe` para agrupar flujos relacionados.
- `test.beforeEach` para estado inicial limpio.
- `webServer` en config para levantar el app automaticamente.
- `trace: 'on-first-retry'` para debugging.

## Do's
- Tests independientes (cada test su propio contexto).
- `expect(locator).toBeVisible()` antes de interactuar.
- `page.route()` para mockear APIs externas en tests.
- `storageState` para reutilizar sesiones autenticadas.
- `test.step` para legibilidad en flujos largos.
- Screenshots en fallos (`screenshot: 'only-on-failure'`).

## Don'ts
- NO `waitForTimeout(5000)` — usa `waitForSelector` o `waitForResponse`.
- NO selectores CSS anidados complejos.
- NO tests que dependen de orden de ejecucion.
- NO `.click()` sin antes verificar que el elemento esta habilitado.
- NO tests de +30 lineas sin `test.step`.
- NO `test.only` commiteado.

## Example E2E for OpenSpec HDU
```typescript
import { test, expect } from '@playwright/test';

test.describe('HDU-01: User Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('successful login redirects to dashboard', async ({ page }) => {
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('ValidPass1!');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome back')).toBeVisible();
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('Wrong!');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Invalid credentials')).toBeVisible();
  });
});
```

## Recommended Commands
- `npx playwright test` — Run all E2E
- `npx playwright test --ui` — Interactive mode
- `npx playwright show-trace test-results/.../trace.zip` — Debug
- `npx playwright codegen localhost:3000` — Record tests

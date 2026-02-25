import { test, expect } from '@playwright/test';

test.describe('Home Page E2E Tests', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/OpsPilot/);
  });

  test('should display welcome message', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText(/欢迎|welcome/i)).toBeVisible();
  });

  test('should have task input', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByPlaceholder(/输入任务|task/i)).toBeVisible();
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('/');
    await page.click('text=/仪表盘|dashboard/i');
    await expect(page).toHaveURL(/dashboard/);
  });
});

test.describe('Dashboard E2E Tests', () => {
  test('should load dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByText(/控制中心|dashboard/i)).toBeVisible();
  });

  test('should display stats cards', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByText(/活跃任务|active tasks/i)).toBeVisible();
  });
});

test.describe('Navigation E2E Tests', () => {
  test('should navigate to tasks page', async ({ page }) => {
  await page.goto('/tasks');
  await expect(page.locator('body')).toBeVisible();
});

test('should navigate to settings page', async ({ page }) => {
  await page.goto('/settings');
  await expect(page.locator('body')).toBeVisible();
});

  test('should navigate to agents page', async ({ page }) => {
    await page.goto('/agents');
    // Just check that page loads without error
    await expect(page.locator('body')).toBeVisible();
  });});

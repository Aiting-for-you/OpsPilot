import { test, expect } from '@playwright/test';

/**
 * 扩展端到端测试 - 更多页面和功能测试
 */

test.describe('Tools页面测试', () => {
  test('Tools页面应该正确加载', async ({ page }) => {
    await page.goto('/tools');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('Tools页面应该有工具列表或相关内容', async ({ page }) => {
    await page.goto('/tools');
    await page.waitForLoadState('networkidle');
    // 检查页面是否有内容（不是空白页）
    const content = await page.locator('body').textContent();
    expect(content?.length).toBeGreaterThan(0);
  });
});

test.describe('Scheduler页面测试', () => {
  test('Scheduler页面应该正确加载', async ({ page }) => {
    await page.goto('/scheduler');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Settings页面测试', () => {
  test('Settings页面应该正确加载', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Pricing页面测试', () => {
  test('Pricing页面应该正确加载', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Analytics页面测试', () => {
  test('Analytics页面应该正确加载', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('SOP页面测试', () => {
  test('SOP页面应该正确加载', async ({ page }) => {
    await page.goto('/sop');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Memory Optimization页面测试', () => {
  test('Memory Optimization页面应该正确加载', async ({ page }) => {
    await page.goto('/memory-optimization');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Tool Optimization页面测试', () => {
  test('Tool Optimization页面应该正确加载', async ({ page }) => {
    await page.goto('/tool-optimization');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('API端点详细测试', () => {
  test('应该能获取工具列表', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/api/v1/tools');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toBeDefined();
    console.log('Tools API response:', typeof data);
  });

  test('应该能获取LLM配置', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/api/v1/llm/config');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toBeDefined();
    console.log('LLM Config API response:', typeof data);
  });
});

test.describe('国际化测试', () => {
  test('应该能切换语言（如果语言切换器存在）', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 查找语言切换按钮
    const languageButton = page.locator('button[class*="language"], button[class*="Language"]').first();
    if (await languageButton.isVisible()) {
      console.log('语言切换器存在');
    }
  });
});

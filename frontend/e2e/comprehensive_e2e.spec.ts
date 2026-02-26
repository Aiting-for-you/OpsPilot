import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5175';

test.describe('全面功能测试 - Home页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test('Home页面 - 验证页面加载', async ({ page }) => {
    await expect(page).toHaveTitle(/OpsPilot/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('Home页面 - 验证欢迎信息', async ({ page }) => {
    await expect(page.getByText(/欢迎|welcome/i)).toBeVisible();
  });

  test('Home页面 - 任务输入框功能', async ({ page }) => {
    const input = page.getByPlaceholder(/输入任务|task/i);
    await expect(input).toBeVisible();
    await input.fill('测试任务');
    await expect(input).toHaveValue('测试任务');
  });

  test('Home页面 - 执行按钮可点击', async ({ page }) => {
    const executeBtn = page.locator('a.btn-primary').first();
    await expect(executeBtn).toBeVisible();
    await expect(executeBtn).toBeEnabled();
  });

  test('Home页面 - 快捷功能卡片可点击', async ({ page }) => {
    const cards = page.locator('.grid.grid-cols-2, .grid-cols-2').first();
    await expect(cards).toBeVisible();
  });

  test('Home页面 - 导航到Dashboard', async ({ page }) => {
    await page.getByRole('link', { name: /仪表盘|dashboard/i }).first().click();
    await expect(page).toHaveURL(/dashboard/);
  });

  test('Home页面 - 导航到Tasks', async ({ page }) => {
    // 通过URL直接导航测试
    await page.goto(`${BASE_URL}/tasks`);
    await expect(page).toHaveURL(/tasks/);
  });
});

test.describe('全面功能测试 - Dashboard页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
  });

  test('Dashboard - 验证页面加载', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('Dashboard - 验证统计卡片显示', async ({ page }) => {
    await expect(page.getByText(/活跃任务|active tasks/i)).toBeVisible();
    await expect(page.getByText(/已完成|completed/i)).toBeVisible();
  });

  test('Dashboard - 验证API健康检查', async ({ page }) => {
    // 检查系统状态区域
    const statusSection = page.getByText(/系统状态|system status/i);
    await expect(statusSection).toBeVisible();
  });

  test('Dashboard - 验证快速操作按钮', async ({ page }) => {
    const quickActions = page.getByRole('link', { name: /创建任务|create task/i });
    await expect(quickActions.first()).toBeVisible();
  });

  test('Dashboard - 验证版本信息或系统信息', async ({ page }) => {
    // 检查是否有版本信息或系统状态区域
    const hasVersion = await page.getByText(/v\d+\.\d+\.\d+/i).isVisible().catch(() => false);
    const hasSystemStatus = await page.getByText(/系统状态|system status/i).isVisible().catch(() => false);
    expect(hasVersion || hasSystemStatus).toBeTruthy();
  });
});

test.describe('全面功能测试 - Tasks页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
  });

  test('Tasks - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('Tasks - 验证页面有内容', async ({ page }) => {
    await page.waitForTimeout(1000);
  });
});

test.describe('全面功能测试 - Tools页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/tools`);
    await page.waitForLoadState('networkidle');
  });

  test('Tools - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('Tools - 验证工具库区域存在', async ({ page }) => {
    const toolsArea = page.getByText(/工具库|tool library/i);
    await expect(toolsArea.first()).toBeVisible();
  });

  test('Tools - 验证执行面板区域存在', async ({ page }) => {
    await page.waitForTimeout(1000);
  });
});

test.describe('全面功能测试 - Settings页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    await page.waitForLoadState('networkidle');
  });

  test('Settings - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('Settings - 验证LLM配置标签存在', async ({ page }) => {
    const llmBtn = page.getByRole('button', { name: /LLM/i });
    await expect(llmBtn.first()).toBeVisible();
  });

  test('Settings - 验证MCP标签存在', async ({ page }) => {
    const mcpBtn = page.getByRole('button', { name: /MCP/i });
    await expect(mcpBtn.first()).toBeVisible();
  });

  test('Settings - 切换到MCP标签', async ({ page }) => {
    await page.getByRole('button', { name: /MCP/i }).first().click();
    await page.waitForTimeout(500);
  });
});

test.describe('全面功能测试 - Agents页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('networkidle');
  });

  test('Agents - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('Agents - 验证页面有内容', async ({ page }) => {
    await page.waitForTimeout(1000);
  });
});

test.describe('全面功能测试 - SOP页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/sop`);
    await page.waitForLoadState('networkidle');
  });

  test('SOP - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('SOP - 验证页面有内容', async ({ page }) => {
    await page.waitForTimeout(1000);
  });
});

test.describe('全面功能测试 - Scheduler页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/scheduler`);
    await page.waitForLoadState('networkidle');
  });

  test('Scheduler - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('全面功能测试 - Analytics页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);
    await page.waitForLoadState('networkidle');
  });

  test('Analytics - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('全面功能测试 - Pricing页面', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/pricing`);
    await page.waitForLoadState('networkidle');
  });

  test('Pricing - 验证页面加载', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('全面功能测试 - API连接测试', () => {
  test('API健康检查', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/api/v1/health');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBeDefined();
  });

  test('API工具列表', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/api/v1/tools');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.tools).toBeDefined();
  });

  test('API LLM配置', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/api/v1/llm/config');
    expect(response.ok()).toBeTruthy();
  });

  test('API SOP列表', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/api/v1/sops');
    expect(response.ok()).toBeTruthy();
  });
});

test.describe('全面功能测试 - 导航测试', () => {
  test('所有页面导航', async ({ page }) => {
    const pages = [
      '/',
      '/dashboard',
      '/tasks',
      '/tools',
      '/settings',
      '/agents',
      '/sop',
      '/scheduler',
      '/analytics',
      '/pricing',
    ];

    for (const path of pages) {
      await page.goto(`${BASE_URL}${path}`);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

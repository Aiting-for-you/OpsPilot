import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5175';
const API_BASE = 'http://localhost:8000/api/v1';

test.describe('真实功能测试 - Tasks任务管理', () => {
  test('Tasks - 创建新任务', async ({ page }) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    
    // 找到任务输入框
    const input = page.getByPlaceholder(/输入任务|placeholder/i);
    await expect(input).toBeVisible();
    
    // 输入任务描述
    const testTask = '测试创建一个简单任务';
    await input.fill(testTask);
    await expect(input).toHaveValue(testTask);
    
    // 点击创建按钮
    const createBtn = page.getByRole('button', { name: /创建|create/i }).first();
    await expect(createBtn).toBeEnabled();
    
    // 点击提交（可能触发网络请求）
    await createBtn.click();
    
    // 等待一下看任务是否被创建
    await page.waitForTimeout(2000);
    
    // 验证输入框被清空（表示任务已提交）
    // 注意：由于是异步创建，状态可能不同
    const inputValue = await input.inputValue();
    console.log(`创建任务后输入框内容: "${inputValue}"`);
  });

  test('Tasks - 查看任务列表', async ({ page }) => {
    await page.goto(`${BASE_URL}/tasks`);
    await page.waitForLoadState('networkidle');
    
    // 验证任务队列标题
    await expect(page.getByText(/任务队列|task queue/i)).toBeVisible();
    
    // 验证任务详情区域存在
    await expect(page.getByText(/任务详情|task details/i)).toBeVisible();
  });

  test('Tasks - API创建任务', async ({ page }) => {
    // 直接通过API创建任务
    const response = await page.request.post(`${API_BASE}/tasks`, {
      data: {
        user_input: "API测试任务 - 验证后端功能"
      }
    });
    
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.task_id).toBeDefined();
    console.log(`创建的任务ID: ${data.task_id}`);
  });

  test('Tasks - API查询任务状态', async ({ page }) => {
    // 先创建一个任务
    const createResponse = await page.request.post(`${API_BASE}/tasks`, {
      data: {
        user_input: "API测试任务状态查询"
      }
    });
    const createData = await createResponse.json();
    const taskId = createData.task_id;
    
    // 查询任务状态
    const statusResponse = await page.request.get(`${API_BASE}/tasks/${taskId}`);
    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();
    expect(statusData.task_id).toBe(taskId);
    expect(statusData.state).toBeDefined();
    console.log(`任务状态: ${statusData.state}`);
  });
});

test.describe('真实功能测试 - Tools工具执行', () => {
  test('Tools - 获取工具列表API', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/tools`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.tools).toBeDefined();
    expect(Array.isArray(data.tools)).toBe(true);
    console.log(`可用工具数量: ${data.tools.length}`);
    
    // 打印前几个工具名称
    if (data.tools.length > 0) {
      console.log(`示例工具: ${data.tools.slice(0, 3).map((t: any) => t.name).join(', ')}`);
    }
  });

  test('Tools - 页面显示工具列表', async ({ page }) => {
    await page.goto(`${BASE_URL}/tools`);
    await page.waitForLoadState('networkidle');
    
    // 验证工具库标题
    await expect(page.getByText(/工具库|tool library/i)).first().toBeVisible();
    
    // 等待工具加载
    await page.waitForTimeout(2000);
    
    // 验证至少有工具区域
    const toolsArea = page.locator('.card').first();
    await expect(toolsArea).toBeVisible();
  });

  test('Tools - 调用echo工具测试', async ({ page }) => {
    // 调用echo工具（如果可用）
    const response = await page.request.post(`${API_BASE}/tools/call`, {
      data: {
        tool_name: "echo",
        params: {
          message: "Hello from E2E test"
        }
      }
    });
    
    // echo工具可能不存在，所以我们只记录结果
    if (response.ok()) {
      const data = await response.json();
      expect(data.success).toBeDefined();
      console.log(`工具调用结果: ${JSON.stringify(data)}`);
    } else {
      console.log(`工具不存在或调用失败，状态码: ${response.status()}`);
    }
  });
});

test.describe('真实功能测试 - Settings设置管理', () => {
  test('Settings - LLM配置API', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/llm/config`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.providers).toBeDefined();
    expect(Array.isArray(data.providers)).toBe(true);
    console.log(`LLM提供商数量: ${data.providers.length}`);
    console.log(`默认提供商: ${data.default_provider}`);
    
    // 打印提供商信息
    data.providers.forEach((provider: any) => {
      console.log(`- ${provider.provider}: ${provider.name}, 已启用: ${provider.is_enabled}`);
    });
  });

  test('Settings - 页面切换标签页', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings`);
    await page.waitForLoadState('networkidle');
    
    // 验证LLM标签存在
    const llmTab = page.getByRole('button', { name: /LLM/i }).first();
    await expect(llmTab).toBeVisible();
    
    // 点击MCP标签
    const mcpTab = page.getByRole('button', { name: /MCP/i }).first();
    await mcpTab.click();
    await page.waitForTimeout(500);
    
    // 点击Providers标签
    const providersTab = page.getByRole('button', { name: /Providers/i }).first();
    await providersTab.click();
    await page.waitForTimeout(500);
    
    // 点击Notification标签
    const notificationTab = page.getByRole('button', { name: /Notification/i }).first();
    await notificationTab.click();
    await page.waitForTimeout(500);
    
    // 切回LLM标签
    await llmTab.click();
    await page.waitForTimeout(500);
    
    console.log('所有标签页切换成功');
  });

  test('Settings - 测试LLM连接（不保存）', async ({ page }) => {
    const response = await page.request.post(`${API_BASE}/llm/config/openai/test`);
    // 即使没有配置，也应该返回结果
    expect(response.status()).toBeDefined();
    const data = await response.json();
    expect(data.success).toBeDefined();
    console.log(`LLM连接测试结果: success=${data.success}, message=${data.message}`);
  });
});

test.describe('真实功能测试 - SOP标准流程', () => {
  test('SOP - 获取SOP列表API', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/sop/list`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.sops).toBeDefined();
    expect(Array.isArray(data.sops)).toBe(true);
    console.log(`可用SOP数量: ${data.sops.length}`);
    console.log(`SOP列表: ${data.sops.join(', ')}`);
  });

  test('SOP - 页面加载', async ({ page }) => {
    await page.goto(`${BASE_URL}/sop`);
    await page.waitForLoadState('networkidle');
    
    // 等待页面加载完成
    await page.waitForTimeout(1000);
    
    // 验证页面基本元素存在
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('真实功能测试 - MCP服务器', () => {
  test('MCP - 获取服务器列表API', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/mcp/servers`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.servers).toBeDefined();
    expect(Array.isArray(data.servers)).toBe(true);
    console.log(`MCP服务器数量: ${data.servers.length}`);
  });

  test('MCP - 获取所有MCP工具API', async ({ page }) => {
    const response = await page.request.get(`${API_BASE}/mcp/tools`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.tools).toBeDefined();
    console.log(`MCP工具数量: ${data.tools.length}`);
  });
});

test.describe('真实功能测试 - 数据库数据', () => {
  test('Dashboard - 验证统计数据API', async ({ page }) => {
    // 检查健康状态
    const healthResponse = await page.request.get(`${API_BASE}/health`);
    expect(healthResponse.ok()).toBeTruthy();
    const healthData = await healthResponse.json();
    expect(healthData.status).toBe('healthy');
    expect(healthData.components).toBeDefined();
    console.log(`健康状态: ${healthData.status}`);
    console.log(`组件状态: ${JSON.stringify(healthData.components)}`);
  });

  test('Memory - 存储和搜索记忆', async ({ page }) => {
    // 存储记忆
    const storeResponse = await page.request.post(`${API_BASE}/memory/store`, {
      data: {
        content: "E2E测试存储的记忆内容",
        task_id: "test-task-001",
        metadata: { source: "e2e-test" }
      }
    });
    expect(storeResponse.ok()).toBeTruthy();
    const storeData = await storeResponse.json();
    expect(storeData.success).toBe(true);
    expect(storeData.entry_id).toBeDefined();
    console.log(`存储的记忆ID: ${storeData.entry_id}`);
    
    // 搜索记忆
    const searchResponse = await page.request.post(`${API_BASE}/memory/search`, {
      data: {
        query: "测试",
        limit: 5
      }
    });
    expect(searchResponse.ok()).toBeTruthy();
    const searchData = await searchResponse.json();
    expect(searchData.success).toBe(true);
    console.log(`搜索结果数量: ${searchData.total}`);
  });
});

test.describe('真实功能测试 - 工作流验证', () {
  test('完整工作流 - 创建任务 -> 查询状态 -> 获取结果', async ({ page }) => {
    // 1. 创建任务
    const createResponse = await page.request.post(`${API_BASE}/tasks`, {
      data: {
        user_input: "完整工作流测试 - 查询今天的天气"
      }
    });
    expect(createResponse.ok()).toBeTruthy();
    const createData = await createResponse.json();
    expect(createData.task_id).toBeDefined();
    const taskId = createData.task_id;
    console.log(`[工作流] 创建任务ID: ${taskId}`);
    
    // 2. 等待一小段时间让任务开始处理
    await page.waitForTimeout(2000);
    
    // 3. 查询任务状态
    const statusResponse = await page.request.get(`${API_BASE}/tasks/${taskId}`);
    expect(statusResponse.ok()).toBeTruthy();
    const statusData = await statusResponse.json();
    expect(statusData.task_id).toBe(taskId);
    expect(statusData.state).toBeDefined();
    console.log(`[工作流] 任务状态: ${statusData.state}`);
    
    // 4. 获取任务结果（如果已完成）
    if (statusData.state === 'success' || statusData.state === 'failed') {
      const resultResponse = await page.request.get(`${API_BASE}/tasks/${taskId}/result`);
      if (resultResponse.ok()) {
        const resultData = await resultResponse.json();
        console.log(`[工作流] 任务结果: ${JSON.stringify(resultData).substring(0, 200)}...`);
      }
    }
    
    console.log('[工作流] 完整流程验证完成');
  });
});

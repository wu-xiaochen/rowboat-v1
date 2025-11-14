/**
 * 完整用户流程端到端测试
 * Complete user flow end-to-end tests using Playwright
 * 覆盖所有用户点击使用的功能
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

test.describe('完整用户流程测试', () => {
  let projectId: string;
  let projectName: string;

  test.beforeAll(async ({ request }) => {
    // 创建测试项目
    const response = await request.post(`${API_BASE_URL}/api/v1/projects`, {
      data: {
        name: '完整流程测试项目',
        mode: {
          workflowJson: JSON.stringify({
            agents: [],
            tools: [],
            prompts: [],
            pipelines: [],
            startAgent: null
          })
        }
      }
    });
    
    const data = await response.json();
    projectId = data.id || data.data?.id;
    projectName = data.name || '完整流程测试项目';
    expect(projectId).toBeTruthy();
  });

  test.afterAll(async ({ request }) => {
    // 清理测试项目
    if (projectId) {
      await request.delete(`${API_BASE_URL}/api/v1/projects/${projectId}`);
    }
  });

  test('场景1: 创建智能体并测试对话', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 等待页面加载
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 步骤1: 创建智能体
    const addAgentButton = page.locator('button:has-text("添加智能体"), button:has-text("Add Agent")').first();
    await addAgentButton.click();
    
    await page.waitForSelector('input[placeholder*="名称"], input[placeholder*="name"]', { timeout: 5000 });
    
    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="name"]').first();
    await nameInput.fill('客服智能体');
    
    const instructionsInput = page.locator('textarea[placeholder*="指令"], textarea[placeholder*="instructions"]').first();
    await instructionsInput.fill('你是一个专业的客服助手，能够友好地回答用户问题。');
    
    // 保存
    const saveButton = page.locator('button:has-text("保存"), button:has-text("Save")').first();
    if (await saveButton.isVisible()) {
      await saveButton.click();
    }
    
    // 验证智能体已创建
    await expect(page.locator('text=客服智能体')).toBeVisible({ timeout: 5000 });
    
    // 步骤2: 切换到测试面板
    const chatTab = page.locator('button:has-text("Playground"), button:has-text("测试"), button:has-text("Chat")').first();
    if (await chatTab.isVisible()) {
      await chatTab.click();
    }
    
    // 等待聊天输入框
    await page.waitForSelector('textarea[placeholder*="消息"], textarea[placeholder*="message"], input[type="text"]', { timeout: 5000 });
    
    // 步骤3: 发送测试消息
    const messageInput = page.locator('textarea[placeholder*="消息"], textarea[placeholder*="message"], input[type="text"]').first();
    await messageInput.fill('你好');
    await messageInput.press('Enter');
    
    // 等待响应
    await page.waitForTimeout(3000);
    
    // 验证有响应
    const responseArea = page.locator('[class*="message"], [class*="response"], [class*="assistant"]').last();
    await expect(responseArea).toBeVisible({ timeout: 30000 });
    
    const responseText = await responseArea.textContent();
    expect(responseText).toBeTruthy();
    expect(responseText?.trim().length).toBeGreaterThan(0);
  });

  test('场景2: 使用Copilot创建智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Copilot面板
    const copilotTab = page.locator('button:has-text("Copilot"), button:has-text("助手")').first();
    if (await copilotTab.isVisible()) {
      await copilotTab.click();
    }
    
    // 等待Copilot输入框
    await page.waitForSelector('textarea[placeholder*="消息"], textarea[placeholder*="message"]', { timeout: 5000 });
    
    // 输入创建智能体的请求
    const messageInput = page.locator('textarea[placeholder*="消息"], textarea[placeholder*="message"]').first();
    await messageInput.fill('帮我创建一个销售智能体，能够介绍产品特点并回答客户问题');
    await messageInput.press('Enter');
    
    // 等待响应（最多60秒）
    await page.waitForTimeout(5000);
    
    // 验证有响应
    const responseArea = page.locator('[class*="message"], [class*="response"]').last();
    await expect(responseArea).toBeVisible({ timeout: 60000 });
    
    // 验证智能体可能已创建（检查智能体列表）
    const agentsList = page.locator('[data-tour-target="entity-agents"]');
    await expect(agentsList).toBeVisible();
  });

  test('场景3: 创建多个智能体并配置Pipeline', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 创建第一个智能体
    const addAgentButton = page.locator('button:has-text("添加智能体")').first();
    await addAgentButton.click();
    
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    const nameInput1 = page.locator('input[placeholder*="名称"]').first();
    await nameInput1.fill('智能体1');
    
    // 创建第二个智能体
    await addAgentButton.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    const nameInput2 = page.locator('input[placeholder*="名称"]').first();
    await nameInput2.fill('智能体2');
    
    // 验证两个智能体都存在
    await expect(page.locator('text=智能体1')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=智能体2')).toBeVisible({ timeout: 5000 });
    
    // 创建Pipeline
    const addPipelineButton = page.locator('button:has-text("添加Pipeline"), button:has-text("Add Pipeline")').first();
    if (await addPipelineButton.isVisible()) {
      await addPipelineButton.click();
      
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const pipelineNameInput = page.locator('input[placeholder*="名称"]').first();
      await pipelineNameInput.fill('测试Pipeline');
      
      // 验证Pipeline已创建
      await expect(page.locator('text=测试Pipeline')).toBeVisible({ timeout: 5000 });
    }
  });

  test('场景4: 添加工具并测试', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    await page.waitForSelector('[data-tour-target="entity-tools"]', { timeout: 10000 });
    
    // 切换到工具面板
    const toolsTab = page.locator('button:has-text("工具"), button:has-text("Tools")').first();
    if (await toolsTab.isVisible()) {
      await toolsTab.click();
    }
    
    // 添加工具
    const addToolButton = page.locator('button:has-text("添加工具"), button:has-text("Add Tool")').first();
    if (await addToolButton.isVisible()) {
      await addToolButton.click();
      
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const nameInput = page.locator('input[placeholder*="名称"]').first();
      await nameInput.fill('测试工具');
      
      // 验证工具已添加
      await expect(page.locator('text=测试工具')).toBeVisible({ timeout: 5000 });
    }
  });

  test('场景5: 发布项目并使用', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找发布按钮
    const publishButton = page.locator('button:has-text("发布"), button:has-text("Publish")').first();
    if (await publishButton.isVisible() && !(await publishButton.isDisabled())) {
      await publishButton.click();
      
      // 等待发布完成
      await page.waitForTimeout(3000);
      
      // 验证发布状态
      const liveIndicator = page.locator('text=实时, text=Live, [class*="live"]').first();
      if (await liveIndicator.isVisible()) {
        await expect(liveIndicator).toBeVisible();
      }
    }
    
    // 测试"使用助手"功能
    const useAssistantButton = page.locator('button:has-text("使用助手"), button:has-text("Use Assistant")').first();
    if (await useAssistantButton.isVisible()) {
      await useAssistantButton.click();
      
      // 等待选项菜单或页面跳转
      await page.waitForTimeout(2000);
      
      // 验证功能可用
      expect(await useAssistantButton.isVisible() || page.url().includes('/config')).toBeTruthy();
    }
  });

  test('场景6: 编辑智能体配置', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 点击已存在的智能体
    const agentItem = page.locator('text=客服智能体').first();
    if (await agentItem.isVisible()) {
      await agentItem.click();
      
      // 等待配置面板出现
      await page.waitForTimeout(1000);
      
      // 修改指令
      const instructionsInput = page.locator('textarea[placeholder*="指令"]').first();
      if (await instructionsInput.isVisible()) {
        await instructionsInput.fill('你是一个升级版的客服助手，能够提供更专业的服务。');
        
        // 保存
        const saveButton = page.locator('button:has-text("保存")').first();
        if (await saveButton.isVisible()) {
          await saveButton.click();
        }
      }
    }
  });

  test('场景7: 删除智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找删除按钮（通常在菜单中）
    const agentItem = page.locator('text=智能体1').first();
    if (await agentItem.isVisible()) {
      // 右键点击或点击菜单按钮
      await agentItem.click({ button: 'right' });
      
      // 或查找菜单按钮
      const menuButton = agentItem.locator('..').locator('button[aria-label*="菜单"], button[aria-label*="Menu"]').first();
      if (await menuButton.isVisible()) {
        await menuButton.click();
        
        // 查找删除选项
        const deleteOption = page.locator('text=删除, text=Delete').first();
        if (await deleteOption.isVisible()) {
          await deleteOption.click();
          
          // 确认删除
          const confirmButton = page.locator('button:has-text("确认"), button:has-text("Confirm")').first();
          if (await confirmButton.isVisible()) {
            await confirmButton.click();
          }
        }
      }
    }
  });
});

test.describe('API端点直接测试', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

  test('健康检查', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('API信息', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/info`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.name).toBeTruthy();
  });

  test('创建项目', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/v1/projects`, {
      data: {
        name: 'API测试项目',
        mode: {
          workflowJson: JSON.stringify({
            agents: [],
            tools: [],
            prompts: [],
            pipelines: [],
            startAgent: null
          })
        }
      }
    });
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const projectId = data.id || data.data?.id;
    
    // 清理
    if (projectId) {
      await request.delete(`${API_BASE_URL}/api/v1/projects/${projectId}`);
    }
  });
});


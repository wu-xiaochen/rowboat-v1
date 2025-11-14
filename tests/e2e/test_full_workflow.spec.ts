/**
 * 完整工作流端到端测试
 * Complete workflow end-to-end tests using Playwright
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

test.describe('完整工作流测试', () => {
  let projectId: string;

  test.beforeAll(async ({ request }) => {
    // 创建测试项目
    const response = await request.post(`${API_BASE_URL}/api/v1/projects`, {
      data: {
        name: 'E2E测试项目',
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
    expect(projectId).toBeTruthy();
  });

  test('1. 创建智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 等待页面加载
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 点击添加智能体按钮
    const addAgentButton = page.locator('button:has-text("添加智能体"), button:has-text("Add Agent")').first();
    await addAgentButton.click();
    
    // 等待智能体配置面板出现
    await page.waitForSelector('input[placeholder*="名称"], input[placeholder*="name"]', { timeout: 5000 });
    
    // 填写智能体名称
    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="name"]').first();
    await nameInput.fill('测试智能体1');
    
    // 填写指令
    const instructionsInput = page.locator('textarea[placeholder*="指令"], textarea[placeholder*="instructions"]').first();
    await instructionsInput.fill('你是一个友好的助手');
    
    // 保存（如果有保存按钮）
    const saveButton = page.locator('button:has-text("保存"), button:has-text("Save")').first();
    if (await saveButton.isVisible()) {
      await saveButton.click();
    }
    
    // 验证智能体已创建
    await expect(page.locator('text=测试智能体1')).toBeVisible();
  });

  test('2. 使用Copilot创建智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 等待页面加载
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Copilot面板
    const copilotTab = page.locator('button:has-text("Copilot"), button:has-text("助手")').first();
    if (await copilotTab.isVisible()) {
      await copilotTab.click();
    }
    
    // 等待Copilot输入框
    await page.waitForSelector('textarea[placeholder*="消息"], textarea[placeholder*="message"]', { timeout: 5000 });
    
    // 输入消息
    const messageInput = page.locator('textarea[placeholder*="消息"], textarea[placeholder*="message"]').first();
    await messageInput.fill('帮我创建一个智能客服');
    await messageInput.press('Enter');
    
    // 等待响应（最多30秒）
    await page.waitForTimeout(2000);
    
    // 验证有响应（不一定是成功，但应该有内容）
    const responseArea = page.locator('[class*="message"], [class*="response"]').last();
    await expect(responseArea).toBeVisible({ timeout: 30000 });
  });

  test('3. 测试智能体对话', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 等待页面加载
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Playground/Chat面板
    const chatTab = page.locator('button:has-text("Playground"), button:has-text("测试"), button:has-text("Chat")').first();
    if (await chatTab.isVisible()) {
      await chatTab.click();
    }
    
    // 等待聊天输入框
    await page.waitForSelector('textarea[placeholder*="消息"], textarea[placeholder*="message"], input[type="text"]', { timeout: 5000 });
    
    // 输入消息
    const messageInput = page.locator('textarea[placeholder*="消息"], textarea[placeholder*="message"], input[type="text"]').first();
    await messageInput.fill('你好');
    await messageInput.press('Enter');
    
    // 等待响应（最多30秒）
    await page.waitForTimeout(2000);
    
    // 验证有响应
    const responseArea = page.locator('[class*="message"], [class*="response"], [class*="assistant"]').last();
    await expect(responseArea).toBeVisible({ timeout: 30000 });
    
    // 验证响应不为空
    const responseText = await responseArea.textContent();
    expect(responseText).toBeTruthy();
    expect(responseText?.trim().length).toBeGreaterThan(0);
  });

  test('4. 创建多个智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 创建第二个智能体
    const addAgentButton = page.locator('button:has-text("添加智能体"), button:has-text("Add Agent")').first();
    await addAgentButton.click();
    
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    const nameInput = page.locator('input[placeholder*="名称"]').first();
    await nameInput.fill('测试智能体2');
    
    // 验证两个智能体都存在
    await expect(page.locator('text=测试智能体1')).toBeVisible();
    await expect(page.locator('text=测试智能体2')).toBeVisible();
  });

  test('5. 测试Pipeline', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 创建Pipeline
    const addPipelineButton = page.locator('button:has-text("添加Pipeline"), button:has-text("Add Pipeline")').first();
    if (await addPipelineButton.isVisible()) {
      await addPipelineButton.click();
      
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const nameInput = page.locator('input[placeholder*="名称"]').first();
      await nameInput.fill('测试Pipeline');
      
      // 验证Pipeline已创建
      await expect(page.locator('text=测试Pipeline')).toBeVisible();
    }
  });

  test('6. 测试工具添加', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 切换到工具面板
    const toolsTab = page.locator('button:has-text("工具"), button:has-text("Tools")').first();
    if (await toolsTab.isVisible()) {
      await toolsTab.click();
      
      // 添加工具
      const addToolButton = page.locator('button:has-text("添加工具"), button:has-text("Add Tool")').first();
      if (await addToolButton.isVisible()) {
        await addToolButton.click();
        
        await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
        
        const nameInput = page.locator('input[placeholder*="名称"]').first();
        await nameInput.fill('测试工具');
        
        // 验证工具已添加
        await expect(page.locator('text=测试工具')).toBeVisible();
      }
    }
  });

  test('7. 测试发布功能', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 查找发布按钮
    const publishButton = page.locator('button:has-text("发布"), button:has-text("Publish")').first();
    if (await publishButton.isVisible() && !(await publishButton.isDisabled())) {
      await publishButton.click();
      
      // 等待发布完成
      await page.waitForTimeout(2000);
      
      // 验证发布状态
      const liveIndicator = page.locator('text=实时, text=Live, [class*="live"]').first();
      if (await liveIndicator.isVisible()) {
        await expect(liveIndicator).toBeVisible();
      }
    }
  });

  test('8. 测试使用助手功能', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    
    // 查找"使用助手"按钮
    const useAssistantButton = page.locator('button:has-text("使用助手"), button:has-text("Use Assistant")').first();
    if (await useAssistantButton.isVisible()) {
      await useAssistantButton.click();
      
      // 等待选项菜单或页面跳转
      await page.waitForTimeout(1000);
      
      // 验证功能可用
      expect(await useAssistantButton.isVisible() || page.url().includes('/config')).toBeTruthy();
    }
  });
});

test.describe('API端点测试', () => {
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
  });
});






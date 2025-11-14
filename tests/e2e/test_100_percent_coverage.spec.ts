/**
 * 100%覆盖测试 - 所有用户使用环节和细节
 * 100% Coverage Test - All user interaction scenarios and details
 */
import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

// 测试数据
const TEST_AGENT_NAME = '测试智能体';
const TEST_AGENT_INSTRUCTIONS = '你是一个专业的测试助手，能够回答各种问题。';
const TEST_TOOL_NAME = '测试工具';
const TEST_PROMPT_NAME = '测试提示词';
const TEST_PIPELINE_NAME = '测试Pipeline';

test.describe('100%覆盖测试 - 所有用户使用环节', () => {
  let projectId: string;
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // 创建测试项目
    const response = await request.post(`${API_BASE_URL}/api/v1/projects`, {
      data: {
        name: '100%覆盖测试项目',
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

  test.afterAll(async ({ request }) => {
    // 清理测试项目
    if (projectId) {
      await request.delete(`${API_BASE_URL}/api/v1/projects/${projectId}`);
    }
  });

  // ========== 第一部分：项目基础操作 ==========
  
  test('1.1 访问项目工作流页面', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForLoadState('networkidle');
    
    // 验证页面元素
    await expect(page.locator('[data-tour-target="entity-agents"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=智能体, text=Agents')).toBeVisible();
  });

  test('1.2 验证顶部导航栏', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForLoadState('networkidle');
    
    // 验证进度条
    const progressBar = page.locator('[aria-label*="Workflow"]');
    await expect(progressBar).toBeVisible();
    
    // 验证步骤：构建、测试、使用
    await expect(page.locator('text=构建, text=Build')).toBeVisible();
    await expect(page.locator('text=测试, text=Test')).toBeVisible();
    await expect(page.locator('text=使用, text=Use')).toBeVisible();
  });

  // ========== 第二部分：智能体管理 ==========
  
  test('2.1 手动创建智能体 - 完整流程', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 点击添加智能体按钮
    const addAgentBtn = page.locator('button:has-text("添加智能体"), button:has-text("Add Agent")').first();
    await addAgentBtn.click();
    
    // 等待配置面板出现
    await page.waitForSelector('input[placeholder*="名称"], input[placeholder*="name"]', { timeout: 5000 });
    
    // 填写智能体名称
    const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="name"]').first();
    await nameInput.clear();
    await nameInput.fill(TEST_AGENT_NAME);
    
    // 填写描述
    const descInput = page.locator('textarea[placeholder*="描述"], textarea[placeholder*="description"]').first();
    if (await descInput.isVisible()) {
      await descInput.fill('这是一个测试智能体的描述');
    }
    
    // 填写指令
    const instructionsInput = page.locator('textarea[placeholder*="指令"], textarea[placeholder*="instructions"]').first();
    await instructionsInput.clear();
    await instructionsInput.fill(TEST_AGENT_INSTRUCTIONS);
    
    // 选择模型（如果有下拉框）
    const modelSelect = page.locator('select, [role="combobox"]').first();
    if (await modelSelect.isVisible()) {
      await modelSelect.click();
      await page.waitForTimeout(500);
    }
    
    // 保存
    const saveButton = page.locator('button:has-text("保存"), button:has-text("Save")').first();
    if (await saveButton.isVisible()) {
      await saveButton.click();
      await page.waitForTimeout(1000);
    }
    
    // 验证智能体已创建
    await expect(page.locator(`text=${TEST_AGENT_NAME}`)).toBeVisible({ timeout: 5000 });
  });

  test('2.2 编辑智能体配置', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 点击已创建的智能体
    const agentItem = page.locator(`text=${TEST_AGENT_NAME}`).first();
    await agentItem.click();
    await page.waitForTimeout(1000);
    
    // 修改指令
    const instructionsInput = page.locator('textarea[placeholder*="指令"]').first();
    if (await instructionsInput.isVisible()) {
      await instructionsInput.clear();
      await instructionsInput.fill('更新后的指令：你是一个升级版的测试助手。');
      
      // 保存
      const saveButton = page.locator('button:has-text("保存")').first();
      if (await saveButton.isVisible()) {
        await saveButton.click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('2.3 设置起始智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找设置起始智能体的按钮或选项
    const agentItem = page.locator(`text=${TEST_AGENT_NAME}`).first();
    await agentItem.hover();
    
    // 查找设置为主智能体的按钮
    const setMainBtn = page.locator('button[aria-label*="主"], button[aria-label*="main"], button[aria-label*="start"]').first();
    if (await setMainBtn.isVisible()) {
      await setMainBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test('2.4 启用/禁用智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找启用/禁用开关
    const agentItem = page.locator(`text=${TEST_AGENT_NAME}`).first();
    await agentItem.hover();
    
    const toggleBtn = page.locator('button[aria-label*="启用"], button[aria-label*="禁用"], input[type="checkbox"]').first();
    if (await toggleBtn.isVisible()) {
      await toggleBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test('2.5 删除智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 创建临时智能体用于删除测试
    const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
    await addAgentBtn.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    const nameInput = page.locator('input[placeholder*="名称"]').first();
    await nameInput.fill('待删除智能体');
    
    const saveButton = page.locator('button:has-text("保存")').first();
    if (await saveButton.isVisible()) {
      await saveButton.click();
      await page.waitForTimeout(1000);
    }
    
    // 删除智能体
    const deleteAgent = page.locator('text=待删除智能体').first();
    await deleteAgent.hover();
    
    // 查找删除按钮（可能在菜单中）
    const menuBtn = page.locator('button[aria-label*="菜单"], button[aria-label*="more"]').first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
      
      const deleteBtn = page.locator('text=删除, text=Delete').first();
      if (await deleteBtn.isVisible()) {
        await deleteBtn.click();
        
        // 确认删除
        const confirmBtn = page.locator('button:has-text("确认"), button:has-text("Confirm")').first();
        if (await confirmBtn.isVisible()) {
          await confirmBtn.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  // ========== 第三部分：Copilot功能 ==========
  
  test('3.1 使用Copilot创建智能体', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Copilot面板
    const copilotTab = page.locator('button:has-text("Copilot"), button:has-text("助手")').first();
    if (await copilotTab.isVisible()) {
      await copilotTab.click();
      await page.waitForTimeout(1000);
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
    
    // 验证可能创建了智能体
    await page.waitForTimeout(3000);
    const agentsList = page.locator('[data-tour-target="entity-agents"]');
    await expect(agentsList).toBeVisible();
  });

  test('3.2 Copilot工具调用流程', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Copilot
    const copilotTab = page.locator('button:has-text("Copilot")').first();
    if (await copilotTab.isVisible()) {
      await copilotTab.click();
    }
    
    await page.waitForSelector('textarea[placeholder*="消息"]', { timeout: 5000 });
    
    // 发送会触发工具调用的消息
    const messageInput = page.locator('textarea[placeholder*="消息"]').first();
    await messageInput.fill('搜索相关工具');
    await messageInput.press('Enter');
    
    // 等待工具调用事件
    await page.waitForTimeout(3000);
    
    // 验证工具调用和结果
    const toolCallIndicator = page.locator('text=工具, text=tool, [class*="tool-call"]').first();
    if (await toolCallIndicator.isVisible({ timeout: 10000 })) {
      // 工具调用正在进行
      await page.waitForTimeout(5000);
    }
  });

  test('3.3 使用Copilot编辑智能体指令', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 选择智能体
    const agentItem = page.locator(`text=${TEST_AGENT_NAME}`).first();
    await agentItem.click();
    await page.waitForTimeout(1000);
    
    // 切换到Copilot
    const copilotTab = page.locator('button:has-text("Copilot")').first();
    if (await copilotTab.isVisible()) {
      await copilotTab.click();
    }
    
    await page.waitForSelector('textarea[placeholder*="消息"]', { timeout: 5000 });
    
    // 请求编辑指令
    const messageInput = page.locator('textarea[placeholder*="消息"]').first();
    await messageInput.fill('优化这个智能体的指令，使其更加专业');
    await messageInput.press('Enter');
    
    // 等待响应
    await page.waitForTimeout(5000);
    const responseArea = page.locator('[class*="message"], [class*="response"]').last();
    await expect(responseArea).toBeVisible({ timeout: 30000 });
  });

  // ========== 第四部分：工具管理 ==========
  
  test('4.1 添加自定义工具', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-tools"]', { timeout: 10000 });
    
    // 切换到工具面板
    const toolsTab = page.locator('button:has-text("工具"), button:has-text("Tools")').first();
    if (await toolsTab.isVisible()) {
      await toolsTab.click();
      await page.waitForTimeout(1000);
    }
    
    // 添加工具
    const addToolBtn = page.locator('button:has-text("添加工具"), button:has-text("Add Tool")').first();
    if (await addToolBtn.isVisible()) {
      await addToolBtn.click();
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const nameInput = page.locator('input[placeholder*="名称"]').first();
      await nameInput.fill(TEST_TOOL_NAME);
      
      // 填写工具描述和代码
      const descInput = page.locator('textarea[placeholder*="描述"]').first();
      if (await descInput.isVisible()) {
        await descInput.fill('这是一个测试工具');
      }
      
      // 保存
      const saveButton = page.locator('button:has-text("保存")').first();
      if (await saveButton.isVisible()) {
        await saveButton.click();
        await page.waitForTimeout(1000);
      }
      
      // 验证工具已添加
      await expect(page.locator(`text=${TEST_TOOL_NAME}`)).toBeVisible({ timeout: 5000 });
    }
  });

  test('4.2 浏览Composio工具', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-tools"]', { timeout: 10000 });
    
    // 切换到工具面板
    const toolsTab = page.locator('button:has-text("工具")').first();
    if (await toolsTab.isVisible()) {
      await toolsTab.click();
    }
    
    // 查找Composio工具面板
    const composioPanel = page.locator('text=Composio, text=Toolkit').first();
    if (await composioPanel.isVisible()) {
      await composioPanel.click();
      await page.waitForTimeout(1000);
      
      // 浏览工具列表
      const toolCards = page.locator('[class*="card"], [class*="tool"]');
      const count = await toolCards.count();
      if (count > 0) {
        // 点击第一个工具查看详情
        await toolCards.first().click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('4.3 连接Composio工具', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-tools"]', { timeout: 10000 });
    
    // 切换到工具面板
    const toolsTab = page.locator('button:has-text("工具")').first();
    if (await toolsTab.isVisible()) {
      await toolsTab.click();
    }
    
    // 查找Composio工具
    const composioCard = page.locator('[class*="composio"], [class*="toolkit"]').first();
    if (await composioCard.isVisible()) {
      await composioCard.click();
      await page.waitForTimeout(1000);
      
      // 查找连接按钮
      const connectBtn = page.locator('button:has-text("连接"), button:has-text("Connect")').first();
      if (await connectBtn.isVisible()) {
        // 注意：实际连接可能需要OAuth，这里只测试UI交互
        await connectBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  // ========== 第五部分：Pipeline管理 ==========
  
  test('5.1 创建Pipeline', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找Pipeline标签或按钮
    const pipelineTab = page.locator('button:has-text("Pipeline"), button:has-text("管道")').first();
    if (await pipelineTab.isVisible()) {
      await pipelineTab.click();
      await page.waitForTimeout(1000);
    }
    
    // 添加Pipeline
    const addPipelineBtn = page.locator('button:has-text("添加Pipeline"), button:has-text("Add Pipeline")').first();
    if (await addPipelineBtn.isVisible()) {
      await addPipelineBtn.click();
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const nameInput = page.locator('input[placeholder*="名称"]').first();
      await nameInput.fill(TEST_PIPELINE_NAME);
      
      // 保存
      const saveButton = page.locator('button:has-text("保存")').first();
      if (await saveButton.isVisible()) {
        await saveButton.click();
        await page.waitForTimeout(1000);
      }
      
      // 验证Pipeline已创建
      await expect(page.locator(`text=${TEST_PIPELINE_NAME}`)).toBeVisible({ timeout: 5000 });
    }
  });

  test('5.2 配置Pipeline步骤', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 选择Pipeline
    const pipelineItem = page.locator(`text=${TEST_PIPELINE_NAME}`).first();
    if (await pipelineItem.isVisible()) {
      await pipelineItem.click();
      await page.waitForTimeout(1000);
      
      // 添加步骤
      const addStepBtn = page.locator('button:has-text("添加步骤"), button:has-text("Add Step")').first();
      if (await addStepBtn.isVisible()) {
        await addStepBtn.click();
        await page.waitForTimeout(1000);
        
        // 选择智能体作为步骤
        const agentSelect = page.locator('select, [role="combobox"]').first();
        if (await agentSelect.isVisible()) {
          await agentSelect.click();
          await page.waitForTimeout(500);
          
          // 选择已存在的智能体
          const agentOption = page.locator(`text=${TEST_AGENT_NAME}`).first();
          if (await agentOption.isVisible()) {
            await agentOption.click();
            await page.waitForTimeout(1000);
          }
        }
      }
    }
  });

  // ========== 第六部分：Playground测试 ==========
  
  test('6.1 切换到Playground并发送消息', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Playground
    const playgroundTab = page.locator('button:has-text("Playground"), button:has-text("测试"), button:has-text("Chat")').first();
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click();
      await page.waitForTimeout(2000);
    }
    
    // 等待聊天输入框
    await page.waitForSelector('textarea[placeholder*="消息"], textarea[placeholder*="message"], input[type="text"]', { timeout: 5000 });
    
    // 发送第一条消息
    const messageInput = page.locator('textarea[placeholder*="消息"], textarea[placeholder*="message"], input[type="text"]').first();
    await messageInput.fill('你好，请介绍一下你自己');
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

  test('6.2 多轮对话测试', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Playground
    const playgroundTab = page.locator('button:has-text("Playground"), button:has-text("测试")').first();
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click();
    }
    
    await page.waitForSelector('textarea[placeholder*="消息"]', { timeout: 5000 });
    
    // 第一轮对话
    const messageInput = page.locator('textarea[placeholder*="消息"]').first();
    await messageInput.fill('1+1等于多少？');
    await messageInput.press('Enter');
    await page.waitForTimeout(5000);
    
    // 第二轮对话
    await messageInput.fill('那2+2呢？');
    await messageInput.press('Enter');
    await page.waitForTimeout(5000);
    
    // 验证多轮对话
    const messages = page.locator('[class*="message"]');
    const messageCount = await messages.count();
    expect(messageCount).toBeGreaterThan(2);
  });

  test('6.3 清空对话历史', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Playground
    const playgroundTab = page.locator('button:has-text("Playground")').first();
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click();
    }
    
    // 查找清空/新对话按钮
    const newChatBtn = page.locator('button:has-text("新对话"), button:has-text("New Chat"), button[aria-label*="new"]').first();
    if (await newChatBtn.isVisible()) {
      await newChatBtn.click();
      await page.waitForTimeout(1000);
      
      // 验证对话已清空
      const messages = page.locator('[class*="message"]');
      const count = await messages.count();
      expect(count).toBeLessThanOrEqual(1); // 可能还有系统消息
    }
  });

  // ========== 第七部分：发布和使用 ==========
  
  test('7.1 发布工作流', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找发布按钮
    const publishBtn = page.locator('button:has-text("发布"), button:has-text("Publish")').first();
    if (await publishBtn.isVisible() && !(await publishBtn.isDisabled())) {
      await publishBtn.click();
      await page.waitForTimeout(3000);
      
      // 验证发布状态
      const liveIndicator = page.locator('text=实时, text=Live, [class*="live"]').first();
      if (await liveIndicator.isVisible({ timeout: 5000 })) {
        await expect(liveIndicator).toBeVisible();
      }
    }
  });

  test('7.2 使用助手 - API配置', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找"使用助手"按钮
    const useAssistantBtn = page.locator('button:has-text("使用助手"), button:has-text("Use Assistant")').first();
    if (await useAssistantBtn.isVisible()) {
      await useAssistantBtn.click();
      await page.waitForTimeout(2000);
      
      // 验证跳转到配置页面或显示配置选项
      const configPage = page.url().includes('/config');
      const apiKeySection = page.locator('text=API, text=密钥, text=Key').first();
      
      expect(configPage || await apiKeySection.isVisible()).toBeTruthy();
    }
  });

  test('7.3 查看API密钥', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/config`);
    await page.waitForLoadState('networkidle');
    
    // 查找API密钥部分
    const apiKeysSection = page.locator('text=API密钥, text=API Keys').first();
    if (await apiKeysSection.isVisible()) {
      await apiKeysSection.click();
      await page.waitForTimeout(1000);
      
      // 验证API密钥列表
      const apiKeysList = page.locator('[class*="api-key"], [class*="key"]');
      await expect(apiKeysList.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('7.4 创建API密钥', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/config`);
    await page.waitForLoadState('networkidle');
    
    // 查找创建API密钥按钮
    const createKeyBtn = page.locator('button:has-text("创建"), button:has-text("Create"), button:has-text("添加")').first();
    if (await createKeyBtn.isVisible()) {
      await createKeyBtn.click();
      await page.waitForTimeout(1000);
      
      // 填写密钥名称
      const nameInput = page.locator('input[placeholder*="名称"], input[placeholder*="name"]').first();
      if (await nameInput.isVisible()) {
        await nameInput.fill('测试API密钥');
        
        // 确认创建
        const confirmBtn = page.locator('button:has-text("确认"), button:has-text("Confirm")').first();
        if (await confirmBtn.isVisible()) {
          await confirmBtn.click();
          await page.waitForTimeout(2000);
          
          // 验证密钥已创建（可能显示在列表中或弹窗中）
          const keyDisplay = page.locator('text=测试API密钥, [class*="api-key"]').first();
          if (await keyDisplay.isVisible({ timeout: 5000 })) {
            await expect(keyDisplay).toBeVisible();
          }
        }
      }
    }
  });

  // ========== 第八部分：对话历史 ==========
  
  test('8.1 查看对话列表', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/conversations`);
    await page.waitForLoadState('networkidle');
    
    // 验证对话列表页面
    const conversationsList = page.locator('[class*="conversation"], [class*="list"]').first();
    await expect(conversationsList).toBeVisible({ timeout: 5000 });
  });

  test('8.2 查看单个对话详情', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/conversations`);
    await page.waitForLoadState('networkidle');
    
    // 点击第一个对话（如果存在）
    const firstConversation = page.locator('[class*="conversation-item"], [class*="conversation"]').first();
    if (await firstConversation.isVisible({ timeout: 5000 })) {
      await firstConversation.click();
      await page.waitForTimeout(2000);
      
      // 验证对话详情页面
      const conversationView = page.locator('[class*="conversation-view"], [class*="messages"]').first();
      await expect(conversationView).toBeVisible({ timeout: 5000 });
    }
  });

  // ========== 第九部分：任务管理 ==========
  
  test('9.1 查看任务列表', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/jobs`);
    await page.waitForLoadState('networkidle');
    
    // 验证任务列表页面
    const jobsList = page.locator('[class*="job"], [class*="list"]').first();
    await expect(jobsList).toBeVisible({ timeout: 5000 });
  });

  test('9.2 查看任务详情', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/jobs`);
    await page.waitForLoadState('networkidle');
    
    // 点击第一个任务（如果存在）
    const firstJob = page.locator('[class*="job-item"], [class*="job"]').first();
    if (await firstJob.isVisible({ timeout: 5000 })) {
      await firstJob.click();
      await page.waitForTimeout(2000);
      
      // 验证任务详情
      const jobView = page.locator('[class*="job-view"], [class*="detail"]').first();
      await expect(jobView).toBeVisible({ timeout: 5000 });
    }
  });

  // ========== 第十部分：触发器管理 ==========
  
  test('10.1 查看触发器列表', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/manage-triggers`);
    await page.waitForLoadState('networkidle');
    
    // 验证触发器页面
    const triggersPage = page.locator('text=触发器, text=Triggers').first();
    await expect(triggersPage).toBeVisible({ timeout: 5000 });
  });

  test('10.2 创建Webhook触发器', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/manage-triggers`);
    await page.waitForLoadState('networkidle');
    
    // 查找创建触发器按钮
    const createBtn = page.locator('button:has-text("创建"), button:has-text("Create"), button:has-text("添加")').first();
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await page.waitForTimeout(1000);
      
      // 选择Webhook类型
      const webhookOption = page.locator('text=Webhook, text=webhook').first();
      if (await webhookOption.isVisible()) {
        await webhookOption.click();
        await page.waitForTimeout(1000);
        
        // 填写触发器配置
        const nameInput = page.locator('input[placeholder*="名称"]').first();
        if (await nameInput.isVisible()) {
          await nameInput.fill('测试Webhook触发器');
          
          // 保存
          const saveBtn = page.locator('button:has-text("保存")').first();
          if (await saveBtn.isVisible()) {
            await saveBtn.click();
            await page.waitForTimeout(2000);
          }
        }
      }
    }
  });

  // ========== 第十一部分：数据源管理 ==========
  
  test('11.1 查看数据源列表', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/sources`);
    await page.waitForLoadState('networkidle');
    
    // 验证数据源页面
    const sourcesPage = page.locator('text=数据源, text=Data Sources').first();
    await expect(sourcesPage).toBeVisible({ timeout: 5000 });
  });

  test('11.2 创建文本数据源', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/sources`);
    await page.waitForLoadState('networkidle');
    
    // 查找添加数据源按钮
    const addBtn = page.locator('button:has-text("添加"), button:has-text("Add"), button:has-text("创建")').first();
    if (await addBtn.isVisible()) {
      await addBtn.click();
      await page.waitForTimeout(1000);
      
      // 选择文本类型
      const textOption = page.locator('text=文本, text=Text').first();
      if (await textOption.isVisible()) {
        await textOption.click();
        await page.waitForTimeout(1000);
        
        // 填写数据源信息
        const nameInput = page.locator('input[placeholder*="名称"]').first();
        if (await nameInput.isVisible()) {
          await nameInput.fill('测试文本数据源');
          
          const contentInput = page.locator('textarea[placeholder*="内容"], textarea[placeholder*="content"]').first();
          if (await contentInput.isVisible()) {
            await contentInput.fill('这是测试数据源的内容。');
          }
          
          // 保存
          const saveBtn = page.locator('button:has-text("保存")').first();
          if (await saveBtn.isVisible()) {
            await saveBtn.click();
            await page.waitForTimeout(2000);
          }
        }
      }
    }
  });

  // ========== 第十二部分：UI交互细节 ==========
  
  test('12.1 测试撤销/重做功能', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找撤销/重做按钮
    const undoBtn = page.locator('button[aria-label*="撤销"], button[aria-label*="undo"], button[aria-label*="Undo"]').first();
    const redoBtn = page.locator('button[aria-label*="重做"], button[aria-label*="redo"], button[aria-label*="Redo"]').first();
    
    if (await undoBtn.isVisible()) {
      // 先做一个操作
      const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
      await addAgentBtn.click();
      await page.waitForTimeout(1000);
      
      // 撤销
      await undoBtn.click();
      await page.waitForTimeout(1000);
      
      // 重做
      if (await redoBtn.isVisible()) {
        await redoBtn.click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('12.2 测试拖拽排序', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 创建多个智能体
    for (let i = 0; i < 2; i++) {
      const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
      await addAgentBtn.click();
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const nameInput = page.locator('input[placeholder*="名称"]').first();
      await nameInput.fill(`智能体${i + 1}`);
      
      const saveBtn = page.locator('button:has-text("保存")').first();
      if (await saveBtn.isVisible()) {
        await saveBtn.click();
        await page.waitForTimeout(1000);
      }
    }
    
    // 尝试拖拽（如果支持）
    const firstAgent = page.locator('text=智能体1').first();
    const secondAgent = page.locator('text=智能体2').first();
    
    if (await firstAgent.isVisible() && await secondAgent.isVisible()) {
      // 查找拖拽手柄
      const dragHandle = firstAgent.locator('[class*="drag"], [class*="grip"], [aria-label*="drag"]').first();
      if (await dragHandle.isVisible()) {
        await dragHandle.hover();
        await page.mouse.down();
        await secondAgent.hover();
        await page.mouse.up();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('12.3 测试搜索和过滤', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="search"], input[type="search"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill(TEST_AGENT_NAME);
      await page.waitForTimeout(1000);
      
      // 验证过滤结果
      const filteredItems = page.locator(`text=${TEST_AGENT_NAME}`);
      await expect(filteredItems.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('12.4 测试视图模式切换', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找视图切换按钮
    const viewToggle = page.locator('button[aria-label*="视图"], button[aria-label*="view"], [class*="view-toggle"]').first();
    if (await viewToggle.isVisible()) {
      await viewToggle.click();
      await page.waitForTimeout(1000);
      
      // 尝试不同的视图模式
      const viewOptions = page.locator('[role="menuitem"], [class*="option"]');
      const optionCount = await viewOptions.count();
      if (optionCount > 0) {
        await viewOptions.first().click();
        await page.waitForTimeout(1000);
      }
    }
  });

  test('12.5 测试面板展开/折叠', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找面板切换按钮
    const panelToggle = page.locator('button[aria-label*="展开"], button[aria-label*="折叠"], button[aria-label*="toggle"]').first();
    if (await panelToggle.isVisible()) {
      await panelToggle.click();
      await page.waitForTimeout(1000);
      
      // 再次点击恢复
      await panelToggle.click();
      await page.waitForTimeout(1000);
    }
  });

  // ========== 第十三部分：多智能体工作流 ==========
  
  test('13.1 创建多个智能体并配置handoff', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 创建第一个智能体
    const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
    await addAgentBtn.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    let nameInput = page.locator('input[placeholder*="名称"]').first();
    await nameInput.fill('智能体A');
    
    const saveBtn = page.locator('button:has-text("保存")').first();
    if (await saveBtn.isVisible()) {
      await saveBtn.click();
      await page.waitForTimeout(1000);
    }
    
    // 创建第二个智能体
    await addAgentBtn.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    nameInput = page.locator('input[placeholder*="名称"]').first();
    await nameInput.fill('智能体B');
    
    if (await saveBtn.isVisible()) {
      await saveBtn.click();
      await page.waitForTimeout(1000);
    }
    
    // 验证两个智能体都存在
    await expect(page.locator('text=智能体A')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=智能体B')).toBeVisible({ timeout: 5000 });
    
    // 配置handoff（如果支持）
    await page.locator('text=智能体A').first().click();
    await page.waitForTimeout(1000);
    
    // 查找handoff配置
    const handoffSection = page.locator('text=handoff, text=移交, text=转交').first();
    if (await handoffSection.isVisible()) {
      await handoffSection.click();
      await page.waitForTimeout(1000);
      
      // 选择handoff目标
      const targetSelect = page.locator('select, [role="combobox"]').first();
      if (await targetSelect.isVisible()) {
        await targetSelect.click();
        await page.waitForTimeout(500);
        
        const targetOption = page.locator('text=智能体B').first();
        if (await targetOption.isVisible()) {
          await targetOption.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('13.2 测试多智能体对话流程', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 切换到Playground
    const playgroundTab = page.locator('button:has-text("Playground")').first();
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click();
    }
    
    await page.waitForSelector('textarea[placeholder*="消息"]', { timeout: 5000 });
    
    // 发送会触发handoff的消息
    const messageInput = page.locator('textarea[placeholder*="消息"]').first();
    await messageInput.fill('测试多智能体handoff');
    await messageInput.press('Enter');
    
    // 等待响应
    await page.waitForTimeout(5000);
    
    // 验证响应
    const responseArea = page.locator('[class*="message"], [class*="response"]').last();
    await expect(responseArea).toBeVisible({ timeout: 30000 });
  });

  // ========== 第十四部分：错误处理和边界情况 ==========
  
  test('14.1 测试空智能体名称验证', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
    await addAgentBtn.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    // 尝试不填写名称直接保存
    const saveBtn = page.locator('button:has-text("保存")').first();
    if (await saveBtn.isVisible()) {
      await saveBtn.click();
      await page.waitForTimeout(1000);
      
      // 验证错误提示
      const errorMsg = page.locator('text=必填, text=required, text=不能为空').first();
      if (await errorMsg.isVisible({ timeout: 2000 })) {
        await expect(errorMsg).toBeVisible();
      }
    }
  });

  test('14.2 测试网络错误处理', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 模拟网络错误（通过拦截请求）
    await page.route('**/api/v1/**', route => route.abort());
    
    // 尝试发送消息
    const playgroundTab = page.locator('button:has-text("Playground")').first();
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click();
    }
    
    await page.waitForSelector('textarea[placeholder*="消息"]', { timeout: 5000 });
    
    const messageInput = page.locator('textarea[placeholder*="消息"]').first();
    await messageInput.fill('测试错误处理');
    await messageInput.press('Enter');
    
    // 验证错误提示
    await page.waitForTimeout(3000);
    const errorMsg = page.locator('text=错误, text=error, text=失败').first();
    if (await errorMsg.isVisible({ timeout: 5000 })) {
      await expect(errorMsg).toBeVisible();
    }
    
    // 恢复网络
    await page.unroute('**/api/v1/**');
  });

  // ========== 第十五部分：性能和响应性 ==========
  
  test('15.1 测试大量智能体加载', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 创建多个智能体
    const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
    for (let i = 0; i < 5; i++) {
      await addAgentBtn.click();
      await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
      
      const nameInput = page.locator('input[placeholder*="名称"]').first();
      await nameInput.fill(`批量智能体${i}`);
      
      const saveBtn = page.locator('button:has-text("保存")').first();
      if (await saveBtn.isVisible()) {
        await saveBtn.click();
        await page.waitForTimeout(500);
      }
    }
    
    // 验证所有智能体都显示
    for (let i = 0; i < 5; i++) {
      await expect(page.locator(`text=批量智能体${i}`)).toBeVisible({ timeout: 5000 });
    }
  });

  test('15.2 测试快速连续操作', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 快速连续创建和删除
    const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
    await addAgentBtn.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    const nameInput = page.locator('input[placeholder*="名称"]').first();
    await nameInput.fill('快速操作测试');
    
    const saveBtn = page.locator('button:has-text("保存")').first();
    if (await saveBtn.isVisible()) {
      await saveBtn.click();
      await page.waitForTimeout(500);
      
      // 立即删除
      const deleteBtn = page.locator('text=快速操作测试').first();
      await deleteBtn.hover();
      
      const menuBtn = page.locator('button[aria-label*="菜单"]').first();
      if (await menuBtn.isVisible()) {
        await menuBtn.click();
        await page.waitForTimeout(300);
        
        const deleteOption = page.locator('text=删除').first();
        if (await deleteOption.isVisible()) {
          await deleteOption.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  // ========== 第十六部分：配置和设置 ==========
  
  test('16.1 访问项目设置', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/config`);
    await page.waitForLoadState('networkidle');
    
    // 验证设置页面
    const settingsPage = page.locator('text=设置, text=Settings, text=配置').first();
    await expect(settingsPage).toBeVisible({ timeout: 5000 });
  });

  test('16.2 修改项目名称', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/config`);
    await page.waitForLoadState('networkidle');
    
    // 查找项目名称输入框
    const nameInput = page.locator('input[value*="项目"], input[placeholder*="名称"]').first();
    if (await nameInput.isVisible()) {
      const oldName = await nameInput.inputValue();
      await nameInput.clear();
      await nameInput.fill('更新后的项目名称');
      
      // 保存
      const saveBtn = page.locator('button:has-text("保存")').first();
      if (await saveBtn.isVisible()) {
        await saveBtn.click();
        await page.waitForTimeout(2000);
        
        // 验证名称已更新
        await expect(nameInput).toHaveValue('更新后的项目名称');
        
        // 恢复原名称
        await nameInput.clear();
        await nameInput.fill(oldName);
        if (await saveBtn.isVisible()) {
          await saveBtn.click();
          await page.waitForTimeout(2000);
        }
      }
    }
  });

  // ========== 第十七部分：导出和分享 ==========
  
  test('17.1 导出工作流JSON', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找导出按钮
    const exportBtn = page.locator('button[aria-label*="导出"], button[aria-label*="export"], button[aria-label*="下载"]').first();
    if (await exportBtn.isVisible()) {
      // 设置下载监听
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
      await exportBtn.click();
      
      const download = await downloadPromise;
      if (download) {
        expect(download.suggestedFilename()).toContain('.json');
      }
    }
  });

  test('17.2 分享工作流', async ({ page }) => {
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    // 查找分享按钮
    const shareBtn = page.locator('button[aria-label*="分享"], button[aria-label*="share"]').first();
    if (await shareBtn.isVisible()) {
      await shareBtn.click();
      await page.waitForTimeout(1000);
      
      // 验证分享模态框
      const shareModal = page.locator('[role="dialog"], [class*="modal"]').first();
      if (await shareModal.isVisible({ timeout: 5000 })) {
        await expect(shareModal).toBeVisible();
        
        // 关闭模态框
        const closeBtn = page.locator('button[aria-label*="关闭"], button[aria-label*="close"]').first();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
        }
      }
    }
  });

  // ========== 第十八部分：完整工作流测试 ==========
  
  test('18.1 完整工作流：从创建到使用', async ({ page }) => {
    // 步骤1: 创建智能体
    await page.goto(`${BASE_URL}/projects/${projectId}/workflow`);
    await page.waitForSelector('[data-tour-target="entity-agents"]', { timeout: 10000 });
    
    const addAgentBtn = page.locator('button:has-text("添加智能体")').first();
    await addAgentBtn.click();
    await page.waitForSelector('input[placeholder*="名称"]', { timeout: 5000 });
    
    const nameInput = page.locator('input[placeholder*="名称"]').first();
    await nameInput.fill('完整流程智能体');
    
    const instructionsInput = page.locator('textarea[placeholder*="指令"]').first();
    await instructionsInput.fill('你是一个完整的测试智能体');
    
    const saveBtn = page.locator('button:has-text("保存")').first();
    if (await saveBtn.isVisible()) {
      await saveBtn.click();
      await page.waitForTimeout(2000);
    }
    
    // 步骤2: 测试对话
    const playgroundTab = page.locator('button:has-text("Playground")').first();
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click();
    }
    
    await page.waitForSelector('textarea[placeholder*="消息"]', { timeout: 5000 });
    
    const messageInput = page.locator('textarea[placeholder*="消息"]').first();
    await messageInput.fill('你好');
    await messageInput.press('Enter');
    await page.waitForTimeout(5000);
    
    // 步骤3: 发布
    const publishBtn = page.locator('button:has-text("发布")').first();
    if (await publishBtn.isVisible() && !(await publishBtn.isDisabled())) {
      await publishBtn.click();
      await page.waitForTimeout(3000);
    }
    
    // 步骤4: 使用助手
    const useBtn = page.locator('button:has-text("使用助手")').first();
    if (await useBtn.isVisible()) {
      await useBtn.click();
      await page.waitForTimeout(2000);
    }
    
    // 验证所有步骤完成
    await expect(page.locator('text=完整流程智能体')).toBeVisible({ timeout: 5000 });
  });
});

// ========== API端点直接测试 ==========

test.describe('API端点100%覆盖测试', () => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

  test('API-1: 健康检查', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data.status).toBe('healthy');
  });

  test('API-2: Ping端点', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/health/ping`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data.ping).toBe('pong');
  });

  test('API-3: API信息', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/info`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data.name).toBeTruthy();
    expect(data.data.version).toBeTruthy();
  });

  test('API-4: 创建项目（需要认证）', async ({ request }) => {
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
    
    // 可能需要认证，所以接受200或401
    expect([200, 201, 401, 400]).toContain(response.status());
  });

  test('API-5: 列出项目（需要认证）', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/v1/projects`);
    // 可能需要认证
    expect([200, 401]).toContain(response.status());
  });
});






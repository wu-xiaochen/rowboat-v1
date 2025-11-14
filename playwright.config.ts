import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright配置
 * 用于端到端测试
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // 可以添加更多浏览器
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // 注释掉webServer，使用已运行的服务
  // webServer: [
  //   {
  //     command: 'cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001',
  //     url: 'http://localhost:8001/api/v1/health',
  //     reuseExistingServer: !process.env.CI,
  //     timeout: 120 * 1000,
  //   },
  //   {
  //     command: 'cd apps/rowboat && npm run dev',
  //     url: 'http://localhost:3001',
  //     reuseExistingServer: !process.env.CI,
  //     timeout: 120 * 1000,
  //   },
  // ],
});


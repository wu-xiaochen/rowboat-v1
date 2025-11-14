import dotenv from 'dotenv'
import path from 'path'

// 统一从项目根目录加载环境变量
// 加载顺序：.env.local (本地覆盖) > 根目录 .env (统一配置) > 当前目录 .env (向后兼容)

// 获取项目根目录路径
// 从 apps/rowboat/app/lib/loadenv.ts 到项目根目录
const currentFileDir = __dirname; // apps/rowboat/app/lib
const rootDir = path.resolve(currentFileDir, '../../../..'); // 项目根目录
const rootEnvPath = path.resolve(rootDir, '.env');
const localEnvPath = path.resolve(process.cwd(), '.env.local');
const currentEnvPath = path.resolve(process.cwd(), '.env');

dotenv.config({ path: [localEnvPath, rootEnvPath, currentEnvPath] });
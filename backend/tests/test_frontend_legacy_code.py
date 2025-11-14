"""
检查前端残留的旧后端功能代码
Check for legacy backend code in frontend
"""
import os
import re
from pathlib import Path


def find_legacy_code_patterns():
    """查找前端中可能残留的旧后端代码模式"""
    frontend_dir = Path("apps/rowboat")
    patterns = [
        # 旧的API调用模式
        (r'PROVIDER_API_KEY|PROVIDER_BASE_URL|PROVIDER_DEFAULT_MODEL', '旧的PROVIDER_*环境变量'),
        (r'COPILOT_MODEL|AGENT_MODEL', '旧的模型配置变量'),
        (r'from.*agents-runtime.*agents', '旧的agents runtime导入'),
        (r'streamResponse|getResponse.*agents', '旧的agents runtime函数'),
        (r'runTurnController|RunTurnController', '旧的Turn控制器'),
        (r'@/src/application/lib/copilot/copilot', '旧的Copilot实现'),
    ]
    
    issues = []
    
    for pattern, description in patterns:
        for file_path in frontend_dir.rglob('*.ts'):
            if 'node_modules' in str(file_path) or '.next' in str(file_path):
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': str(file_path.relative_to(frontend_dir)),
                        'line': line_num,
                        'pattern': pattern,
                        'description': description,
                        'context': content[max(0, match.start()-50):match.end()+50]
                    })
            except Exception as e:
                print(f"读取文件失败 {file_path}: {e}")
    
    return issues


def check_api_routes():
    """检查前端API路由是否都代理到后端"""
    api_routes_dir = Path("apps/rowboat/app/api")
    legacy_routes = []
    
    # 应该被禁用的路由
    disabled_routes = [
        'widget/v1/chats',
        'twilio/turn',
        'twilio/inbound_call',
    ]
    
    for route_path in api_routes_dir.rglob('route.ts'):
        route_str = str(route_path.relative_to(api_routes_dir))
        
        # 检查是否是被禁用的路由
        for disabled in disabled_routes:
            if disabled in route_str:
                try:
                    content = route_path.read_text(encoding='utf-8')
                    # 检查是否返回501
                    if '501' not in content and 'Not implemented' not in content:
                        legacy_routes.append({
                            'file': route_str,
                            'issue': f'路由应该被禁用但未返回501',
                        })
                except Exception as e:
                    print(f"读取路由文件失败 {route_path}: {e}")
    
    return legacy_routes


if __name__ == '__main__':
    print("🔍 检查前端残留的旧后端代码...")
    print("")
    
    # 查找遗留代码模式
    issues = find_legacy_code_patterns()
    if issues:
        print(f"⚠️ 发现 {len(issues)} 个可能的遗留代码问题:")
        for issue in issues[:20]:  # 只显示前20个
            print(f"  {issue['file']}:{issue['line']} - {issue['description']}")
        if len(issues) > 20:
            print(f"  ... 还有 {len(issues) - 20} 个问题")
    else:
        print("✅ 未发现遗留的PROVIDER_*或旧agents runtime代码")
    
    print("")
    
    # 检查API路由
    legacy_routes = check_api_routes()
    if legacy_routes:
        print(f"⚠️ 发现 {len(legacy_routes)} 个未正确禁用的路由:")
        for route in legacy_routes:
            print(f"  {route['file']} - {route['issue']}")
    else:
        print("✅ 所有旧路由都已正确禁用")
    
    print("")
    print("检查完成")






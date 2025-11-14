#!/bin/bash
# 全面测试和修复脚本
# Comprehensive test and fix script

set -e

echo "🔧 开始全面测试和修复流程..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试结果文件
TEST_RESULTS_FILE="test_results_$(date +%Y%m%d_%H%M%S).txt"

# 记录测试结果
log_result() {
    echo "$1" | tee -a "$TEST_RESULTS_FILE"
}

# 检查服务
check_services() {
    log_result "📋 步骤1: 检查服务状态..."
    
    # 检查后端
    if curl -s http://localhost:8001/api/v1/health > /dev/null 2>&1; then
        log_result "  ${GREEN}✓${NC} 后端服务运行中"
    else
        log_result "  ${RED}✗${NC} 后端服务未运行"
        log_result "  请运行: cd backend && uvicorn app.main:app --reload --port 8001"
        return 1
    fi
    
    # 检查前端
    if curl -s http://localhost:3001 > /dev/null 2>&1; then
        log_result "  ${GREEN}✓${NC} 前端服务运行中"
    else
        log_result "  ${RED}✗${NC} 前端服务未运行"
        log_result "  请运行: cd apps/rowboat && npm run dev"
        return 1
    fi
    
    return 0
}

# 检查遗留代码
check_legacy_code() {
    log_result ""
    log_result "📋 步骤2: 检查前端遗留代码..."
    
    if [ -f "scripts/check_legacy_code.sh" ]; then
        bash scripts/check_legacy_code.sh | tee -a "$TEST_RESULTS_FILE"
    else
        log_result "  ${YELLOW}⚠${NC} 遗留代码检查脚本不存在"
    fi
}

# 运行后端测试
run_backend_tests() {
    log_result ""
    log_result "📋 步骤3: 运行后端API测试..."
    
    cd backend
    
    if [ -f "tests/test_api_endpoints.py" ]; then
        python -m pytest tests/test_api_endpoints.py -v --tb=short 2>&1 | tee -a "../$TEST_RESULTS_FILE"
        BACKEND_TEST_RESULT=$?
    else
        log_result "  ${YELLOW}⚠${NC} 后端测试文件不存在"
        BACKEND_TEST_RESULT=0
    fi
    
    cd ..
    return $BACKEND_TEST_RESULT
}

# 运行服务测试
run_service_tests() {
    log_result ""
    log_result "📋 步骤4: 运行服务层测试..."
    
    cd backend
    
    if [ -f "tests/test_services.py" ]; then
        python -m pytest tests/test_services.py -v --tb=short 2>&1 | tee -a "../$TEST_RESULTS_FILE"
        SERVICE_TEST_RESULT=$?
    else
        log_result "  ${YELLOW}⚠${NC} 服务测试文件不存在"
        SERVICE_TEST_RESULT=0
    fi
    
    cd ..
    return $SERVICE_TEST_RESULT
}

# 运行Playwright测试
run_playwright_tests() {
    log_result ""
    log_result "📋 步骤5: 运行Playwright端到端测试..."
    
    if [ -f "scripts/run_playwright_tests.sh" ]; then
        bash scripts/run_playwright_tests.sh 2>&1 | tee -a "$TEST_RESULTS_FILE"
        PLAYWRIGHT_TEST_RESULT=$?
    else
        log_result "  ${YELLOW}⚠${NC} Playwright测试脚本不存在"
        PLAYWRIGHT_TEST_RESULT=0
    fi
    
    return $PLAYWRIGHT_TEST_RESULT
}

# 生成测试报告
generate_report() {
    log_result ""
    log_result "📊 测试结果汇总:"
    log_result "  后端API测试: $([ $BACKEND_TEST_RESULT -eq 0 ] && echo -e "${GREEN}通过${NC}" || echo -e "${RED}失败${NC}")"
    log_result "  服务层测试: $([ $SERVICE_TEST_RESULT -eq 0 ] && echo -e "${GREEN}通过${NC}" || echo -e "${RED}失败${NC}")"
    log_result "  Playwright测试: $([ $PLAYWRIGHT_TEST_RESULT -eq 0 ] && echo -e "${GREEN}通过${NC}" || echo -e "${RED}失败${NC}")"
    log_result ""
    log_result "详细结果已保存到: $TEST_RESULTS_FILE"
}

# 主流程
main() {
    log_result "=========================================="
    log_result "全面测试和修复流程"
    log_result "开始时间: $(date)"
    log_result "=========================================="
    log_result ""
    
    # 检查服务
    if ! check_services; then
        log_result ""
        log_result "${RED}❌ 服务检查失败，请先启动服务${NC}"
        exit 1
    fi
    
    # 检查遗留代码
    check_legacy_code
    
    # 运行测试
    run_backend_tests
    BACKEND_TEST_RESULT=$?
    
    run_service_tests
    SERVICE_TEST_RESULT=$?
    
    run_playwright_tests
    PLAYWRIGHT_TEST_RESULT=$?
    
    # 生成报告
    generate_report
    
    # 返回结果
    if [ $BACKEND_TEST_RESULT -eq 0 ] && [ $SERVICE_TEST_RESULT -eq 0 ] && [ $PLAYWRIGHT_TEST_RESULT -eq 0 ]; then
        log_result ""
        log_result "${GREEN}✅ 所有测试通过！${NC}"
        exit 0
    else
        log_result ""
        log_result "${RED}❌ 部分测试失败，请检查上述输出${NC}"
        exit 1
    fi
}

# 运行主流程
main






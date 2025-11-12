"""
提示词加载器单元测试
Unit tests for Prompt Loader
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from app.core.prompt_loader import PromptLoader, get_prompt_loader


class TestPromptLoader:
    """提示词加载器测试"""
    
    def test_init_with_custom_dir(self, tmp_path):
        """测试：使用自定义目录初始化"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("Test prompt")
        
        loader = PromptLoader(str(test_dir))
        assert loader.prompts_dir == test_dir
    
    def test_init_with_default_dir(self):
        """测试：使用默认目录初始化"""
        loader = PromptLoader()
        assert loader.prompts_dir.exists()
        assert loader.prompts_dir.name == "prompts"
    
    def test_init_with_nonexistent_dir(self, tmp_path):
        """测试：使用不存在的目录初始化（应该抛出异常）"""
        nonexistent_dir = tmp_path / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            PromptLoader(str(nonexistent_dir))
    
    def test_load_prompt_success(self, tmp_path):
        """测试：成功加载提示词文件"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_content = "Test prompt content"
        test_file.write_text(test_content)
        
        loader = PromptLoader(str(test_dir))
        content = loader.load_prompt("test.txt")
        
        assert content == test_content
        assert "test.txt" in loader._cache
    
    def test_load_prompt_not_found(self, tmp_path):
        """测试：加载不存在的提示词文件（应该抛出异常）"""
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        
        loader = PromptLoader(str(test_dir))
        
        with pytest.raises(FileNotFoundError):
            loader.load_prompt("nonexistent.txt")
    
    def test_load_prompt_caching(self, tmp_path):
        """测试：提示词缓存功能"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_content = "Test prompt content"
        test_file.write_text(test_content)
        
        loader = PromptLoader(str(test_dir))
        
        # 第一次加载
        content1 = loader.load_prompt("test.txt")
        assert content1 == test_content
        
        # 删除文件（模拟缓存）
        test_file.unlink()
        
        # 第二次加载（应该从缓存读取）
        content2 = loader.load_prompt("test.txt")
        assert content2 == test_content
        assert content1 == content2
    
    def test_load_all_prompts(self, tmp_path):
        """测试：加载所有提示词文件"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        (test_dir / "prompt1.txt").write_text("Prompt 1")
        (test_dir / "prompt2.txt").write_text("Prompt 2")
        (test_dir / "other_file.md").write_text("Not a prompt")  # 应该被忽略
        
        loader = PromptLoader(str(test_dir))
        prompts = loader.load_all_prompts()
        
        assert len(prompts) == 2
        assert "prompt1" in prompts
        assert "prompt2" in prompts
        assert prompts["prompt1"] == "Prompt 1"
        assert prompts["prompt2"] == "Prompt 2"
    
    def test_build_system_prompt(self, tmp_path):
        """测试：构建完整的系统提示词"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        (test_dir / "copilot_multi_agent.txt").write_text(
            "Main prompt with {agent_model} and {workflow_schema} and {USING_ROWBOAT_DOCS}"
        )
        (test_dir / "current_workflow.txt").write_text("Workflow prompt")
        (test_dir / "example_multi_agent_1.txt").write_text("Example prompt")
        (test_dir / "using_rowboat_docs.txt").write_text("Product docs")
        
        loader = PromptLoader(str(test_dir))
        
        system_prompt = loader.build_system_prompt(
            agent_model="gpt-4",
            workflow_schema='{"type": "object"}',
            using_rowboat_docs="Custom docs",
            include_example=True
        )
        
        # 验证占位符被替换
        assert "{agent_model}" not in system_prompt
        assert "{workflow_schema}" not in system_prompt
        assert "{USING_ROWBOAT_DOCS}" not in system_prompt
        assert "gpt-4" in system_prompt
        assert '{"type": "object"}' in system_prompt
        assert "Custom docs" in system_prompt
        assert "Main prompt" in system_prompt
        assert "Workflow prompt" in system_prompt
        assert "Example prompt" in system_prompt
    
    def test_build_system_prompt_without_example(self, tmp_path):
        """测试：构建系统提示词（不包含示例）"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        (test_dir / "copilot_multi_agent.txt").write_text("Main prompt")
        (test_dir / "current_workflow.txt").write_text("Workflow prompt")
        
        loader = PromptLoader(str(test_dir))
        
        system_prompt = loader.build_system_prompt(
            agent_model="gpt-4",
            workflow_schema='{"type": "object"}',
            include_example=False
        )
        
        assert "Main prompt" in system_prompt
        assert "Workflow prompt" in system_prompt
        # 示例不应该存在（文件不存在时会跳过）
    
    def test_get_edit_agent_prompt(self, tmp_path):
        """测试：获取编辑智能体提示词"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        (test_dir / "copilot_edit_agent.txt").write_text("Edit agent prompt")
        
        loader = PromptLoader(str(test_dir))
        prompt = loader.get_edit_agent_prompt()
        
        assert prompt == "Edit agent prompt"
    
    def test_clear_cache(self, tmp_path):
        """测试：清除缓存"""
        # 创建测试目录和文件
        test_dir = tmp_path / "test_prompts"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("Test prompt")
        
        loader = PromptLoader(str(test_dir))
        loader.load_prompt("test.txt")
        
        assert "test.txt" in loader._cache
        assert len(loader._cache) == 1
        
        loader.clear_cache()
        
        assert len(loader._cache) == 0
    
    def test_get_prompt_loader_singleton(self):
        """测试：获取提示词加载器实例（单例模式）"""
        loader1 = get_prompt_loader()
        loader2 = get_prompt_loader()
        
        # 应该是同一个实例
        assert loader1 is loader2


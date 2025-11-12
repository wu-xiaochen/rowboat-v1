"""
提示词加载器
Prompt Loader

负责从配置文件加载Copilot提示词
Responsible for loading Copilot prompts from configuration files
"""

import os
from pathlib import Path
from typing import Optional, Dict
from app.core.config import get_settings


class PromptLoader:
    """
    提示词加载器类
    Prompt Loader Class
    
    从配置文件加载提示词，支持占位符替换
    Load prompts from configuration files with placeholder replacement support
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化提示词加载器
        Initialize prompt loader
        
        Args:
            prompts_dir: 提示词文件目录（可选，默认使用配置中的路径）
        """
        if prompts_dir is None:
            # 默认使用backend/config/prompts目录
            base_dir = Path(__file__).parent.parent.parent
            prompts_dir = str(base_dir / "config" / "prompts")
        
        self.prompts_dir = Path(prompts_dir)
        
        # 验证目录是否存在
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"提示词目录不存在: {self.prompts_dir}"
            )
        
        # 缓存已加载的提示词
        self._cache: Dict[str, str] = {}
    
    def load_prompt(self, filename: str) -> str:
        """
        加载单个提示词文件
        Load a single prompt file
        
        Args:
            filename: 提示词文件名（例如: "copilot_multi_agent.txt"）
            
        Returns:
            提示词内容
            
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        # 检查缓存
        if filename in self._cache:
            return self._cache[filename]
        
        # 加载文件
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"提示词文件不存在: {file_path}"
            )
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 缓存内容
        self._cache[filename] = content
        
        return content
    
    def load_all_prompts(self) -> Dict[str, str]:
        """
        加载所有提示词文件
        Load all prompt files
        
        Returns:
            提示词字典，键为文件名（不含扩展名），值为提示词内容
        """
        prompts = {}
        
        # 遍历提示词目录中的所有.txt文件
        for file_path in self.prompts_dir.glob("*.txt"):
            filename = file_path.name
            key = file_path.stem  # 不含扩展名的文件名
            
            try:
                prompts[key] = self.load_prompt(filename)
            except Exception as e:
                # 记录错误但不中断
                print(f"警告: 无法加载提示词文件 {filename}: {e}")
        
        return prompts
    
    def build_system_prompt(
        self,
        agent_model: str,
        workflow_schema: str,
        using_rowboat_docs: Optional[str] = None,
        include_example: bool = True
    ) -> str:
        """
        构建完整的系统提示词
        Build complete system prompt
        
        Args:
            agent_model: 智能体模型名称
            workflow_schema: 工作流JSON schema
            using_rowboat_docs: 产品文档内容（可选）
            include_example: 是否包含示例（默认True）
            
        Returns:
            完整的系统提示词
        """
        # 加载主要提示词组件
        multi_agent_prompt = self.load_prompt("copilot_multi_agent.txt")
        current_workflow_prompt = self.load_prompt("current_workflow.txt")
        
        # 加载示例（可选）
        example_prompt = ""
        if include_example:
            try:
                example_prompt = self.load_prompt("example_multi_agent_1.txt")
            except FileNotFoundError:
                # 示例文件不存在时跳过
                pass
        
        # 加载产品文档（可选）
        if using_rowboat_docs is None:
            try:
                using_rowboat_docs = self.load_prompt("using_rowboat_docs.txt")
            except FileNotFoundError:
                using_rowboat_docs = ""
        
        # 组合提示词
        parts = [
            multi_agent_prompt,
            example_prompt,
            current_workflow_prompt,
        ]
        
        system_prompt = "\n\n".join(filter(None, parts))
        
        # 替换占位符
        system_prompt = system_prompt.replace("{agent_model}", agent_model)
        system_prompt = system_prompt.replace("{workflow_schema}", workflow_schema)
        system_prompt = system_prompt.replace("{USING_ROWBOAT_DOCS}", using_rowboat_docs)
        
        return system_prompt
    
    def get_edit_agent_prompt(self) -> str:
        """
        获取编辑智能体提示词
        Get edit agent prompt
        
        Returns:
            编辑智能体提示词
        """
        return self.load_prompt("copilot_edit_agent.txt")
    
    def clear_cache(self):
        """
        清除缓存
        Clear cache
        """
        self._cache.clear()


# 全局提示词加载器实例（单例模式）
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """
    获取提示词加载器实例（单例）
    Get prompt loader instance (singleton)
    
    Returns:
        提示词加载器实例
    """
    global _prompt_loader
    
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    
    return _prompt_loader


import { useMemo } from "react";

type Block =
  | { type: "text"; content: string }
  | { type: "code"; content: string };

const copilotCodeMarker = "copilot_change\n";

function parseMarkdown(markdown: string): Block[] {
  // Debug: Log the markdown to understand what we're receiving
  console.log('🔍 [parseMarkdown] 处理内容:', {
    length: markdown.length,
    preview: markdown.substring(0, 200),
    hasTripleBackticks: markdown.includes('```'),
    copilotChangeCount: (markdown.match(/```copilot_change/g) || []).length
  });
  
  // 首先，检测所有copilot_change元数据模式（即使没有```标记或JSON未完整）
  // 这样可以在流式输出时更早地识别和显示StreamingAction卡片
  // 注意：正则表达式中需要转义斜杠 // -> \/\/
  // 改进：允许元数据注释之间有空行，使用更宽松的匹配
  // 使用更灵活的正则：允许元数据注释之间有任意空白字符（包括空行）
  const copilotMetadataPattern = /(?:copilot_change\s*\n?)?\/\/\s*action:\s*(\w+)(?:\s*\n*\s*)?\/\/\s*config_type:\s*(\w+)(?:\s*\n*\s*)?\/\/\s*name:\s*([^\n\{]+)/gm;
  const copilotMatches: Array<{ start: number; end: number; action: string; configType: string; name: string }> = [];
  let metadataMatch;
  
  // 重置正则表达式的 lastIndex（确保每次调用都能正确匹配）
  copilotMetadataPattern.lastIndex = 0;
  
  // 找到所有copilot_change元数据模式的位置
  while ((metadataMatch = copilotMetadataPattern.exec(markdown)) !== null) {
    const start = metadataMatch.index;
    // JavaScript中，使用数组索引访问捕获组，而不是.group()方法
    const action = (metadataMatch[1] || '').trim();
    const configType = (metadataMatch[2] || '').trim();
    const name = (metadataMatch[3] || '').trim();
    
    // 调试日志
    console.log(`🔍 [parseMarkdown] 匹配到元数据: action=${action}, configType=${configType}, name=${name}, start=${start}`);
    
    // 查找这个元数据块对应的JSON开始位置（在匹配的元数据之后）
    const metadataEnd = metadataMatch.index + metadataMatch[0].length;
    const jsonStart = markdown.indexOf('{', metadataEnd);
    if (jsonStart !== -1) {
      // 尝试找到JSON结束位置（即使未完整）
      let braceCount = 0;
      let jsonEnd = -1;
      let inString = false;
      let escapeNext = false;
      
      for (let i = jsonStart; i < markdown.length; i++) {
        const char = markdown[i];
        
        if (escapeNext) {
          escapeNext = false;
          continue;
        }
        
        if (char === '\\') {
          escapeNext = true;
          continue;
        }
        
        if (char === '"') {
          inString = !inString;
          continue;
        }
        
        if (!inString) {
          if (char === '{') braceCount++;
          if (char === '}') {
            braceCount--;
            if (braceCount === 0) {
              jsonEnd = i + 1;
              break;
            }
          }
        }
      }
      
      // 如果找到JSON结束，记录完整的块；如果没找到，记录到当前文本结束（流式输出）
      const end = jsonEnd !== -1 ? jsonEnd : markdown.length;
      copilotMatches.push({ start, end, action, configType, name });
      console.log(`✅ [parseMarkdown] 检测到 copilot_change 元数据块: action=${action}, configType=${configType}, name=${name}, start=${start}, end=${end}, complete=${jsonEnd !== -1}`);
    } else {
      // 没有找到JSON开始，但仍记录元数据位置（流式输出中）
      // 在这种情况下，end应该是从start到markdown结束的所有内容
      const end = markdown.length;
      copilotMatches.push({ start, end, action, configType, name });
      console.log(`⚠️ [parseMarkdown] 检测到 copilot_change 元数据（无JSON）: action=${action}, configType=${configType}, name=${name}, start=${start}, end=${end}`);
    }
  }
  
  // 现在处理markdown内容，合并代码块和copilotMatches
  // 策略：按照位置顺序处理，将文本和代码块正确交错
  const blocks: Block[] = [];
  
  // 收集所有需要处理的区间（代码块和copilotMatches）
  const intervals: Array<{ start: number; end: number; type: 'codeBlock' | 'copilotMatch'; data: any }> = [];
  
  // 首先，处理标准的markdown代码块（```...```）
  const codeBlockRegex = /```(\w+)?\s*\n([\s\S]*?)```/g;
  codeBlockRegex.lastIndex = 0;
  let match;
  
  while ((match = codeBlockRegex.exec(markdown)) !== null) {
    const fullMatch = match[0];
    const language = (match[1] || '').trim();
    const codeContent = match[2];
    const matchStart = match.index;
    const matchEnd = match.index + fullMatch.length;
    
    // 检查这个代码块是否与任何copilotMatches重叠
    const overlapsWithCopilotMatch = copilotMatches.some(cp => 
      (matchStart >= cp.start && matchStart < cp.end) || 
      (matchEnd > cp.start && matchEnd <= cp.end) ||
      (matchStart <= cp.start && matchEnd >= cp.end)
    );
    
    // 如果与copilotMatches重叠，跳过（copilotMatches优先）
    if (!overlapsWithCopilotMatch) {
      intervals.push({
        start: matchStart,
        end: matchEnd,
        type: 'codeBlock',
        data: { language, content: codeContent, isCopilotChange: language === 'copilot_change' }
      });
    }
  }
  
  // 添加copilotMatches作为区间
  copilotMatches.forEach(cp => {
    intervals.push({
      start: cp.start,
      end: cp.end,
      type: 'copilotMatch',
      data: cp
    });
  });
  
  // 按start位置排序
  intervals.sort((a, b) => a.start - b.start);
  
  // 处理每个区间
  let currentIndex = 0;
  for (const interval of intervals) {
    // 添加区间之前的文本
    if (interval.start > currentIndex) {
      const textContent = markdown.substring(currentIndex, interval.start).trim();
      if (textContent) {
        // 过滤掉copilot_change相关的文本（元数据注释等）
        const lines = textContent.split('\n');
        const filteredLines: string[] = [];
        
        for (const line of lines) {
          const trimmed = line.trim();
          // 跳过copilot_change标记和元数据注释
          if (trimmed === 'copilot_change' || 
              trimmed.startsWith('// action:') || 
              trimmed.startsWith('// config_type:') || 
              trimmed.startsWith('// name:')) {
            continue;
          }
          filteredLines.push(line);
        }
        
        const filteredContent = filteredLines.join('\n').trim();
        if (filteredContent) {
          console.log(`📝 [parseMarkdown] 添加文本块: length=${filteredContent.length}`);
          blocks.push({ type: 'text', content: filteredContent });
        }
      }
    }
    
    // 处理区间内容
    if (interval.type === 'codeBlock') {
      const cb = interval.data;
      if (cb.isCopilotChange) {
        console.log('✅ [parseMarkdown] 识别为 copilot_change 代码块，content:', cb.content.substring(0, 100));
        blocks.push({ type: 'code', content: cb.content });
      } else {
        // 其他代码块作为文本处理
        const codeBlockText = markdown.substring(interval.start, interval.end);
        blocks.push({ type: 'text', content: codeBlockText });
      }
    } else if (interval.type === 'copilotMatch') {
      const cp = interval.data;
      const copilotContent = markdown.substring(interval.start, interval.end).trim();
      if (copilotContent) {
        // 移除copilot_change标记（如果存在）
        let cleanContent = copilotContent;
        if (cleanContent.startsWith('copilot_change')) {
          cleanContent = cleanContent.replace(/^copilot_change\s*\n?/, '');
        }
        console.log(`✅ [parseMarkdown] 添加 copilot_change 代码块（从元数据检测）: action=${cp.action}, configType=${cp.configType}, name=${cp.name}, length=${cleanContent.length}`);
        blocks.push({ type: 'code', content: cleanContent });
      }
    }
    
    currentIndex = interval.end;
  }
  
  // 添加最后剩余的文本
  if (currentIndex < markdown.length) {
    const remainingText = markdown.substring(currentIndex).trim();
    if (remainingText) {
      // 过滤掉copilot_change相关的文本和JSON内容
      const lines = remainingText.split('\n');
      const filteredLines: string[] = [];
      let inCopilotChangeBlock = false;
      let braceCount = 0;
      let inString = false;
      let escapeNext = false;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // 检测是否开始了一个新的copilot_change块
        if (!inCopilotChangeBlock) {
          // 检查是否是元数据注释的开始
          if (trimmed.startsWith('// action:') || 
              (trimmed.startsWith('// config_type:') && i > 0 && lines[i-1]?.trim().startsWith('// action:')) ||
              (trimmed.startsWith('// name:') && i > 1 && 
               lines[i-1]?.trim().startsWith('// config_type:') && 
               lines[i-2]?.trim().startsWith('// action:'))) {
            inCopilotChangeBlock = true;
            continue;
          }
        }
        
        // 如果在copilot_change块中，检查JSON状态
        if (inCopilotChangeBlock) {
          // 检查是否到达JSON开始
          if (!line.includes('{') && !line.includes('}')) {
            // 还没有JSON，继续跳过
            continue;
          }
          
          // 处理JSON内容
          for (let j = 0; j < line.length; j++) {
            const char = line[j];
            
            if (escapeNext) {
              escapeNext = false;
              continue;
            }
            
            if (char === '\\') {
              escapeNext = true;
              continue;
            }
            
            if (char === '"') {
              inString = !inString;
              continue;
            }
            
            if (!inString) {
              if (char === '{') {
                braceCount++;
              } else if (char === '}') {
                braceCount--;
                if (braceCount === 0) {
                  // JSON结束
                  inCopilotChangeBlock = false;
                  break;
                }
              }
            }
          }
          continue;
        }
        
        // 跳过copilot_change标记和元数据注释
        if (trimmed === 'copilot_change' || 
            trimmed.startsWith('// action:') || 
            trimmed.startsWith('// config_type:') || 
            trimmed.startsWith('// name:')) {
          continue;
        }
        
        // 检查是否包含JSON对象（可能是遗漏的copilot_change块）
        if (trimmed.startsWith('{') && trimmed.includes('"config_changes"')) {
          // 这可能是copilot_change的JSON内容，跳过
          continue;
        }
        
        filteredLines.push(line);
      }
      
      const filteredContent = filteredLines.join('\n').trim();
      if (filteredContent) {
        console.log(`📝 [parseMarkdown] 添加剩余文本块: length=${filteredContent.length}`);
        blocks.push({ type: 'text', content: filteredContent });
      }
    }
  }
  
  // 如果没有找到任何块，整个内容作为文本（但过滤掉copilot_change相关内容）
  if (blocks.length === 0) {
    console.log('⚠️ [parseMarkdown] 没有找到任何代码块，整个内容作为文本');
    // 过滤掉copilot_change相关的文本
    const lines = markdown.split('\n');
    const filteredLines: string[] = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      // 跳过copilot_change标记和元数据注释
      if (trimmed === 'copilot_change' || 
          trimmed.startsWith('// action:') || 
          trimmed.startsWith('// config_type:') || 
          trimmed.startsWith('// name:')) {
        continue;
      }
      filteredLines.push(line);
    }
    
    const filteredContent = filteredLines.join('\n').trim();
    if (filteredContent) {
      blocks.push({ type: 'text', content: filteredContent });
    } else {
      // 如果过滤后为空，仍然添加（可能是纯JSON内容）
      blocks.push({ type: 'text', content: markdown });
    }
  }
  
  console.log('📦 [parseMarkdown] 最终得到', blocks.length, '个块:', blocks.map(b => b.type));
  return blocks;
}

export function useParsedBlocks(text: string): Block[] {
  return useMemo(() => {
    return parseMarkdown(text);
  }, [text]);
}
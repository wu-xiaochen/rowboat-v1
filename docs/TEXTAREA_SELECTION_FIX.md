# Textarea Selection 错误修复

## 问题描述

前端出现以下错误：
```
Uncaught TypeError: Cannot read properties of null (reading 'getSelection')
    at HTMLTextAreaElement.<anonymous> (MVTODUFQ.js:52:27619)
```

## 问题原因

在 `components/ui/textarea.tsx` 中，`debouncedAdjustHeight` 函数在 `requestAnimationFrame` 回调中尝试访问和恢复 textarea 的选择（selection），但在某些情况下：

1. **组件已卸载**：textarea 元素已经从 DOM 中移除
2. **异步执行**：`requestAnimationFrame` 回调执行时，textarea 可能已经被卸载
3. **Selection 访问失败**：当 textarea 被卸载时，访问 `selectionStart` 和 `selectionEnd` 会失败
4. **setSelectionRange 失败**：在已卸载的元素上调用 `setSelectionRange` 会抛出错误

## 解决方案

### 1. 添加安全检查

在访问 selection 之前，检查 textarea 是否仍然存在：

```typescript
// Safely get selection range (may fail if textarea is detached)
try {
  selectionStart = textarea.selectionStart;
  selectionEnd = textarea.selectionEnd;
} catch (e) {
  // If selection access fails, textarea may be detached, skip adjustment
  return;
}
```

### 2. 在 requestAnimationFrame 中再次检查

在 `requestAnimationFrame` 回调中，再次验证 textarea 是否仍然存在：

```typescript
requestAnimationFrame(() => {
  // Double-check textarea still exists and is mounted before accessing it
  if (!textarea || !textarea.offsetParent || !document.body.contains(textarea)) {
    return;
  }
  
  // ... rest of the code
});
```

### 3. 安全地恢复选择

在恢复选择时，使用 try-catch 捕获可能的错误：

```typescript
// Restore focus and selection if it was focused before
if (hadFocus && document.activeElement !== textarea) {
  textarea.focus();
  // Safely restore selection (may fail if textarea is detached)
  try {
    textarea.setSelectionRange(selectionStart, selectionEnd);
  } catch (e) {
    // Ignore selection restoration errors if textarea is detached
  }
}
```

## 修改文件

- `apps/rowboat/components/ui/textarea.tsx`
  - 在访问 selection 之前添加 try-catch
  - 在 `requestAnimationFrame` 回调中添加存在性检查
  - 在恢复选择时添加错误处理

## 验证

修复后，textarea 组件应该能够：
1. ✅ 安全地处理组件卸载情况
2. ✅ 避免在已卸载的元素上访问 selection
3. ✅ 优雅地处理异步回调中的元素访问

## 相关错误

这类错误通常发生在：
- React 组件快速卸载和重新挂载时
- 路由切换时
- 条件渲染导致元素移除时
- 异步操作（如 `requestAnimationFrame`、`setTimeout`）执行时元素已被移除

## 最佳实践

1. **始终检查元素存在性**：在异步回调中访问 DOM 元素前，检查元素是否仍然存在
2. **使用 try-catch**：对于可能失败的 DOM 操作，使用 try-catch 捕获错误
3. **清理定时器**：在组件卸载时，清理所有定时器和异步操作
4. **使用 ref 检查**：使用 React ref 来跟踪元素的存在性


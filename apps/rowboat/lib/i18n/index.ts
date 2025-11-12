/**
 * 国际化配置
 * i18n configuration
 */

import zhCN from './locales/zh-CN.json';

export type Locale = 'zh-CN' | 'en-US';

export interface Translations {
  [key: string]: string | Translations;
}

export const locales = {
  'zh-CN': zhCN,
  'en-US': zhCN, // 暂时使用中文作为默认，后续可以添加英文翻译
} as const;

export const defaultLocale: Locale = 'zh-CN';

/**
 * 获取翻译文本
 * Get translated text
 */
export function t(key: string, locale: Locale = defaultLocale): string {
  const translations = locales[locale];
  const keys = key.split('.');
  let value: any = translations;

  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return key; // 如果找不到翻译，返回原始key
    }
  }

  return typeof value === 'string' ? value : key;
}

/**
 * 获取嵌套翻译对象
 * Get nested translation object
 */
export function getTranslations(
  namespace: string,
  locale: Locale = defaultLocale
): Translations {
  const translations = locales[locale];
  const keys = namespace.split('.');
  let value: any = translations;

  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return {};
    }
  }

  return value && typeof value === 'object' ? value : {};
}

/**
 * 格式化翻译文本（支持参数替换）
 * Format translated text with parameters
 */
export function tf(
  key: string,
  params: Record<string, string | number> = {},
  locale: Locale = defaultLocale
): string {
  let text = t(key, locale);

  // 替换参数
  for (const [param, value] of Object.entries(params)) {
    text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), String(value));
  }

  return text;
}


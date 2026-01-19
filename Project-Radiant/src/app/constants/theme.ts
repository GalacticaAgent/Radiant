// 主题颜色常量
export const COLORS = {
  primary: '#0F3B6C',
  primaryHover: '#0a2945',
  secondary: '#4A2E9E',
  background: '#F8F9FA',
} as const;

// 渐变样式
export const GRADIENTS = {
  primary: 'from-[#0F3B6C] to-[#4A2E9E]',
  primaryBg: 'from-blue-50 to-purple-50',
} as const;

// 图标盒子样式（多个页面重复使用的方形渐变图标容器）
export const ICON_BOX_CLASSES = 'h-10 w-10 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center';

// 页面标题样式
export const PAGE_TITLE_CLASSES = 'text-2xl font-bold';
export const PAGE_SUBTITLE_CLASSES = 'text-sm text-muted-foreground';

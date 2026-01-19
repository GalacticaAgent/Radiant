// 多语言支持
import React from 'react';

export type Language = 'zh-CN' | 'en-US';

export interface Translations {
  // 通用
  common: {
    confirm: string;
    cancel: string;
    close: string;
    save: string;
    submit: string;
    loading: string;
  };
  // 设置
  settings: {
    title: string;
    theme: string;
    themeLight: string;
    themeDark: string;
    themeSystem: string;
    language: string;
    feedback: string;
    feedbackTitle: string;
    feedbackDescription: string;
    feedbackPlaceholder: string;
    feedbackSubmit: string;
    feedbackSuccess: string;
    feedbackError: string;
  };
  // 导航
  navigation: {
    dashboard: string;
    knowledgeGraph: string;
    favorites: string;
    userCenter: string;
    settings: string;
  };
}

const translations: Record<Language, Translations> = {
  'zh-CN': {
    common: {
      confirm: '确认',
      cancel: '取消',
      close: '关闭',
      save: '保存',
      submit: '提交',
      loading: '加载中...',
    },
    settings: {
      title: '设置',
      theme: '主题',
      themeLight: '浅色',
      themeDark: '深色',
      themeSystem: '跟随系统',
      language: '语言',
      feedback: '反馈与建议',
      feedbackTitle: '反馈与建议',
      feedbackDescription: '我们非常重视您的反馈，请告诉我们您的想法和建议。',
      feedbackPlaceholder: '请输入您的反馈或建议...',
      feedbackSubmit: '提交反馈',
      feedbackSuccess: '感谢您的反馈！我们会认真考虑您的建议。',
      feedbackError: '提交失败，请稍后重试。',
    },
    navigation: {
      dashboard: '智能助手',
      knowledgeGraph: '知识图谱',
      favorites: '收藏夹',
      userCenter: '用户中心',
      settings: '设置',
    },
  },
  'en-US': {
    common: {
      confirm: 'Confirm',
      cancel: 'Cancel',
      close: 'Close',
      save: 'Save',
      submit: 'Submit',
      loading: 'Loading...',
    },
    settings: {
      title: 'Settings',
      theme: 'Theme',
      themeLight: 'Light',
      themeDark: 'Dark',
      themeSystem: 'System',
      language: 'Language',
      feedback: 'Feedback & Suggestions',
      feedbackTitle: 'Feedback & Suggestions',
      feedbackDescription: 'We value your feedback. Please share your thoughts and suggestions with us.',
      feedbackPlaceholder: 'Please enter your feedback or suggestions...',
      feedbackSubmit: 'Submit Feedback',
      feedbackSuccess: 'Thank you for your feedback! We will carefully consider your suggestions.',
      feedbackError: 'Failed to submit. Please try again later.',
    },
    navigation: {
      dashboard: 'Dashboard',
      knowledgeGraph: 'Knowledge Graph',
      favorites: 'Favorites',
      userCenter: 'User Center',
      settings: 'Settings',
    },
  },
};

// 获取当前语言
export function getLanguage(): Language {
  if (typeof window === 'undefined') return 'zh-CN';
  const saved = localStorage.getItem('language') as Language;
  return saved && translations[saved] ? saved : 'zh-CN';
}

// 设置语言
export function setLanguage(lang: Language) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('language', lang);
  // 触发语言变更事件
  window.dispatchEvent(new CustomEvent('languagechange', { detail: lang }));
}

// 获取翻译
export function t(): Translations {
  return translations[getLanguage()];
}

// 创建翻译hook（用于React组件）
export function useTranslation() {
  const [language, setLanguageState] = React.useState<Language>(getLanguage());

  React.useEffect(() => {
    const handleLanguageChange = (e: CustomEvent<Language>) => {
      setLanguageState(e.detail);
    };

    window.addEventListener('languagechange', handleLanguageChange as EventListener);
    return () => {
      window.removeEventListener('languagechange', handleLanguageChange as EventListener);
    };
  }, []);

  const changeLanguage = (lang: Language) => {
    setLanguage(lang);
    setLanguageState(lang);
  };

  return {
    t: translations[language],
    language,
    changeLanguage,
  };
}

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Label } from '@/app/components/ui/label';
import { Switch } from '@/app/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select';
import { Settings, Moon, Sun, Monitor, MessageSquare, Globe } from 'lucide-react';
import { useTranslation, type Language } from '@/utils/i18n';
import { FeedbackDialog } from './FeedbackDialog';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const { t, language, changeLanguage } = useTranslation();
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);

  // 初始化主题
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null;
    const initialTheme = savedTheme || 'system';
    setTheme(initialTheme);
    applyTheme(initialTheme);

    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const currentTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null || 'system';
      if (currentTheme === 'system') {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const applyTheme = (themeToApply: 'light' | 'dark' | 'system') => {
    if (typeof window === 'undefined') return;
    
    const root = document.documentElement;
    if (themeToApply === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      themeToApply = prefersDark ? 'dark' : 'light';
    }
    
    if (themeToApply === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);
  };

  const handleLanguageChange = (lang: string) => {
    changeLanguage(lang as Language);
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              {t.settings.title}
            </DialogTitle>
            <DialogDescription>
              {t.settings.feedbackDescription}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* 主题设置 */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="theme" className="flex items-center gap-2">
                  <Monitor className="h-4 w-4" />
                  {t.settings.theme}
                </Label>
              </div>
              <Select value={theme} onValueChange={handleThemeChange}>
                <SelectTrigger id="theme" className="w-full">
                  <SelectValue placeholder={t.settings.theme} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">
                    <div className="flex items-center gap-2">
                      <Sun className="h-4 w-4" />
                      {t.settings.themeLight}
                    </div>
                  </SelectItem>
                  <SelectItem value="dark">
                    <div className="flex items-center gap-2">
                      <Moon className="h-4 w-4" />
                      {t.settings.themeDark}
                    </div>
                  </SelectItem>
                  <SelectItem value="system">
                    <div className="flex items-center gap-2">
                      <Monitor className="h-4 w-4" />
                      {t.settings.themeSystem}
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 语言设置 */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="language" className="flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  {t.settings.language}
                </Label>
              </div>
              <Select value={language} onValueChange={handleLanguageChange}>
                <SelectTrigger id="language" className="w-full">
                  <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    <SelectValue placeholder={t.settings.language} />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="zh-CN">简体中文</SelectItem>
                  <SelectItem value="en-US">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 反馈入口 */}
            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                {t.settings.feedback}
              </Label>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => {
                  setShowFeedbackDialog(true);
                  onOpenChange(false);
                }}
              >
                <MessageSquare className="mr-2 h-4 w-4" />
                {t.settings.feedback}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <FeedbackDialog
        open={showFeedbackDialog}
        onOpenChange={setShowFeedbackDialog}
        onClose={() => {
          setShowFeedbackDialog(false);
          onOpenChange(true);
        }}
      />
    </>
  );
}

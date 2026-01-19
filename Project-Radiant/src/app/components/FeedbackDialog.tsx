import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Textarea } from '@/app/components/ui/textarea';
import { Label } from '@/app/components/ui/label';
import { MessageSquare, Loader2 } from 'lucide-react';
import { useTranslation } from '@/utils/i18n';

interface FeedbackDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onClose?: () => void;
}

export function FeedbackDialog({ open, onOpenChange, onClose }: FeedbackDialogProps) {
  const { t } = useTranslation();
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleSubmit = async () => {
    if (!feedback.trim()) return;

    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      // 这里可以连接到实际的反馈API
      // 目前先模拟提交
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 保存到localStorage作为示例（实际应该发送到服务器）
      const feedbacks = JSON.parse(localStorage.getItem('user_feedbacks') || '[]');
      feedbacks.push({
        content: feedback,
        timestamp: new Date().toISOString(),
      });
      localStorage.setItem('user_feedbacks', JSON.stringify(feedbacks));

      setSubmitStatus('success');
      setFeedback('');
      
      // 显示成功消息
      setTimeout(() => {
        setSubmitStatus('idle');
        onOpenChange(false);
        if (onClose) onClose();
      }, 1500);
    } catch (error) {
      console.error('提交反馈失败:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFeedback('');
      setSubmitStatus('idle');
      onOpenChange(false);
      if (onClose) onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            {t.settings.feedbackTitle}
          </DialogTitle>
          <DialogDescription>
            {t.settings.feedbackDescription}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="feedback">{t.settings.feedback}</Label>
            <Textarea
              id="feedback"
              placeholder={t.settings.feedbackPlaceholder}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={6}
              disabled={isSubmitting}
              className="resize-none"
            />
          </div>

          {submitStatus === 'success' && (
            <div className="rounded-md bg-green-50 dark:bg-green-900/20 p-3 text-sm text-green-800 dark:text-green-200">
              {t.settings.feedbackSuccess}
            </div>
          )}

          {submitStatus === 'error' && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-3 text-sm text-red-800 dark:text-red-200">
              {t.settings.feedbackError}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            {t.common.cancel}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !feedback.trim()}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t.common.loading}
              </>
            ) : (
              t.settings.feedbackSubmit
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

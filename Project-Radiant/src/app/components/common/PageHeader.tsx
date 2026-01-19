import React from 'react';
import { LucideIcon } from 'lucide-react';
import { ICON_BOX_CLASSES, PAGE_TITLE_CLASSES, PAGE_SUBTITLE_CLASSES } from '@/app/constants/theme';

interface PageHeaderProps {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  actions?: React.ReactNode;
}

export function PageHeader({ icon: Icon, title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-3">
        <div className={ICON_BOX_CLASSES}>
          <Icon className="h-5 w-5 text-white" />
        </div>
        <div>
          <h2 className={PAGE_TITLE_CLASSES}>{title}</h2>
          <p className={PAGE_SUBTITLE_CLASSES}>{subtitle}</p>
        </div>
      </div>
      {actions && <div>{actions}</div>}
    </div>
  );
}
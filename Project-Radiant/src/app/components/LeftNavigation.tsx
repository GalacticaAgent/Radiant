import React, { useState } from 'react';
import { Button } from '@/app/components/ui/button';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { 
  Plus, 
  MessageSquare, 
  ChevronLeft,
  ChevronRight,
  Trash2,
  Clock,
  Network,
  Bookmark,
  FileText,
  X,
  RotateCcw
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/app/components/ui/tooltip';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/app/components/ui/alert-dialog';

interface Conversation {
  id: string;
  title: string;
  timestamp: Date;
  type?: 'chat' | 'review';
}

interface LeftNavigationProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  currentView: string;
  onNavigate: (view: string) => void;
  conversations?: Conversation[];
  currentConversationId?: string | null;
  onSelectConversation?: (id: string) => void;
  onDeleteConversation?: (id: string) => void;
  onNewConversation?: () => void;
  onClearAllConversations?: () => void;
  showConversations?: boolean;
}

export function LeftNavigation({
  collapsed,
  onToggleCollapse,
  currentView,
  onNavigate,
  conversations = [],
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewConversation,
  onClearAllConversations,
  showConversations = false
}: LeftNavigationProps) {
  
  const [showClearDialog, setShowClearDialog] = useState(false);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const handleClearAll = () => {
    onClearAllConversations?.();
    setShowClearDialog(false);
  };

  return (
    <TooltipProvider delayDuration={300}>
      <div className={`${collapsed ? 'w-16' : 'w-72'} bg-card border-r flex flex-col transition-all duration-300`}>
        {/* 头部 - 新对话按钮 - 所有页面都显示 */}
        <div className="p-4 border-b space-y-2">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  size="icon"
                  className="w-full bg-[#0F3B6C] hover:bg-[#0a2945] text-white"
                  onClick={onNewConversation}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">
                <p>新对话</p>
              </TooltipContent>
            </Tooltip>
          ) : (
            <Button 
              className="w-full bg-[#0F3B6C] hover:bg-[#0a2945] text-white"
              onClick={onNewConversation}
            >
              <Plus className="mr-2 h-4 w-4" />
              新对话
            </Button>
          )}
        </div>

        {/* 功能导航 */}
        <div className="border-b">
          <div className="p-2 space-y-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={currentView === 'dashboard' ? 'secondary' : 'ghost'}
                  className={`w-full ${collapsed ? 'justify-center px-0' : 'justify-start'} text-sm`}
                  onClick={() => onNavigate('dashboard')}
                >
                  <MessageSquare className={`h-4 w-4 ${collapsed ? '' : 'mr-2'}`} />
                  {!collapsed && '智能助手'}
                </Button>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right">
                  <p>智能助手</p>
                </TooltipContent>
              )}
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={currentView === 'graph' ? 'secondary' : 'ghost'}
                  className={`w-full ${collapsed ? 'justify-center px-0' : 'justify-start'} text-sm`}
                  onClick={() => onNavigate('graph')}
                >
                  <Network className={`h-4 w-4 ${collapsed ? '' : 'mr-2'}`} />
                  {!collapsed && '知识图谱'}
                </Button>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right">
                  <p>知识图谱</p>
                </TooltipContent>
              )}
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={currentView === 'favorites' ? 'secondary' : 'ghost'}
                  className={`w-full ${collapsed ? 'justify-center px-0' : 'justify-start'} text-sm`}
                  onClick={() => onNavigate('favorites')}
                >
                  <Bookmark className={`h-4 w-4 ${collapsed ? '' : 'mr-2'}`} />
                  {!collapsed && '收藏夹'}
                </Button>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right">
                  <p>收藏夹</p>
                </TooltipContent>
              )}
            </Tooltip>
          </div>
        </div>

        {/* 对话列表 - 仅在智能助手页面显示 */}
        {showConversations && !collapsed && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* 对话列表标题栏 */}
            {conversations.length > 0 && (
              <div className="px-3 py-2 border-b flex items-center justify-between">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  对话历史 ({conversations.length})
                </div>
                <AlertDialog open={showClearDialog} onOpenChange={setShowClearDialog}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 text-muted-foreground hover:text-destructive relative"
                          onClick={(e) => {
                            e.stopPropagation();
                          }}
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          {/* 角标提示 */}
                          <span className="absolute -top-0.5 -right-0.5 h-2 w-2 bg-destructive rounded-full border border-white"></span>
                        </Button>
                      </AlertDialogTrigger>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <p>清空所有历史记录</p>
                    </TooltipContent>
                  </Tooltip>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>确认清空历史记录</AlertDialogTitle>
                      <AlertDialogDescription>
                        您确定要清空所有对话历史吗？此操作将删除所有 {conversations.length} 条对话记录，且无法撤销。
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>取消</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleClearAll}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        确认清空
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            )}
            <ScrollArea className="flex-1">
              <div className="p-2 space-y-1">
                {conversations.length === 0 ? (
                  <div className="p-4 text-center">
                    <MessageSquare className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                    <p className="text-xs text-muted-foreground">暂无对话历史</p>
                  </div>
                ) : (
                  conversations.map(conv => (
                <div
                  key={conv.id}
                  className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                    currentConversationId === conv.id
                      ? 'bg-accent border border-[#0F3B6C]'
                      : 'hover:bg-muted/50'
                  }`}
                  onClick={() => onSelectConversation?.(conv.id)}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0">
                      {conv.type === 'review' ? (
                        <FileText className="h-4 w-4 mt-0.5 text-[#0F3B6C]" />
                      ) : (
                        <MessageSquare className="h-4 w-4 mt-0.5 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0 overflow-hidden">
                      <div className="font-medium text-sm break-words line-clamp-2">{conv.title}</div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                        <Clock className="h-3 w-3 flex-shrink-0" />
                        <span className="truncate">{formatTime(conv.timestamp)}</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 ml-1"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation?.(conv.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3 text-destructive" />
                    </Button>
                  </div>
                </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* 折叠状态下的对话指示器 */}
        {showConversations && collapsed && (
          <div className="flex-1 flex flex-col items-center justify-start pt-4 gap-2">
            {conversations.slice(0, 5).map(conv => (
              <Tooltip key={conv.id}>
                <TooltipTrigger asChild>
                  <Button
                    variant={currentConversationId === conv.id ? 'secondary' : 'ghost'}
                    size="icon"
                    className="h-9 w-9"
                    onClick={() => onSelectConversation?.(conv.id)}
                  >
                    {conv.type === 'review' ? (
                      <FileText className="h-4 w-4" />
                    ) : (
                      <MessageSquare className="h-4 w-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p className="max-w-xs truncate">{conv.title}</p>
                </TooltipContent>
              </Tooltip>
            ))}
            {conversations.length > 5 && (
              <div className="text-xs text-muted-foreground">
                +{conversations.length - 5}
              </div>
            )}
          </div>
        )}

        {/* 其他页面的占位内容 */}
        {!showConversations && !collapsed && (
          <div className="flex-1 p-4">
            <div className="text-xs text-muted-foreground text-center">
              {currentView === 'graph' && '浏览知识图谱'}
              {currentView === 'projects' && '管理您的项目'}
              {currentView === 'favorites' && '查看收藏内容'}
            </div>
          </div>
        )}
      </div>

      {/* 折叠按钮 */}
      <div className="relative">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-4 -left-3 h-6 w-6 rounded-full border bg-card shadow-sm z-10 hover:bg-muted"
              onClick={onToggleCollapse}
            >
              {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>{collapsed ? '展开侧边栏' : '折叠侧边栏'}</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}
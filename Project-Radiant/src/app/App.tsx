import React, { useEffect, useState } from "react";
import { Dashboard, type Conversation, type Message } from "@/app/components/Dashboard";
import { KnowledgeGraphViewer } from "@/app/components/KnowledgeGraphViewer";
import { UserCenter } from "@/app/components/UserCenter";
import { FavoritesPage } from "@/app/components/FavoritesPage";
import { TutorialDialog } from "@/app/components/TutorialDialog";
import { LeftNavigation } from "@/app/components/LeftNavigation";
import { Login } from "@/app/components/Login";
import { Button } from "@/app/components/ui/button";
import { Avatar, AvatarFallback } from "@/app/components/ui/avatar";
import { LogOut, Settings } from "lucide-react";
import { supabase } from "@/utils/supabase/client";
import { SettingsDialog } from "@/app/components/SettingsDialog";

type ViewType =
  | "dashboard"
  | "graph"
  | "profile"
  | "favorites";

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>("dashboard");
  const [user, setUser] = useState<any>(null);
  const [accessToken, setAccessToken] = useState<string>('');
  const [knowledgeGraphQuery, setKnowledgeGraphQuery] = useState<string>('');
  const [leftNavCollapsed, setLeftNavCollapsed] = useState(false);
  const [fileInputTrigger, setFileInputTrigger] = useState(0);
  const [showTutorial, setShowTutorial] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Lifted state from Dashboard
  const [currentConversationId, setCurrentConversationId] = useState<string | null>('1');
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'Transformer架构原理',
      type: 'chat',
      messages: [
        {
          role: 'user',
          content: '介绍一下Transformer架构的核心原理',
          timestamp: new Date(Date.now() - 3600000)
        },
        {
          role: 'assistant',
          content: 'Transformer架构是一种基于注意力机制的深度学习模型，由Vaswani等人在2017年的论文《Attention is All You Need》中提出。其核心特点包括：\n\n1. **自注意力机制（Self-Attention）**：允许模型在处理序列时关注不同位置的信息\n2. **位置编码（Positional Encoding）**：为序列中的每个位置添加位置信息\n3. **多头注意力（Multi-Head Attention）**：并行运行多个注意力机制\n4. **前馈神经网络（Feed-Forward Network）**：对每个位置独立应用相同的全连接层\n\nTransformer完全抛弃了RNN和CNN，在机器翻译等任务上取得了突破性成果。',
          timestamp: new Date(Date.now() - 3500000),
          relatedQuestions: [
            '什么是自注意力机制？',
            'Transformer与RNN有什么区别？',
            '多头注意力如何工作？'
          ]
        }
      ],
      timestamp: new Date(Date.now() - 3600000)
    }
  ]);

  useEffect(() => {
    // 初始化主题
    initializeTheme();
    // 检查现有会话
    checkSession();
  }, []);

  const initializeTheme = () => {
    if (typeof window === 'undefined') return;
    
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null;
    const root = document.documentElement;
    
    if (savedTheme === 'dark') {
      root.classList.add('dark');
    } else if (savedTheme === 'light') {
      root.classList.remove('dark');
    } else {
      // 系统主题
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  };

  const checkSession = async () => {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (session?.access_token) {
        setAccessToken(session.access_token);
        setUser(session.user);
        
        // 检查用户是否已经看过教程
        const hasSeenTutorial = localStorage.getItem(`tutorial_seen_${session.user.id}`);
        if (!hasSeenTutorial) {
          // 延迟一点显示，让界面先加载完成
          setTimeout(() => {
            setShowTutorial(true);
          }, 1000);
        }
      }
    } catch (error) {
      console.error('检查会话错误:', error);
    }
  };

  const handleLoginSuccess = (token: string, userData: any) => {
    setAccessToken(token);
    setUser(userData);
    
    // 检查用户是否已经看过教程
    const hasSeenTutorial = localStorage.getItem(`tutorial_seen_${userData.id}`);
    if (!hasSeenTutorial) {
      // 延迟一点显示，让登录界面先消失
      setTimeout(() => {
        setShowTutorial(true);
      }, 500);
    }
  };

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
      setAccessToken('');
      setUser(null);
      setCurrentView('dashboard');
    } catch (error) {
      console.error('登出错误:', error);
    }
  };

  const handleGenerateKnowledgeGraph = (query: string) => {
    setKnowledgeGraphQuery(query);
    setCurrentView('graph');
  };

  const handleApplySuggestion = (comment: any) => {
    console.log('应用修改建议:', comment);
    
    // 构建详细的修改建议消息
    const message = comment.originalText 
      ? `✅ 已标记修改建议\n\n📝 原文：\n"${comment.originalText}"\n\n✨ 建议修改为：\n"${comment.suggestion}"\n\n💡 修改理由：${comment.text}\n\n${comment.type === 'grammar' ? '📖 类型：语法优化' : 
         comment.type === 'clarity' ? '🔍 类型：清晰度提升' : 
         comment.type === 'methodology' ? '🔬 类型：方法论完善' : 
         '📐 类型：结构调整'}\n\n建议已应用到编辑器中。`
      : `✅ 已记录修改建议\n\n✨ 建议：\n"${comment.suggestion}"\n\n💡 说明：${comment.text}\n\n建议已应用到编辑器中。`;
    
    alert(message);
  };

  const handleNewConversation = () => {
    setCurrentConversationId(null);
    if (currentView !== 'dashboard') {
      setCurrentView('dashboard');
    }
  };

  const handleDeleteConversation = (id: string) => {
    const newConversations = conversations.filter(c => c.id !== id);
    setConversations(newConversations);
    if (currentConversationId === id) {
      setCurrentConversationId(newConversations[0]?.id || null);
    }
  };

  const handleClearAllConversations = () => {
    if (conversations.length === 0) return;
    setConversations([]);
    setCurrentConversationId(null);
  };


  const handleFileProcessed = () => {
    // 文件处理完成后，重置trigger
    setFileInputTrigger(0);
  };

  // 如果未认证，显示登录界面
  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const getInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* 顶部导航栏 */}
      <header className="h-16 bg-card border-b px-6 flex items-center justify-between shadow-sm z-20 relative">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center cursor-pointer"
              onClick={() => setCurrentView('dashboard')}
              title="返回智能助手"
            >
              <div className="h-4 w-4 border-2 border-white rounded-sm" />
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E] bg-clip-text text-transparent cursor-pointer"
              onClick={() => setCurrentView('dashboard')}
            >
              Radiant
            </h1>
            <span className="text-xs text-muted-foreground">
              学术研究协作平台
            </span>
          </div>
          
          {/* 当前页面指示器 */}
          {currentView !== 'dashboard' && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>/</span>
              <span className="font-medium text-[#0F3B6C]">
                {currentView === 'graph' && '知识图谱'}
                {currentView === 'favorites' && '收藏夹'}
                {currentView === 'profile' && '用户中心'}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            className="flex items-center gap-2 hover:bg-accent"
            onClick={() => setCurrentView('profile')}
          >
            <Avatar className="h-7 w-7 border-2 border-[#0F3B6C]">
              <AvatarFallback className="bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] text-white text-xs">
                {getInitials(user?.user_metadata?.name || user?.email || 'User')}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm">{user?.user_metadata?.name || user?.email}</span>
          </Button>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => setShowSettings(true)}
            title="设置"
            className="hover:bg-accent"
          >
            <Settings className="h-5 w-5" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon"
            onClick={handleLogout}
            title="退出登录"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧导航栏 - 全局存在 */}
        <LeftNavigation
          collapsed={leftNavCollapsed}
          onToggleCollapse={() => setLeftNavCollapsed(!leftNavCollapsed)}
          currentView={currentView}
          onNavigate={setCurrentView}
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={setCurrentConversationId}
          onDeleteConversation={handleDeleteConversation}
          onNewConversation={handleNewConversation}
          onClearAllConversations={handleClearAllConversations}
          showConversations={currentView === 'dashboard'}
        />

        {/* 中央工作区 */}
        <main className="flex-1 overflow-hidden relative">
          {currentView === "dashboard" && (
            <Dashboard 
              userToken={accessToken} 
              onGenerateKnowledgeGraph={handleGenerateKnowledgeGraph}
              onNavigate={setCurrentView}
              fileUploadTrigger={fileInputTrigger}
              conversations={conversations}
              setConversations={setConversations}
              currentConversationId={currentConversationId}
              setCurrentConversationId={setCurrentConversationId}
              onFileProcessed={handleFileProcessed}
              onOpenTutorial={() => setShowTutorial(true)}
            />
          )}
          {currentView === "graph" && <KnowledgeGraphViewer initialQuery={knowledgeGraphQuery} />}
          {currentView === "profile" && (
            <UserCenter 
              userToken={accessToken} 
              user={user} 
              onOpenTutorial={() => setShowTutorial(true)}
            />
          )}
          {currentView === "favorites" && <FavoritesPage />}
        </main>
      </div>

      {/* 教程对话框 */}
      {user && (
        <TutorialDialog
          open={showTutorial}
          onClose={() => {
            setShowTutorial(false);
            // 标记用户已看过教程
            if (user?.id) {
              localStorage.setItem(`tutorial_seen_${user.id}`, 'true');
            }
          }}
          onSkip={() => {
            setShowTutorial(false);
            // 标记用户已看过教程
            if (user?.id) {
              localStorage.setItem(`tutorial_seen_${user.id}`, 'true');
            }
          }}
        />
      )}

      {/* 设置对话框 */}
      <SettingsDialog
        open={showSettings}
        onOpenChange={setShowSettings}
      />
    </div>
  );
}
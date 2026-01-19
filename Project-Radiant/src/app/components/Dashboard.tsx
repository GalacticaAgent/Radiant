import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from '@/app/components/ui/card';
import { Input } from '@/app/components/ui/input';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { 
  Send, 
  Sparkles, 
  Loader2, 
  FileText,
  Upload,
  UserCheck,
  Paperclip,
  Brain,
  Lightbulb,
  CheckCircle2,
  FolderOpen,
  Plus,
  Edit,
  Trash2,
  Clock,
  Users,
  Progress
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import { Avatar, AvatarFallback } from '@/app/components/ui/avatar';
import { NewProjectDialog } from '@/app/components/NewProjectDialog';
import { ProjectsListDialog } from '@/app/components/ProjectsListDialog';

export interface Project {
  id: number;
  name: string;
  description: string;
  papers: number;
  members: number;
  progress: number;
  lastUpdate: string;
  status: 'active' | 'review';
  template: string;
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  relatedQuestions?: string[];
  reviewers?: any[];
  fileInfo?: {
    name: string;
    size: string;
  };
  reviewComments?: ReviewComment[];
  paperContent?: string;
  projects?: Project[];
  projectAction?: 'list' | 'create' | 'detail' | 'edit' | 'delete';
  projectData?: any;
}

interface ReviewComment {
  id: string;
  paragraph: string;
  originalText: string;
  suggestion: string;
  type: 'grammar' | 'clarity' | 'methodology' | 'structure';
  severity: 'high' | 'medium' | 'low';
  startIndex: number;
  endIndex: number;
}

interface Reviewer {
  id: string;
  name: string;
  avatar: string;
  expertise: string;
  strictness: string;
  style: string;
  description: string;
  institution: string;
  color: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  timestamp: Date;
  type?: 'chat' | 'review';
}

interface DashboardProps {
  userToken?: string;
  onGenerateKnowledgeGraph?: (query: string) => void;
  onNavigate?: (view: string) => void;
  fileUploadTrigger?: number;
  conversations: Conversation[];
  setConversations: (conversations: Conversation[]) => void;
  currentConversationId: string | null;
  setCurrentConversationId: (id: string | null) => void;
  onFileProcessed?: () => void;
  onOpenTutorial?: () => void;
}

export function Dashboard({ 
  userToken, 
  onGenerateKnowledgeGraph, 
  onNavigate, 
  fileUploadTrigger,
  conversations,
  setConversations,
  currentConversationId,
  setCurrentConversationId,
  onFileProcessed,
  onOpenTutorial
}: DashboardProps) {
  
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [showReviewMode, setShowReviewMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previousTriggerRef = useRef<number>(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showReviewerDialog, setShowReviewerDialog] = useState(false);
  const [selectedReviewer, setSelectedReviewer] = useState<Reviewer | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [showNewProjectDialog, setShowNewProjectDialog] = useState(false);
  const [showProjectsListDialog, setShowProjectsListDialog] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});
  const [showQuestionsList, setShowQuestionsList] = useState(false);
  const [scrollbarHovered, setScrollbarHovered] = useState(false);
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [highlightedMessageIndex, setHighlightedMessageIndex] = useState<number | null>(null);
  
  // 项目管理状态
  const [projects, setProjects] = useState<Project[]>([
    {
      id: 1,
      name: 'Transformer 架构研究',
      description: '深入研究 Transformer 架构及其变体',
      papers: 15,
      members: 3,
      progress: 65,
      lastUpdate: '2小时前',
      status: 'active',
      template: 'IEEE 会议论文'
    },
    {
      id: 2,
      name: '大语言模型综述',
      description: '整理和分析大语言模型的最新进展',
      papers: 28,
      members: 5,
      progress: 42,
      lastUpdate: '1天前',
      status: 'active',
      template: 'ACM 期刊论文'
    },
    {
      id: 3,
      name: 'NLP 应用案例分析',
      description: '收集各行业 NLP 应用的成功案例',
      papers: 22,
      members: 2,
      progress: 88,
      lastUpdate: '3天前',
      status: 'review',
      template: '文献综述'
    }
  ]);

  const currentConversation = conversations.find(c => c.id === currentConversationId);

  // Reset local state when conversation changes
  useEffect(() => {
    if (!currentConversationId) {
      setInputValue('');
      setShowReviewMode(false);
    } else {
      const conv = conversations.find(c => c.id === currentConversationId);
      if (conv) {
        setShowReviewMode(conv.type === 'review');
      }
    }
  }, [currentConversationId, conversations]);

  // 监听外部文件上传触发
  useEffect(() => {
    // 只有当trigger值真正变化时才执行，避免重复触发
    if (fileUploadTrigger && fileUploadTrigger > 0 && fileUploadTrigger !== previousTriggerRef.current) {
      previousTriggerRef.current = fileUploadTrigger;
      handleFileUploadFromReview();
    }
  }, [fileUploadTrigger]);

  const handleFileUploadFromReview = () => {
    // 从审稿页面返回后，创建一个审稿对话
    setShowReviewMode(true);
    
    const fileMessage: Message = {
      role: 'system',
      content: '已接收到您上传的论文文件',
      timestamp: new Date(),
      fileInfo: {
        name: 'research_paper.pdf',
        size: '2.4 MB'
      }
    };

    // 创建新的审稿对话
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: '论文审稿 - ' + new Date().toLocaleDateString(),
      type: 'review',
      messages: [fileMessage],
      timestamp: new Date()
    };
    
    setConversations([newConversation, ...conversations]);
    setCurrentConversationId(newConversation.id);

    // 模拟AI生成审稿人选项
    setTimeout(() => {
      const reviewerMessage: Message = {
        role: 'assistant',
        content: '文件已成功上传！我为您准备了两位审稿人，请选择其中一位开始审稿：',
        timestamp: new Date(),
        reviewers: [
          {
            id: 'reviewer-a',
            name: '审稿人 A',
            avatar: '👨‍🔬',
            expertise: '深度学习、自然语言处理',
            style: '严格且注重技术细节',
            institution: 'MIT CSAIL'
          },
          {
            id: 'reviewer-b',
            name: '审稿人 B',
            avatar: '👩‍🎓',
            expertise: '机器学习、计算机视觉',
            style: '关注创新性和实用价值',
            institution: 'Stanford AI Lab'
          }
        ]
      };

      setConversations(prevConvs => 
        prevConvs.map(conv => 
          conv.id === newConversation.id
            ? { ...conv, messages: [...conv.messages, reviewerMessage] }
            : conv
        )
      );
      
      // 通知App.tsx文件已处理完成
      if (onFileProcessed) {
        onFileProcessed();
      }
    }, 1000);
  };

  // 处理项目管理命令
  const handleProjectCommand = (question: string): { content: string; projects?: Project[]; projectAction?: string; projectData?: any; openDialog?: 'projects' | 'newProject' } => {
    const lowerQuestion = question.toLowerCase();
    
    // 列出所有项目 - 打开弹窗
    if (lowerQuestion.includes('项目列表') || lowerQuestion.includes('查看项目') || lowerQuestion.includes('所有项目') || lowerQuestion.includes('我的项目')) {
      // 延迟打开弹窗，避免在消息发送过程中打开
      setTimeout(() => {
        setShowProjectsListDialog(true);
      }, 100);
      return {
        content: `正在打开项目列表...`,
        openDialog: 'projects'
      };
    }
    
    // 创建项目
    if (lowerQuestion.includes('创建项目') || lowerQuestion.includes('新建项目') || lowerQuestion.includes('添加项目')) {
      // 尝试从问题中提取项目名称
      const nameMatch = question.match(/[创建新建添加]项目[：:：]?\s*([^，,。.]+)/);
      const projectName = nameMatch ? nameMatch[1].trim() : `新项目 ${projects.length + 1}`;
      
      const newProject: Project = {
        id: Math.max(...projects.map(p => p.id), 0) + 1,
        name: projectName,
        description: `基于模板创建的新项目`,
        papers: 0,
        members: 1,
        progress: 0,
        lastUpdate: '刚刚',
        status: 'active',
        template: '空白项目'
      };
      
      setProjects([newProject, ...projects]);
      
      return {
        content: `✅ 已成功创建项目"${projectName}"！\n\n项目信息：\n- 名称：${projectName}\n- 状态：进行中\n- 进度：0%\n\n您可以通过"查看项目"或"项目列表"来管理您的项目。`,
        projects: [newProject],
        projectAction: 'create'
      };
    }
    
    // 查看特定项目详情
    const projectNameMatch = question.match(/查看项目[：:：]?\s*([^，,。.]+)|项目[：:：]?\s*([^，,。.]+)\s*的详情/);
    if (projectNameMatch) {
      const searchName = (projectNameMatch[1] || projectNameMatch[2]).trim();
      const project = projects.find(p => p.name.includes(searchName) || searchName.includes(p.name));
      
      if (project) {
        return {
          content: `📁 项目详情：${project.name}\n\n${project.description}\n\n📊 统计信息：\n- 文献数量：${project.papers} 篇\n- 成员数量：${project.members} 位\n- 完成进度：${project.progress}%\n- 状态：${project.status === 'active' ? '进行中' : '审阅中'}\n- 模板：${project.template}\n- 最后更新：${project.lastUpdate}`,
          projects: [project],
          projectAction: 'detail',
          projectData: project
        };
      } else {
        return {
          content: `❌ 未找到名为"${searchName}"的项目。请使用"项目列表"查看所有项目。`
        };
      }
    }
    
    // 删除项目
    const deleteMatch = question.match(/删除项目[：:：]?\s*([^，,。.]+)|删除[：:：]?\s*([^，,。.]+)\s*项目/);
    if (deleteMatch) {
      const searchName = (deleteMatch[1] || deleteMatch[2]).trim();
      const project = projects.find(p => p.name.includes(searchName) || searchName.includes(p.name));
      
      if (project) {
        setProjects(projects.filter(p => p.id !== project.id));
        return {
          content: `✅ 已成功删除项目"${project.name}"。`
        };
      } else {
        return {
          content: `❌ 未找到名为"${searchName}"的项目。`
        };
      }
    }
    
    // 编辑项目
    const editMatch = question.match(/编辑项目[：:：]?\s*([^，,。.]+)|修改项目[：:：]?\s*([^，,。.]+)/);
    if (editMatch) {
      const searchName = (editMatch[1] || editMatch[2]).trim();
      const project = projects.find(p => p.name.includes(searchName) || searchName.includes(p.name));
      
      if (project) {
        return {
          content: `📝 编辑项目"${project.name}"\n\n当前信息：\n- 名称：${project.name}\n- 描述：${project.description}\n- 进度：${project.progress}%\n- 状态：${project.status === 'active' ? '进行中' : '审阅中'}\n\n您可以说"将${project.name}的进度改为XX%"或"将${project.name}的描述改为XXX"来更新项目信息。`,
          projects: [project],
          projectAction: 'edit',
          projectData: project
        };
      }
    }
    
    // 更新项目进度
    const progressMatch = question.match(/(将|把)?\s*([^的]+)\s*的进度(改为|设置为|更新为)?\s*(\d+)%/);
    if (progressMatch) {
      const projectName = progressMatch[2].trim();
      const progress = parseInt(progressMatch[4]);
      const project = projects.find(p => p.name.includes(projectName) || projectName.includes(p.name));
      
      if (project && progress >= 0 && progress <= 100) {
        const updatedProject = { ...project, progress, lastUpdate: '刚刚' };
        setProjects(projects.map(p => p.id === project.id ? updatedProject : p));
        return {
          content: `✅ 已更新项目"${project.name}"的进度为 ${progress}%。`,
          projects: [updatedProject],
          projectAction: 'edit'
        };
      }
    }
    
    // 更新项目描述
    const descMatch = question.match(/(将|把)?\s*([^的]+)\s*的描述(改为|设置为|更新为)?\s*([^，,。.]+)/);
    if (descMatch) {
      const projectName = descMatch[2].trim();
      const newDesc = descMatch[4].trim();
      const project = projects.find(p => p.name.includes(projectName) || projectName.includes(p.name));
      
      if (project) {
        const updatedProject = { ...project, description: newDesc, lastUpdate: '刚刚' };
        setProjects(projects.map(p => p.id === project.id ? updatedProject : p));
        return {
          content: `✅ 已更新项目"${project.name}"的描述。`,
          projects: [updatedProject],
          projectAction: 'edit'
        };
      }
    }
    
    return { content: '' };
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    // 如果没有当前对话，创建新对话
    if (!currentConversationId) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: inputValue.slice(0, 30) + (inputValue.length > 30 ? '...' : ''),
        type: showReviewMode ? 'review' : 'chat',
        messages: [userMessage],
        timestamp: new Date()
      };
      setConversations([newConversation, ...conversations]);
      setCurrentConversationId(newConversation.id);
      
      // Simulate AI Response for new conversation
      setInputValue('');
      setLoading(true);
      setTimeout(() => {
        const projectResult = handleProjectCommand(inputValue);
        const assistantMessage: Message = {
          role: 'assistant',
          content: projectResult.content || generateAIResponse(inputValue, showReviewMode),
          timestamp: new Date(),
          relatedQuestions: showReviewMode ? undefined : generateRelatedQuestions(inputValue),
          projects: projectResult.projects,
          projectAction: projectResult.projectAction as any,
          projectData: projectResult.projectData
        };
        
        // Update the new conversation in the list
        setConversations([
          { ...newConversation, messages: [...newConversation.messages, assistantMessage] },
          ...conversations
        ]);
        setLoading(false);
      }, 1500);

    } else {
      // 更新现有对话
      const updatedConversations = conversations.map(conv => 
        conv.id === currentConversationId
          ? { ...conv, messages: [...conv.messages, userMessage], timestamp: new Date() }
          : conv
      );
      setConversations(updatedConversations);
      
      setInputValue('');
      setLoading(true);

      // 模拟AI回复
      setTimeout(() => {
        const projectResult = handleProjectCommand(inputValue);
        const assistantMessage: Message = {
          role: 'assistant',
          content: projectResult.content || generateAIResponse(inputValue, showReviewMode),
          timestamp: new Date(),
          relatedQuestions: showReviewMode ? undefined : generateRelatedQuestions(inputValue),
          projects: projectResult.projects,
          projectAction: projectResult.projectAction as any,
          projectData: projectResult.projectData
        };

        setConversations(conversations.map(conv => 
          conv.id === currentConversationId
            ? { ...conv, messages: [...conv.messages, userMessage, assistantMessage] }
            : conv
        ));
        setLoading(false);
      }, 1500);
    }
  };

  const reviewers: Reviewer[] = [
    {
      id: '1',
      name: '审稿人 A',
      avatar: 'A',
      expertise: 'NLP, 机器学习',
      strictness: '严格',
      style: '注重理论深度',
      description: '资深教授，关注理论创新和严谨性',
      institution: 'Stanford University',
      color: '#FF6B6B'
    },
    {
      id: '2',
      name: '审稿人 B',
      avatar: 'B',
      expertise: '深度学习, 计算机视觉',
      strictness: '温和',
      style: '注重实用性',
      description: '工业界专家，关注实际应用价值',
      institution: 'Google Research',
      color: '#4ECDC4'
    },
    {
      id: '3',
      name: '审稿人 C',
      avatar: 'C',
      expertise: '强化学习, 优化算法',
      strictness: '中等',
      style: '平衡理论与应用',
      description: '年轻学者，追求创新与实用的平衡',
      institution: 'MIT CSAIL',
      color: '#95E1D3'
    }
  ];

  // 模拟论文内容
  const mockPaperContent = `Abstract

This paper presents a novel approach to natural language processing using deep learning techniques. We propose a new method that combines transformer architecture with attention mechanisms to improve performance on various NLP tasks.

Introduction

Deep learning has revolutionized the field of natural language processing in recent years. Recent works have shown significant improvements in tasks such as machine translation, text classification, and question answering.

Methodology

We use standard training methods to train our model. Our experiments show that the proposed method achieves state-of-the-art results on several benchmark datasets.

Results

Figure 1 shows the results of our experiments. The model demonstrates superior performance compared to baseline methods.

Conclusion

In this paper, we have presented a new approach to NLP. The experimental results validate the effectiveness of our method.`;

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setShowReviewMode(true);

    // 如果没有当前对话，创建新对话
    if (!currentConversationId) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: `审稿：${file.name}`,
        type: 'review',
        messages: [
          {
            role: 'system',
            content: `已上传文档：${file.name}`,
            timestamp: new Date(),
            fileInfo: {
              name: file.name,
              size: (file.size / 1024 / 1024).toFixed(2) + ' MB'
            }
          }
        ],
        timestamp: new Date()
      };

      setConversations([newConversation, ...conversations]);
      setCurrentConversationId(newConversation.id);
    } else {
      // 更新现有对话
      const updatedConversations = conversations.map(conv => 
        conv.id === currentConversationId
          ? {
              ...conv,
              messages: [
                ...conv.messages,
                {
                  role: 'system',
                  content: `已上传文档：${file.name}`,
                  timestamp: new Date(),
                  fileInfo: {
                    name: file.name,
                    size: (file.size / 1024 / 1024).toFixed(2) + ' MB'
                  }
                }
              ]
            }
          : conv
      );
      setConversations(updatedConversations);
    }

    // 添加助手回复
    setTimeout(() => {
      const assistantMessage: Message = {
        role: 'assistant',
        content: '文件已成功上传！您可以点击"模拟审稿"按钮开始审稿流程。',
        timestamp: new Date()
      };

      setConversations(prev => prev.map(conv => 
        conv.id === (currentConversationId || Date.now().toString())
          ? { ...conv, messages: [...conv.messages, assistantMessage] }
          : conv
      ));
    }, 500);
  };

  const handleSelectReviewer = (reviewer: Reviewer) => {
    setSelectedReviewer(reviewer);
    setShowReviewerDialog(false);
    setIsReviewing(true);

    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content: `已选择审稿人: ${reviewer.name}`,
      timestamp: new Date()
    };

    setConversations(prev => prev.map(conv => 
      conv.id === currentConversationId
        ? { ...conv, messages: [...conv.messages, userMessage] }
        : conv
    ));

    // 模拟审稿过程
    setTimeout(() => {
      const comments: ReviewComment[] = [
        {
          id: '1',
          paragraph: 'Abstract',
          originalText: 'We propose a new method...',
          suggestion: '建议扩展摘要，增加研究背景、主要贡献和实验结果的简要说明，使读者能够快速了解论文的核心价值。',
          type: 'structure',
          severity: 'high',
          startIndex: 0,
          endIndex: 50
        },
        {
          id: '2',
          paragraph: 'Methodology',
          originalText: 'We use standard training methods',
          suggestion: '建议增加消融实验(Ablation Study)，分析各个模块对最终性能的贡献，这将大大增强论文的说服力。同时需要详细说明训练参数和实验设置。',
          type: 'methodology',
          severity: 'high',
          startIndex: 200,
          endIndex: 250
        },
        {
          id: '3',
          paragraph: 'Results',
          originalText: 'Figure 1 shows the results',
          suggestion: '建议在图表标题中明确说明实验设置、对比基线和主要发现，避免读者需要反复查阅正文。',
          type: 'clarity',
          severity: 'medium',
          startIndex: 300,
          endIndex: 330
        },
        {
          id: '4',
          paragraph: 'Introduction',
          originalText: 'Recent works have...',
          suggestion: '建议扩展相关工作部分，明确指出本研究与现有方法的区别和优势，突出创新点。',
          type: 'structure',
          severity: 'medium',
          startIndex: 100,
          endIndex: 150
        },
        {
          id: '5',
          paragraph: 'Conclusion',
          originalText: 'The experimental results validate',
          suggestion: '建议统一术语使用，在首次出现时给出全称和缩写，后续保持一致。',
          type: 'grammar',
          severity: 'low',
          startIndex: 400,
          endIndex: 450
        }
      ];

      const reviewMessage: Message = {
        role: 'assistant',
        content: `${reviewer.name} 已完成审稿，共发现 ${comments.length} 处需要修改的地方。`,
        timestamp: new Date(),
        reviewComments: comments,
        paperContent: mockPaperContent
      };

      setConversations(prev => prev.map(conv => 
        conv.id === currentConversationId
          ? { ...conv, messages: [...conv.messages, reviewMessage] }
          : conv
      ));

      setIsReviewing(false);
    }, 3000);
  };


  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return '';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'high': return '重要';
      case 'medium': return '中等';
      case 'low': return '建议';
      default: return '';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'grammar': return '语法';
      case 'clarity': return '清晰度';
      case 'methodology': return '方法论';
      case 'structure': return '结构';
      default: return '';
    }
  };

  // 渲染带标红的论文内容
  const renderHighlightedPaper = (paperContent: string, comments: ReviewComment[]) => {
    if (!paperContent || comments.length === 0) {
      return <div className="text-sm text-muted-foreground">{paperContent || '暂无内容'}</div>;
    }

    // 按位置排序评论
    const sortedComments = [...comments].sort((a, b) => a.startIndex - b.startIndex);
    
    let result: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedComments.forEach((comment, index) => {
      // 添加标红前的文本
      if (comment.startIndex > lastIndex) {
        result.push(
          <span key={`text-${index}`}>
            {paperContent.substring(lastIndex, comment.startIndex)}
          </span>
        );
      }

      // 添加标红的文本
      result.push(
        <span
          key={`highlight-${comment.id}`}
          className="bg-red-200 text-red-900 font-medium cursor-pointer relative group"
          title={`${comment.suggestion}`}
        >
          {paperContent.substring(comment.startIndex, comment.endIndex)}
          <span className="absolute bottom-full left-0 mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-10">
            <div className="font-semibold mb-1">{getSeverityLabel(comment.severity)} - {getTypeLabel(comment.type)}</div>
            <div>{comment.suggestion}</div>
          </span>
        </span>
      );

      lastIndex = comment.endIndex;
    });

    // 添加剩余文本
    if (lastIndex < paperContent.length) {
      result.push(
        <span key="text-end">
          {paperContent.substring(lastIndex)}
        </span>
      );
    }

    return <div className="text-sm whitespace-pre-wrap leading-relaxed">{result}</div>;
  };

  const generateAIResponse = (question: string, isReviewMode: boolean): string => {
    if (isReviewMode) {
      return '收到您的问题，我会基于之前的审稿意见为您提供更详细的建议...';
    }

    // 检查是否是项目管理命令
    const projectResult = handleProjectCommand(question);
    if (projectResult.content) {
      return projectResult.content;
    }

    // 简单的响应生成逻辑
    if (question.toLowerCase().includes('transformer')) {
      return 'Transformer是一种基于自注意力机制的深度学习架构，在自然语言处理领域取得了巨大成功。它的核心创新在于完全依赖注意力机制，摒弃了传统的循环和卷积结构。\n\n主要组成部分：\n1. 编码器-解码器架构\n2. 多头自注意力层\n3. 位置编码\n4. 残差连接和层归一化\n\n如果您想深入了解，我可以为您生成相关的知识图谱，展示Transformer与相关技术的关系。';
    } else if (question.toLowerCase().includes('bert')) {
      return 'BERT（Bidirectional Encoder Representations from Transformers）是Google在2018年提出的预训练语言模型。它的主要特点是：\n\n1. **双向编码**：同时考虑上下文信息\n2. **掩码语言模型**：随机遮蔽部分词汇进行预训练\n3. **下一句预测**：学习句子间的关系\n\nBERT在多个NLP任务上刷新了记录，开启了预训练-微调的范式。';
    } else if (question.toLowerCase().includes('论文') || question.toLowerCase().includes('摘要')) {
      return '撰写高质量学术论文摘要的关键要素：\n\n1. **背景与动机**：简要说明研究背景和重要性\n2. **问题陈述**：明确指出要解决的具体问题\n3. **方法概述**：简述采用的研究方法或技术\n4. **主要发现**：突出最重要的研究结果\n5. **结论与意义**：说明研究的学术价值和实际应用\n\n建议长度：150-250词，语言简洁准确，避免使用缩写和引用。';
    }
    return `关于"${question}"的问题，我为您整理了以下信息：\n\n这是一个很好的研究方向。我建议您：\n1. 查阅相关领域的最新文献\n2. 使用知识图谱探索相关概念\n3. 参考领域内权威学者的观点\n\n您可以告诉我更具体的需求，我会提供更详细的帮助。`;
  };

  const generateRelatedQuestions = (question: string): string[] => {
    if (question.toLowerCase().includes('transformer')) {
      return [
        '什么是自注意力机制？',
        'Transformer与RNN有什么区别？',
        'BERT和GPT都基于Transformer吗？'
      ];
    } else if (question.toLowerCase().includes('bert')) {
      return [
        'BERT的预训练任务有哪些？',
        '如何微调BERT模型？',
        'BERT与GPT的主要区别是什么？'
      ];
    } else if (question.toLowerCase().includes('论文')) {
      return [
        '如何撰写论文的引言部分？',
        '学术论文的结构应该如何安排？',
        '如何提高论文的引用率？'
      ];
    }
    return [
      '能否提供更多相关资料？',
      '这个领域有哪些经典论文？',
      '如何在实践中应用这些知识？'
    ];
  };

  const handleStartReview = () => {
    if (selectedFile) {
      // 如果已有文件，直接打开审稿人选择对话框
      setShowReviewerDialog(true);
    } else {
      // 如果没有文件，先触发文件上传
      setShowReviewMode(true);
      fileInputRef.current?.click();
    }
  };

  // 处理创建项目
  const handleCreateProject = (projectData: any) => {
    const newProject: Project = {
      id: Math.max(...projects.map(p => p.id), 0) + 1,
      name: projectData.name,
      description: `基于 ${projectData.templateName} 模板创建`,
      papers: 0,
      members: 1,
      progress: 0,
      lastUpdate: '刚刚',
      status: 'active',
      template: projectData.templateName
    };

    setProjects([newProject, ...projects]);
    setShowNewProjectDialog(false);
  };

  // 处理滚动条悬停显示问题列表
  useEffect(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    if (scrollbarHovered) {
      // 悬停1.5秒后显示问题列表
      hoverTimeoutRef.current = setTimeout(() => {
        setShowQuestionsList(true);
        // 显示后，5秒后自动隐藏（如果鼠标不在滚动条或问题列表上）
        hoverTimeoutRef.current = setTimeout(() => {
          if (!scrollbarHovered) {
            setShowQuestionsList(false);
          }
        }, 5000);
      }, 1500);
    } else {
      // 鼠标离开滚动条区域时，如果问题列表已显示，等待5秒后再隐藏
      if (showQuestionsList) {
        hoverTimeoutRef.current = setTimeout(() => {
          setShowQuestionsList(false);
        }, 5000);
      }
    }

    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, [scrollbarHovered]);

  // 监听滚动条区域的鼠标事件
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const scrollArea = scrollAreaRef.current;
      if (!scrollArea) return;

      const rect = scrollArea.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const scrollAreaWidth = rect.width;
      
      // 检测鼠标是否在右侧滚动条区域（右侧 30px 内）
      if (mouseX > scrollAreaWidth - 30) {
        setScrollbarHovered(true);
      } else {
        setScrollbarHovered(false);
      }
    };

    const handleMouseLeave = () => {
      setScrollbarHovered(false);
    };

    const scrollArea = scrollAreaRef.current;
    if (scrollArea) {
      scrollArea.addEventListener('mousemove', handleMouseMove);
      scrollArea.addEventListener('mouseleave', handleMouseLeave);
      return () => {
        scrollArea.removeEventListener('mousemove', handleMouseMove);
        scrollArea.removeEventListener('mouseleave', handleMouseLeave);
      };
    }
  }, [currentConversation]);

  return (
    <div className="h-full flex flex-col bg-background">
      {/* 隐藏的文件上传input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        className="hidden"
        onChange={handleFileUpload}
      />

      {/* 头部 */}
      <div className="h-16 bg-card border-b px-6 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center">
            {showReviewMode ? <FileText className="h-4 w-4 text-white" /> : <Sparkles className="h-4 w-4 text-white" />}
          </div>
          <div>
            <h2 className="font-semibold">{showReviewMode ? '模拟审稿' : '智能协助助手'}</h2>
            <p className="text-xs text-muted-foreground">
              {showReviewMode ? '基于真实学者背景的智能审稿' : '为您的学术研究提供智能支持'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* 项目管理入口 */}
          {!showReviewMode && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowProjectsListDialog(true)}
                className="flex items-center gap-2"
              >
                <FolderOpen className="h-4 w-4" />
                查看项目
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={() => setShowNewProjectDialog(true)}
                className="bg-[#0F3B6C] hover:bg-[#0a2945] text-white flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                创建项目
              </Button>
            </>
          )}
          {showReviewMode && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mr-2 h-4 w-4" />
              重新上传
            </Button>
          )}
        </div>
      </div>

      {/* 对话内容区 */}
      <div className="flex-1 overflow-hidden relative">
        {/* 中间对话内容 */}
        <div className="flex-1 overflow-hidden relative h-full" ref={scrollAreaRef}>
          <ScrollArea className="h-full px-6">
            {currentConversation && currentConversation.messages.length > 0 ? (
              <div className="max-w-4xl mx-auto py-6 space-y-6">
              {currentConversation.messages.map((message, index) => (
                <div 
                  key={index} 
                  ref={(el) => { messageRefs.current[index] = el; }}
                  className={`transition-all duration-500 ${
                    highlightedMessageIndex === index 
                      ? 'ring-4 ring-blue-300 ring-offset-2 rounded-lg bg-blue-50/30' 
                      : ''
                  }`}
                >
                {/* 系统消息（件上传） */}
                {message.role === 'system' && message.fileInfo && (
                  <div className="flex justify-center">
                    <Card className="px-4 py-3 bg-accent border-[#0F3B6C]">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-[#0F3B6C] rounded-lg flex items-center justify-center">
                          <FileText className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <div className="text-sm font-medium">{message.fileInfo.name}</div>
                          <div className="text-xs text-muted-foreground">{message.fileInfo.size}</div>
                        </div>
                      </div>
                    </Card>
                  </div>
                )}

                {/* 用户消息 */}
                {message.role === 'user' && (
                  <div className="flex justify-end">
                    <div className={`max-w-[80%] rounded-2xl px-4 py-3 bg-[#0F3B6C] text-white transition-all duration-300 ${
                      highlightedMessageIndex === index ? 'ring-4 ring-blue-400 ring-offset-2 shadow-2xl scale-105' : ''
                    }`}>
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      <div className="text-xs mt-2 text-blue-100">
                        {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                )}

                {/* AI消息 */}
                {message.role === 'assistant' && (
                  <>
                    <div className="flex justify-start">
                      <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-card border shadow-sm">
                        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                        <div className="text-xs mt-2 text-muted-foreground">
                          {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>

                    {/* 项目列表渲染 */}
                    {message.projects && message.projects.length > 0 && (
                      <div className="mt-4 space-y-3">
                        {message.projects.map((project) => (
                          <Card key={project.id} className="p-4 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-start gap-3 flex-1">
                                <div className="h-10 w-10 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center flex-shrink-0">
                                  <FolderOpen className="h-5 w-5 text-white" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h3 className="font-semibold mb-1 text-base">{project.name}</h3>
                                  <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{project.description}</p>
                                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                      <FileText className="h-3 w-3" />
                                      <span>{project.papers} 篇文献</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <Users className="h-3 w-3" />
                                      <span>{project.members} 位成员</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <Clock className="h-3 w-3" />
                                      <span>{project.lastUpdate}</span>
                                    </div>
                                  </div>
                                </div>
                                <Badge variant={project.status === 'active' ? 'default' : 'secondary'} className="ml-2">
                                  {project.status === 'active' ? '进行中' : '审阅中'}
                                </Badge>
                              </div>
                            </div>
                            
                            <div className="mt-3">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-muted-foreground">完成进度</span>
                                <span className="font-medium">{project.progress}%</span>
                              </div>
                              <div className="w-full bg-muted rounded-full h-2">
                                <div 
                                  className="bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E] h-2 rounded-full transition-all"
                                  style={{ width: `${project.progress}%` }}
                                />
                              </div>
                            </div>

                            <div className="mt-3 pt-3 border-t flex gap-2">
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="flex-1 text-xs"
                                onClick={() => setInputValue(`查看项目：${project.name}`)}
                              >
                                查看详情
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="flex-1 text-xs"
                                onClick={() => setInputValue(`编辑项目：${project.name}`)}
                              >
                                编辑
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="text-xs text-red-600 hover:text-red-700 hover:border-red-300"
                                onClick={() => {
                                  if (confirm(`确定要删除项目"${project.name}"吗？`)) {
                                    setInputValue(`删除项目：${project.name}`);
                                    handleSendMessage();
                                  }
                                }}
                              >
                                <Trash2 className="h-3 w-3 mr-1" />
                                删除
                              </Button>
                            </div>
                          </Card>
                        ))}
                      </div>
                    )}

                    {/* 审稿结果 - 标红的论文内容和修改意见 */}
                    {message.reviewComments && message.reviewComments.length > 0 && message.paperContent && (
                      <div className="mt-4 space-y-4">
                        <Card className="border-2">
                          <CardContent className="p-6">
                            {selectedReviewer && (
                              <div className="flex items-center gap-3 mb-4">
                                <Avatar className="h-10 w-10" style={{ backgroundColor: selectedReviewer.color }}>
                                  <AvatarFallback className="text-white font-bold">
                                    {selectedReviewer.avatar}
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <h3 className="font-semibold">{selectedReviewer.name} 的审稿意见</h3>
                                  <p className="text-xs text-muted-foreground">{selectedReviewer.institution}</p>
                                </div>
                              </div>
                            )}

                            {/* 论文内容（带标红） */}
                            <div className="mb-6 p-4 bg-muted/50 rounded-lg border max-h-96 overflow-auto">
                              {renderHighlightedPaper(message.paperContent, message.reviewComments)}
                            </div>

                            {/* 详细意见列表 */}
                            <div className="space-y-3">
                              <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                                <Lightbulb className="h-4 w-4 text-[#0F3B6C]" />
                                详细修改意见 ({message.reviewComments.length})
                              </h4>
                              {message.reviewComments.map((comment) => (
                                <Card key={comment.id} className={`border-l-4 ${getSeverityColor(comment.severity)}`}>
                                  <CardContent className="pt-4">
                                    <div className="flex items-start justify-between mb-2">
                                      <div className="flex items-center gap-2">
                                        <Badge variant="outline" className={getSeverityColor(comment.severity)}>
                                          {getSeverityLabel(comment.severity)}
                                        </Badge>
                                        <Badge variant="outline">
                                          {getTypeLabel(comment.type)}
                                        </Badge>
                                        <span className="text-xs text-muted-foreground">{comment.paragraph}</span>
                                      </div>
                                    </div>
                                    
                                    <div className="space-y-2 text-sm">
                                      <div className="bg-red-50 p-3 rounded border border-red-200">
                                        <p className="text-xs text-muted-foreground mb-1">原文片段:</p>
                                        <p className="font-mono text-xs text-red-700">{comment.originalText}</p>
                                      </div>
                                      <div className="bg-blue-50 p-3 rounded border border-blue-200">
                                        <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                                          <Lightbulb className="h-3 w-3" />
                                          修改建议:
                                        </p>
                                        <p className="text-xs">{comment.suggestion}</p>
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    )}

                    {/* 审稿人选择卡片 */}
                    {message.reviewers && message.reviewers.length > 0 && (
                      <div className="mt-4 space-y-3">
                        {message.reviewers.map(reviewer => (
                          <Card 
                            key={reviewer.id}
                            className="p-4 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all"
                            onClick={() => handleSelectReviewer(reviewer)}
                          >
                            <div className="flex items-start gap-3">
                              <div className="text-3xl">{reviewer.avatar}</div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <h4 className="font-semibold">{reviewer.name}</h4>
                                  <Badge variant="outline" className="text-xs">h-index: {reviewer.hIndex}</Badge>
                                </div>
                                <div className="text-sm text-muted-foreground mb-1">{reviewer.institution}</div>
                                <div className="text-xs text-muted-foreground mb-2">
                                  <span className="font-medium">研究方向：</span>{reviewer.expertise}
                                </div>
                                <div className="text-xs bg-blue-50 px-2 py-1 rounded">
                                  <span className="font-medium">审稿风格：</span>{reviewer.style}
                                </div>
                              </div>
                              <UserCheck className="h-5 w-5 text-[#0F3B6C]" />
                            </div>
                          </Card>
                        ))}
                      </div>
                    )}

                    {/* 相关问题推荐 */}
                    {message.relatedQuestions && message.relatedQuestions.length > 0 && (
                      <div className="mt-3 ml-4">
                        <div className="text-xs text-muted-foreground mb-2">💡 相关问题</div>
                        <div className="flex flex-wrap gap-2">
                          {message.relatedQuestions.map((q, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="cursor-pointer hover:bg-[#0F3B6C] hover:text-white hover:border-[#0F3B6C] transition-colors"
                              onClick={() => setInputValue(q)}
                            >
                              {q}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}

            {/* 加载动画 */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-card border shadow-sm rounded-2xl px-4 py-3">
                  <Loader2 className="h-5 w-5 animate-spin text-[#0F3B6C]" />
                </div>
              </div>
            )}

            {/* 审稿进行中 */}
            {isReviewing && selectedReviewer && (
              <div className="flex justify-start">
                <div className="bg-card rounded-lg px-4 py-3 max-w-[70%] shadow-sm border">
                  <div className="flex items-center gap-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#0F3B6C]"></div>
                    <div>
                      <div className="text-sm font-medium">{selectedReviewer.name} 正在审稿中...</div>
                      <div className="text-xs text-muted-foreground">预计需要 3 秒钟</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          // 空状态 - 展示引导
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-2xl px-6">
              <div className="h-20 w-20 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Sparkles className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-2xl font-bold mb-3">你好！我是您的智能研究助手</h3>
              <p className="text-muted-foreground mb-8">
                我可以帮助您解答学术问题、分析论文、提供研究建议。请输入您的问题开始对话。
              </p>
              
              {/* 推荐问题 */}
              <div className="space-y-4 mb-6">
                <div>
                  <h4 className="text-sm font-semibold mb-3 text-muted-foreground">💡 快速开始</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <Card 
                      className="p-4 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all text-left"
                      onClick={() => setInputValue('介绍一下Transformer架构的核心原理')}
                    >
                      <div className="text-sm font-medium mb-1">🤖 深度学习</div>
                      <div className="text-xs text-muted-foreground">介绍一下Transformer架构的核心原理</div>
                    </Card>
                    <Card 
                      className="p-4 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all text-left"
                      onClick={() => setInputValue('如何撰写高质量的学术论文？')}
                    >
                      <div className="text-sm font-medium mb-1">📝 论文写作</div>
                      <div className="text-xs text-muted-foreground">如何撰写高质量的学术论文？</div>
                    </Card>
                    <Card 
                      className="p-4 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all text-left"
                      onClick={handleStartReview}
                    >
                      <div className="text-sm font-medium mb-1">📄 模拟审稿</div>
                      <div className="text-xs text-muted-foreground">上传文档开始智能审稿</div>
                    </Card>
                    <Card 
                      className="p-4 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all text-left"
                      onClick={() => onOpenTutorial?.()}
                    >
                      <div className="text-sm font-medium mb-1">📚 新手引导</div>
                      <div className="text-xs text-muted-foreground">了解平台功能和使用方法</div>
                    </Card>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold mb-3 text-muted-foreground">📁 项目管理功能</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <Card 
                      className="p-3 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all text-left border-2 border-dashed"
                      onClick={() => setShowProjectsListDialog(true)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <FolderOpen className="h-4 w-4 text-[#0F3B6C]" />
                        <div className="text-sm font-medium">查看项目</div>
                      </div>
                      <div className="text-xs text-muted-foreground">查看所有项目</div>
                    </Card>
                    <Card 
                      className="p-3 cursor-pointer hover:shadow-md hover:border-[#0F3B6C] transition-all text-left border-2 border-dashed"
                      onClick={() => setShowNewProjectDialog(true)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Plus className="h-4 w-4 text-[#0F3B6C]" />
                        <div className="text-sm font-medium">创建项目</div>
                      </div>
                      <div className="text-xs text-muted-foreground">新建研究项目</div>
                    </Card>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground px-1">
                    💡 提示：您也可以直接输入命令，如"查看项目列表"、"创建项目：项目名称"、"编辑项目：项目名称"等
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        </ScrollArea>
        </div>

        {/* 附着在滚动条上的问题列表 */}
        {currentConversation && currentConversation.messages.length > 0 && showQuestionsList && (
          <div 
            className="absolute right-2 top-1/2 -translate-y-1/2 w-64 bg-card border border-border rounded-lg shadow-xl z-50 flex flex-col max-h-[70vh]"
            onMouseEnter={() => {
              // 鼠标进入问题列表时，保持显示并清除隐藏计时器
              if (hoverTimeoutRef.current) {
                clearTimeout(hoverTimeoutRef.current);
              }
            }}
            onMouseLeave={() => {
              // 鼠标离开问题列表时，5秒后隐藏
              if (hoverTimeoutRef.current) {
                clearTimeout(hoverTimeoutRef.current);
              }
              hoverTimeoutRef.current = setTimeout(() => {
                setShowQuestionsList(false);
              }, 5000);
            }}
          >
            <div className="px-4 py-3 border-b flex-shrink-0 bg-gradient-to-r from-[#0F3B6C]/5 to-[#4A2E9E]/5">
              <h3 className="text-sm font-semibold text-foreground">问题列表</h3>
              <p className="text-xs text-muted-foreground mt-1">点击问题快速定位</p>
            </div>
            <ScrollArea className="flex-1">
              <div className="px-2 py-2">
                {currentConversation.messages
                  .map((message, index) => ({ message, index }))
                  .filter(({ message }) => message.role === 'user')
                  .map(({ message, index }) => (
                    <div
                      key={index}
                      onClick={() => {
                        const element = messageRefs.current[index];
                        if (element) {
                          // 高亮显示跳转到的消息
                          setHighlightedMessageIndex(index);
                          // 平滑滚动到对应位置
                          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          // 3秒后取消高亮
                          setTimeout(() => {
                            setHighlightedMessageIndex(null);
                          }, 3000);
                          // 延迟隐藏问题列表，让用户看到跳转效果
                          setTimeout(() => {
                            setShowQuestionsList(false);
                          }, 500);
                        }
                      }}
                      className="px-3 py-2.5 mb-2 rounded-lg cursor-pointer hover:bg-accent active:bg-accent/80 transition-all duration-200 border border-transparent hover:border-border hover:shadow-sm group"
                    >
                      <div className="flex items-start gap-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-blue-400 dark:bg-blue-500 mt-1.5 flex-shrink-0 group-hover:bg-blue-600 dark:group-hover:bg-blue-400 transition-colors"></div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-foreground line-clamp-2 leading-relaxed font-medium group-hover:text-[#0F3B6C] dark:group-hover:text-[#4A90E2] transition-colors">
                            {message.content.length > 50 
                              ? message.content.substring(0, 50) + '...' 
                              : message.content}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </div>

      {/* 底部输入区 */}
      <div className="border-t bg-card p-6 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            <Input
              placeholder="发送消息或上传文件"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              className="pr-32 pl-24 py-5 rounded-xl text-base border-2 focus:border-[#0F3B6C] h-16 bg-input-background"
              disabled={loading}
            />
            
            {/* 模拟审稿按钮 - 在输入框左下角，当有文件时显示 */}
            {selectedFile && !selectedReviewer && (
              <div className="absolute left-4 bottom-4">
                <Button
                  onClick={handleStartReview}
                  variant="outline"
                  className="bg-card hover:bg-muted text-blue-600 border-blue-200 rounded-lg px-4 py-2 flex items-center gap-2 text-sm font-medium h-auto"
                >
                  <Brain className="h-4 w-4" />
                  模拟审稿
                </Button>
              </div>
            )}
            
            {/* 右侧按钮组 */}
            <div className="absolute right-4 bottom-4 flex items-center gap-3">
              {/* 回形针按钮 */}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="上传附件"
              >
                <Paperclip className="h-6 w-6 text-muted-foreground" />
              </button>
              
              {/* 发送按钮 */}
              <Button
                size="icon"
                className="bg-[#0F3B6C] hover:bg-[#0a2945] rounded-lg h-10 w-10"
                onClick={handleSendMessage}
                disabled={loading || !inputValue.trim()}
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 审稿人选择对话框 */}
      <Dialog open={showReviewerDialog} onOpenChange={setShowReviewerDialog}>
        <DialogContent className="max-w-[95%] w-[95%] max-h-[85vh] h-[85vh] flex flex-col p-0 overflow-hidden">
          {/* 头部 - 优化设计 */}
          <div className="px-6 sm:px-8 pt-4 sm:pt-5 pb-3 sm:pb-4 border-b bg-gradient-to-r from-[#0F3B6C]/5 to-[#4A2E9E]/5 flex-shrink-0">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-2xl bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] flex items-center justify-center shadow-lg">
                <UserCheck className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
              </div>
              <div className="flex-1">
                <DialogTitle className="text-lg sm:text-xl font-bold text-foreground mb-1">
                  选择审稿人
                </DialogTitle>
                <DialogDescription className="text-xs sm:text-sm text-muted-foreground">
                  不同审稿人有不同的审稿风格和侧重点，请根据您的论文特点选择最合适的审稿人
                </DialogDescription>
              </div>
            </div>
          </div>
          
          {/* 内容区域 - 添加滚动条 */}
          <div className="flex-1 overflow-hidden min-h-0" style={{ height: 'calc(85vh - 140px)' }}>
            <ScrollArea className="h-full w-full">
              <div className="px-4 sm:px-6 md:px-8 py-4 sm:py-6">
                <div className="space-y-4">
              {reviewers.map(reviewer => (
                <Card 
                  key={reviewer.id}
                  className="cursor-pointer group relative overflow-hidden border-2 border-border hover:border-[#0F3B6C] hover:shadow-xl transition-all duration-300 bg-card"
                  onClick={() => handleSelectReviewer(reviewer)}
                >
                  {/* 左侧装饰条 */}
                  <div 
                    className="w-2 h-full absolute top-0 left-0"
                    style={{ backgroundColor: reviewer.color }}
                  />
                  
                  <CardContent className="pt-4 pb-4 pl-6 pr-4 sm:pl-8 sm:pr-6">
                    <div className="flex items-center gap-4 sm:gap-6">
                      {/* 左侧：审稿人肖像 */}
                      <div className="relative flex-shrink-0">
                        <div 
                          className="h-14 w-14 sm:h-16 sm:w-16 md:h-16 md:w-16 rounded-xl flex items-center justify-center shadow-lg relative overflow-hidden"
                          style={{ backgroundColor: reviewer.color }}
                        >
                          <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
                          <span className="text-white text-xl sm:text-2xl md:text-2xl font-bold relative z-10">
                            {reviewer.avatar}
                          </span>
                        </div>
                        <div className="absolute -bottom-1 -right-1 h-4 w-4 sm:h-5 sm:w-5 bg-green-500 rounded-full border-2 border-white flex items-center justify-center shadow-md">
                          <CheckCircle2 className="h-2 w-2 sm:h-2.5 sm:w-2.5 text-white" />
                        </div>
                      </div>
                      
                      {/* 中间：审稿人信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="mb-2">
                          <h4 className="font-bold text-base sm:text-lg text-foreground mb-1 group-hover:text-[#0F3B6C] dark:group-hover:text-[#4A90E2] transition-colors">
                            {reviewer.name}
                          </h4>
                          <p className="text-xs sm:text-sm text-muted-foreground font-medium">{reviewer.institution}</p>
                        </div>
                        
                        <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed mb-3 line-clamp-2">
                          {reviewer.description}
                        </p>
                        
                        {/* 标签信息 - 横向排列 */}
                        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-muted-foreground font-medium">专业领域:</span>
                            <Badge variant="secondary" className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 border-0 font-medium">
                              {reviewer.expertise.split(',')[0]}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-muted-foreground font-medium">严格程度:</span>
                            <Badge 
                              variant="outline" 
                              className={`text-xs px-2 py-0.5 border-0 font-medium ${
                                reviewer.strictness === '严格' ? 'bg-red-100 text-red-700' :
                                reviewer.strictness === '中等' ? 'bg-orange-100 text-orange-700' :
                                'bg-green-100 text-green-700'
                              }`}
                            >
                              {reviewer.strictness}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-muted-foreground font-medium">审稿风格:</span>
                            <span className="text-xs font-semibold text-foreground">{reviewer.style}</span>
                          </div>
                        </div>
                      </div>
                      
                      {/* 右侧：选择按钮 */}
                      <div className="flex-shrink-0">
                        <Button 
                          className="bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E] hover:from-[#0a2945] hover:to-[#3a1e7e] text-white shadow-lg hover:shadow-xl transition-all h-10 px-6 text-sm font-semibold rounded-lg whitespace-nowrap"
                          size="default"
                        >
                          <UserCheck className="mr-2 h-4 w-4" />
                          选择此审稿人
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
                </div>
              </div>
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      {/* 新建项目对话框 */}
      <NewProjectDialog 
        isOpen={showNewProjectDialog} 
        onClose={() => setShowNewProjectDialog(false)} 
        onCreateProject={handleCreateProject} 
      />

      {/* 项目列表对话框 */}
      <ProjectsListDialog
        isOpen={showProjectsListDialog}
        onClose={() => setShowProjectsListDialog(false)}
        projects={projects}
        setProjects={setProjects}
      />
    </div>
  );
}
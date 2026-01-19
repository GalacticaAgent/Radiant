import React, { useRef, useState } from 'react';
import { Button } from '@/app/components/ui/button';
import { Card, CardContent } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/app/components/ui/avatar';
import { 
  Paperclip, 
  Send, 
  FileText, 
  UserCheck, 
  CheckCircle2, 
  AlertCircle, 
  Lightbulb,
  Brain,
  X
} from 'lucide-react';
import { PageHeader } from '@/app/components/common/PageHeader';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import { Input } from '@/app/components/ui/input';

interface ReviewPageProps {
  onFileUpload: () => void;
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
  avatarUrl?: string; // 审稿人肖像图片URL
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

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  file?: File;
  timestamp: Date;
}

export function ReviewPage({ onFileUpload }: ReviewPageProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: 'assistant',
      content: '今天有什么可以帮到你？',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showReviewerDialog, setShowReviewerDialog] = useState(false);
  const [selectedReviewer, setSelectedReviewer] = useState<Reviewer | null>(null);
  const [reviewComments, setReviewComments] = useState<ReviewComment[]>([]);
  const [paperContent, setPaperContent] = useState<string>('');
  const [isReviewing, setIsReviewing] = useState(false);

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
      color: '#FF6B6B',
      avatarUrl: undefined // 可以添加实际的头像URL
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
      color: '#4ECDC4',
      avatarUrl: undefined
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
      color: '#95E1D3',
      avatarUrl: undefined
    }
  ];

  // 模拟论文内容（实际应该从上传的文件中读取）
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

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setSelectedFile(file);
      
      // 添加用户消息显示已上传文件
      const userMessage: Message = {
        id: messages.length + 1,
        role: 'user',
        content: `已上传文件: ${file.name}`,
        file: file,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, userMessage]);
      
      // 模拟读取文件内容（实际应该解析PDF/Word等）
      setPaperContent(mockPaperContent);
      
      // 添加助手回复
      const assistantMessage: Message = {
        id: messages.length + 2,
        role: 'assistant',
        content: '文件已成功上传！您可以点击"模拟审稿"按钮开始审稿流程。',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    }
  };

  const handleStartReview = () => {
    setShowReviewerDialog(true);
  };

  const handleSelectReviewer = (reviewer: Reviewer) => {
    setSelectedReviewer(reviewer);
    setShowReviewerDialog(false);
    setIsReviewing(true);
    
    // 添加用户消息
    const userMessage: Message = {
      id: messages.length + 1,
      role: 'user',
      content: `已选择审稿人: ${reviewer.name}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    
    // 模拟审稿过程
    setTimeout(() => {
      generateReviewComments(reviewer);
      setIsReviewing(false);
      
      // 添加助手消息
      const assistantMessage: Message = {
        id: messages.length + 2,
        role: 'assistant',
        content: `${reviewer.name} 已完成审稿，共发现 ${reviewComments.length} 处需要修改的地方。`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    }, 3000);
  };

  const generateReviewComments = (reviewer: Reviewer) => {
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
    
    setReviewComments(comments);
  };

  const handleSend = () => {
    if (!input.trim() && !selectedFile) return;
    
    if (input.trim()) {
      const userMessage: Message = {
        id: messages.length + 1,
        role: 'user',
        content: input,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      setInput('');
    }
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
  const renderHighlightedPaper = () => {
    if (!paperContent || reviewComments.length === 0) {
      return <div className="text-sm text-muted-foreground">{paperContent || '暂无内容'}</div>;
    }

    // 按位置排序评论
    const sortedComments = [...reviewComments].sort((a, b) => a.startIndex - b.startIndex);
    
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

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="flex-1 flex flex-col max-w-6xl mx-auto w-full">
        <PageHeader 
          icon={FileText}
          title="AI 模拟审稿"
          subtitle="上传您的学术论文，获得专业的AI审稿意见"
        />

        {/* 聊天消息区域 */}
        <ScrollArea className="flex-1 px-6 py-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="flex flex-col">
                {message.role === 'user' ? (
                  <div className="flex justify-end">
                    <div className="bg-[#0F3B6C] text-white rounded-lg px-4 py-2 max-w-[70%]">
                      {message.content}
                      {message.file && (
                        <div className="mt-2 flex items-center gap-2 text-sm opacity-90">
                          <FileText className="h-4 w-4" />
                          {message.file.name}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-start">
                    <div className="bg-card rounded-lg px-4 py-3 max-w-[70%] shadow-sm border">
                      <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                    </div>
                  </div>
                )}
              </div>
            ))}

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

            {/* 显示审稿结果 */}
            {!isReviewing && selectedReviewer && reviewComments.length > 0 && (
              <div className="space-y-4">
                <Card className="border-2">
                  <CardContent className="p-6">
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

                    {/* 论文内容（带标红） */}
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg border max-h-96 overflow-auto">
                      {renderHighlightedPaper()}
                    </div>

                    {/* 详细意见列表 */}
                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-[#0F3B6C]" />
                        详细修改意见 ({reviewComments.length})
                      </h4>
                      {reviewComments.map((comment) => (
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
          </div>
        </ScrollArea>

        {/* 输入区域 */}
        <div className="p-4 border-t bg-card">
          <div className="relative">
            <div className="relative">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="给 DeepSeek 发送消息"
                className="pr-32 pl-24 py-3 rounded-xl text-base border-2 focus:border-[#0F3B6C] bg-input-background"
              />
              
              {/* 模拟审稿按钮 - 在输入框左下角，当有文件时显示 */}
              {selectedFile && !selectedReviewer && (
                <div className="absolute left-3 bottom-3">
                  <Button
                    onClick={handleStartReview}
                    variant="outline"
                    className="bg-white hover:bg-gray-50 text-blue-600 border-blue-200 rounded-lg px-3 py-1.5 flex items-center gap-1.5 text-sm font-medium h-auto"
                  >
                    <Brain className="h-3.5 w-3.5" />
                    模拟审稿
                  </Button>
                </div>
              )}
              
              {/* 右侧按钮组 */}
              <div className="absolute right-3 bottom-3 flex items-center gap-2">
                {/* 回形针按钮 */}
                <button
                  onClick={handleFileUpload}
                  className="p-1.5 hover:bg-muted rounded transition-colors"
                  title="上传附件"
                >
                  <Paperclip className="h-5 w-5 text-muted-foreground" />
                </button>
                
                {/* 发送按钮 */}
                <Button 
                  onClick={handleSend} 
                  size="icon"
                  className="bg-[#0F3B6C] hover:bg-[#0a2945] rounded-lg h-8 w-8"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.doc,.docx,.tex"
            onChange={handleFileChange}
          />
        </div>
      </div>

      {/* 审稿人选择对话框 */}
      <Dialog open={showReviewerDialog} onOpenChange={setShowReviewerDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-[#0F3B6C]" />
              选择审稿人
            </DialogTitle>
            <DialogDescription>
              不同审稿人有不同的审稿风格和侧重点，请根据需求选择
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            {reviewers.map(reviewer => (
              <Card 
                key={reviewer.id}
                className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-[#0F3B6C]"
                onClick={() => handleSelectReviewer(reviewer)}
              >
                <CardContent className="pt-6">
                  <div className="flex flex-col items-center text-center space-y-3">
                    {/* 审稿人肖像 */}
                    <Avatar className="h-20 w-20" style={{ backgroundColor: reviewer.color }}>
                      <AvatarFallback className="text-white text-2xl font-bold" style={{ backgroundColor: reviewer.color }}>
                        {reviewer.avatar}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div>
                      <h4 className="font-semibold text-lg">{reviewer.name}</h4>
                      <p className="text-xs text-muted-foreground">{reviewer.institution}</p>
                    </div>
                    
                    <div className="space-y-2 w-full">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">专业领域:</span>
                        <Badge variant="outline" className="text-xs">{reviewer.expertise.split(',')[0]}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">严格程度:</span>
                        <Badge variant="outline" className="text-xs">{reviewer.strictness}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">审稿风格:</span>
                        <span className="text-xs">{reviewer.style}</span>
                      </div>
                    </div>
                    
                    <p className="text-xs text-muted-foreground">{reviewer.description}</p>
                    
                    <Button 
                      className="w-full bg-[#0F3B6C] hover:bg-[#0a2945]"
                      size="sm"
                    >
                      选择此审稿人
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

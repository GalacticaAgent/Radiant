import React, { useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Badge } from '@/app/components/ui/badge';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/app/components/ui/avatar';
import { Bot, Send, Lightbulb, BookOpen, Network, UserCircle, CheckCircle2, ChevronRight } from 'lucide-react';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  suggestions?: string[];
  sourceNodes?: string[];
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

interface ReviewComment {
  id: string;
  text: string;
  originalText: string;
  suggestion: string;
  type: 'grammar' | 'clarity' | 'methodology' | 'structure';
  severity: 'high' | 'medium' | 'low';
}

interface IntelligentSidebarProps {
  mode?: 'chat' | 'review';
  reviewContent?: string;
  reviewType?: string;
  reviewerProfile?: any;
  onApplySuggestion?: (comment: ReviewComment) => void;
}

export function IntelligentSidebar({ 
  mode = 'chat', 
  reviewContent, 
  reviewType, 
  reviewerProfile,
  onApplySuggestion 
}: IntelligentSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: 'assistant',
      content: '您好！我是 Radiant 智能助手。我可以帮助您：\n\n• 总结论文和文献\n• 探索知识图谱\n• 寻找相关研究\n• 模拟审稿意见\n\n请问有什么可以帮您？',
      suggestions: ['总结当前论文', '寻找相关文献', '扩展知识图谱']
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedReviewer, setSelectedReviewer] = useState<Reviewer | null>(null);
  const [reviewComments, setReviewComments] = useState<ReviewComment[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // 模拟审稿人数据
  const reviewers: Reviewer[] = [
    {
      id: 'reviewer-yoshua',
      name: 'Dr. Yoshua Bengio',
      avatar: 'YB',
      expertise: '深度学习',
      strictness: '严格',
      style: '批判性',
      description: '2018年图灵奖得主，深度学习三巨头之一。在神经网络、表示学习领域发表过500+篇论文，H-index超过150。强调理论严谨性和数学证明。',
      institution: 'Université de Montréal',
      color: 'from-indigo-600 to-purple-700'
    },
    {
      id: 'reviewer-lecun',
      name: 'Dr. Yann LeCun',
      avatar: 'YL',
      expertise: '卷积神经网络',
      strictness: '适中',
      style: '建设性',
      description: '2018年图灵奖得主，CNN之父，Meta首席AI科学家。在CVPR、NeurIPS等顶会发表200+篇论文。注重实验验证和工程实践，善于提出建设性改进建议。',
      institution: 'Meta AI & NYU',
      color: 'from-blue-600 to-cyan-600'
    },
    {
      id: 'reviewer-hinton',
      name: 'Dr. Geoffrey Hinton',
      avatar: 'GH',
      expertise: '神经网络',
      strictness: '宽松',
      style: '鼓励性',
      description: '2018年图灵奖得主，"深度学习教父"，反向传播算法核心贡献者。Google前副总裁，发表300+篇论文。鼓励创新思想，关注方法的潜力和未来应用价值。',
      institution: 'University of Toronto',
      color: 'from-green-600 to-teal-600'
    },
  ];

  // 生成审稿意见
  const generateReview = (reviewer: Reviewer) => {
    setSelectedReviewer(reviewer);
    setIsGenerating(true);

    // 模拟生成审稿意见
    setTimeout(() => {
      const mockComments: ReviewComment[] = [
        {
          id: 'comment-1',
          text: '摘要的第一句过于宽泛',
          originalText: '深度学习在自然语言处理领域有广泛应用',
          suggestion: '深度学习技术，特别是基于Transformer的模型，已成为自然语言处理领域的主流方法',
          type: 'clarity',
          severity: 'medium'
        },
        {
          id: 'comment-2',
          text: '方法论部分缺少实验设置的细节',
          originalText: '我们使用标准的训练方法',
          suggestion: '我们采用AdamW优化器（学习率1e-4，权重衰减0.01），在8块V100 GPU上训练模型，批次大小为32',
          type: 'methodology',
          severity: 'high'
        },
        {
          id: 'comment-3',
          text: '这个句子存在语法问题',
          originalText: '实验结果表明我们的模型表现更好',
          suggestion: '实验结果表明，我们的模型在所有评估指标上均优于基线方法',
          type: 'grammar',
          severity: 'low'
        },
        {
          id: 'comment-4',
          text: '结构建议：引言过长，建议精简',
          originalText: '',
          suggestion: '将引言部分从3页精简至1.5页，突出核心贡献和创新点',
          type: 'structure',
          severity: 'medium'
        },
      ];

      setReviewComments(mockComments);
      setIsGenerating(false);
    }, 2000);
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      role: 'user',
      content: input
    };

    const assistantMessage: Message = {
      id: messages.length + 2,
      role: 'assistant',
      content: '我正在分析您的问题并从知识图谱中检索相关信息...\\n\\n根据知识图谱中的数据，McDonald 的主要研究方向包括：\\n\\n1. 深度学习在 NLP 中的应用\\n2. Transformer 架构优化\\n3. 大规模语言模型训练\\n\\n相关的关键论文已标记在图谱中。',
      suggestions: ['深入了解第1点', '对比其他研究', '生成研究报告'],
      sourceNodes: ['McDonald et al.', 'Deep Learning in NLP', 'Transformer Architecture']
    };

    setMessages([...messages, userMessage, assistantMessage]);
    setInput('');
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return '';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'grammar': return '语法';
      case 'clarity': return '清晰度';
      case 'methodology': return '方法论';
      case 'structure': return '结构';
      default: return type;
    }
  };

  // 审稿模式渲染
  if (mode === 'review') {
    return (
      <Card className="h-full flex flex-col">
        {/* 头部 */}
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-2">
            <UserCircle className="h-5 w-5 text-[#0F3B6C]" />
            <h3 className="font-semibold">模拟审稿</h3>
          </div>
          <p className="text-xs text-muted-foreground">选择审稿人查看专业意见</p>
        </div>

        <ScrollArea className="flex-1 p-4">
          {!selectedReviewer ? (
            /* 审稿人选择 */
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-muted-foreground mb-3">可用审稿人</h4>
              {reviewers.map((reviewer) => (
                <Card
                  key={reviewer.id}
                  className="p-4 cursor-pointer hover:shadow-lg transition-all border-2 hover:border-[#0F3B6C]"
                  onClick={() => generateReview(reviewer)}
                >
                  <div className="flex items-start gap-3">
                    <Avatar className={`h-12 w-12 bg-gradient-to-br ${reviewer.color}`}>
                      <AvatarFallback className="text-white font-bold text-lg">
                        {reviewer.avatar}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h5 className="font-semibold">{reviewer.name}</h5>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <p className="text-xs text-muted-foreground mb-2">{reviewer.institution}</p>
                      <p className="text-sm mb-2">{reviewer.description}</p>
                      <div className="flex flex-wrap gap-1">
                        <Badge variant="secondary" className="text-xs">
                          {reviewer.expertise}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {reviewer.strictness}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {reviewer.style}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : isGenerating ? (
            /* 生成中 */
            <div className="flex flex-col items-center justify-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0F3B6C] mb-4"></div>
              <p className="text-sm text-muted-foreground">审稿人正在仔细审阅您的论文...</p>
            </div>
          ) : (
            /* 审稿意见 */
            <div className="space-y-4">
              {/* 审稿人信息 */}
              <Card className="p-4 bg-gradient-to-br from-slate-50 to-white">
                <div className="flex items-center gap-3 mb-2">
                  <Avatar className={`h-10 w-10 bg-gradient-to-br ${selectedReviewer.color}`}>
                    <AvatarFallback className="text-white font-bold">
                      {selectedReviewer.avatar}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h5 className="font-semibold">{selectedReviewer.name}</h5>
                    <p className="text-xs text-muted-foreground">{selectedReviewer.institution}</p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => {
                    setSelectedReviewer(null);
                    setReviewComments([]);
                  }}
                >
                  更换审稿人
                </Button>
              </Card>

              {/* 审稿意见列表 */}
              <div>
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-[#0F3B6C]" />
                  审稿意见 ({reviewComments.length})
                </h4>
                <div className="space-y-3">
                  {reviewComments.map((comment) => (
                    <Card key={comment.id} className={`p-3 border-l-4 ${getSeverityColor(comment.severity)}`}>
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            {getTypeLabel(comment.type)}
                          </Badge>
                          <Badge variant="outline" className="text-xs capitalize">
                            {comment.severity === 'high' ? '重要' : comment.severity === 'medium' ? '中等' : '轻微'}
                          </Badge>
                        </div>
                      </div>
                      
                      <p className="text-sm font-medium mb-2">{comment.text}</p>
                      
                      {comment.originalText && (
                        <div className="mb-2 p-2 bg-red-50 rounded border border-red-200">
                          <p className="text-xs text-muted-foreground mb-1">原文：</p>
                          <p className="text-sm text-red-700 line-through">{comment.originalText}</p>
                        </div>
                      )}
                      
                      <div className="mb-3 p-2 bg-green-50 rounded border border-green-200">
                        <p className="text-xs text-muted-foreground mb-1">建议修改：</p>
                        <p className="text-sm text-green-700">{comment.suggestion}</p>
                      </div>

                      <Button
                        size="sm"
                        className="w-full bg-[#0F3B6C]"
                        onClick={() => onApplySuggestion && onApplySuggestion(comment)}
                      >
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        应用修改
                      </Button>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}
        </ScrollArea>
      </Card>
    );
  }

  // 聊天模式渲染（默认）
  return (
    <Card className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-2 mb-2">
          <Bot className="h-5 w-5 text-[#0F3B6C]" />
          <h3 className="font-semibold">智能协作助手</h3>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            <Network className="mr-1 h-3 w-3" />
            调研助手模式
          </Badge>
          <Badge variant="outline" className="text-xs">
            已连接知识图谱
          </Badge>
        </div>
      </div>

      {/* 对话区域 */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id}>
              {message.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="bg-[#0F3B6C] text-white rounded-lg px-4 py-2 max-w-[80%]">
                    {message.content}
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="bg-muted/50 rounded-lg px-4 py-3">
                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                  </div>

                  {/* 知识来源 */}
                  {message.sourceNodes && message.sourceNodes.length > 0 && (
                    <div className="ml-2">
                      <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        <BookOpen className="h-3 w-3" />
                        知识来源:
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {message.sourceNodes.map((node, i) => (
                          <Badge key={i} variant="outline" className="text-xs cursor-pointer hover:bg-accent">
                            {node}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 建议操作 */}
                  {message.suggestions && message.suggestions.length > 0 && (
                    <div className="ml-2">
                      <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                        <Lightbulb className="h-3 w-3" />
                        建议下��步:
                      </div>
                      <div className="space-y-2">
                        {message.suggestions.map((suggestion, i) => (
                          <Button
                            key={i}
                            variant="outline"
                            size="sm"
                            className="w-full justify-start text-xs h-8"
                            onClick={() => setInput(suggestion)}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* 输入区域 */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="向 Radiant 提问..."
            className="flex-1"
          />
          <Button onClick={handleSend} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
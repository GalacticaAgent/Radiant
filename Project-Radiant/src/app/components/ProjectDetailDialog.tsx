import React, { useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Progress } from '@/app/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { 
  X, 
  FileText, 
  Users, 
  Clock, 
  Activity,
  BookOpen,
  MessageSquare,
  Settings,
  Calendar,
  Tag,
  Edit,
  Trash2
} from 'lucide-react';

interface Project {
  id: number;
  name: string;
  description: string;
  papers: number;
  members: number;
  progress: number;
  lastUpdate: string;
  status: string;
  template: string;
}

interface ProjectDetailDialogProps {
  isOpen: boolean;
  project: Project | null;
  onClose: () => void;
  onEdit: (project: Project) => void;
  onDelete: (projectId: number) => void;
}

export function ProjectDetailDialog({ 
  isOpen, 
  project, 
  onClose, 
  onEdit, 
  onDelete 
}: ProjectDetailDialogProps) {
  if (!isOpen || !project) return null;

  const handleDelete = () => {
    if (window.confirm(`确定要删除项目"${project.name}"吗？此操作不可撤销。`)) {
      onDelete(project.id);
      onClose();
    }
  };

  // 模拟项目活动数据
  const activities = [
    {
      id: 1,
      type: 'paper',
      user: '张三',
      action: '添加了新文献',
      content: 'Attention Is All You Need',
      time: '2小时前'
    },
    {
      id: 2,
      type: 'comment',
      user: '李四',
      action: '发表了评论',
      content: '这篇论文的实验部分值得深入研究',
      time: '5小时前'
    },
    {
      id: 3,
      type: 'update',
      user: '王五',
      action: '更新了项目进度',
      content: '完成了第三章的撰写',
      time: '1天前'
    },
    {
      id: 4,
      type: 'member',
      user: '赵六',
      action: '加入了项目',
      content: '',
      time: '2天前'
    }
  ];

  // 模拟项目成员数据
  const membersList = [
    { id: 1, name: '张三', role: '项目负责人', avatar: 'Z', email: 'zhangsan@example.com' },
    { id: 2, name: '李四', role: '研究员', avatar: 'L', email: 'lisi@example.com' },
    { id: 3, name: '王五', role: '研究员', avatar: 'W', email: 'wangwu@example.com' }
  ];

  // 模拟项目文献数据
  const papersList = [
    { 
      id: 1, 
      title: 'Attention Is All You Need', 
      authors: 'Vaswani et al.', 
      year: 2017,
      venue: 'NeurIPS',
      status: '已读'
    },
    { 
      id: 2, 
      title: 'BERT: Pre-training of Deep Bidirectional Transformers', 
      authors: 'Devlin et al.', 
      year: 2019,
      venue: 'NAACL',
      status: '阅读中'
    },
    { 
      id: 3, 
      title: 'GPT-3: Language Models are Few-Shot Learners', 
      authors: 'Brown et al.', 
      year: 2020,
      venue: 'NeurIPS',
      status: '待读'
    }
  ];

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div 
        className="bg-card rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="border-b p-6 bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E]">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-2xl font-bold text-white">{project.name}</h2>
                <Badge 
                  variant="secondary" 
                  className="bg-white/20 text-white border-white/30"
                >
                  {project.status === 'active' ? '进行中' : '审阅中'}
                </Badge>
              </div>
              <p className="text-blue-100 mb-3">{project.description}</p>
              <div className="flex items-center gap-2 text-sm text-blue-100">
                <Tag className="h-4 w-4" />
                <span>模板：{project.template}</span>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="text-white hover:bg-white/20"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* 快速统计 */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="flex items-center gap-2 text-blue-100 text-sm mb-1">
                <FileText className="h-4 w-4" />
                <span>文献数量</span>
              </div>
              <div className="text-2xl font-bold text-white">{project.papers}</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="flex items-center gap-2 text-blue-100 text-sm mb-1">
                <Users className="h-4 w-4" />
                <span>项目成员</span>
              </div>
              <div className="text-2xl font-bold text-white">{project.members}</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="flex items-center gap-2 text-blue-100 text-sm mb-1">
                <Activity className="h-4 w-4" />
                <span>完成度</span>
              </div>
              <div className="text-2xl font-bold text-white">{project.progress}%</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="flex items-center gap-2 text-blue-100 text-sm mb-1">
                <Clock className="h-4 w-4" />
                <span>最后更新</span>
              </div>
              <div className="text-lg font-semibold text-white">{project.lastUpdate}</div>
            </div>
          </div>
        </div>

        {/* 内容区 */}
        <div className="flex-1 overflow-y-auto p-6">
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="overview">概览</TabsTrigger>
              <TabsTrigger value="papers">文献</TabsTrigger>
              <TabsTrigger value="members">成员</TabsTrigger>
              <TabsTrigger value="activity">动态</TabsTrigger>
            </TabsList>

            {/* 项目概览 */}
            <TabsContent value="overview" className="space-y-4">
              <Card className="p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Activity className="h-5 w-5 text-[#0F3B6C]" />
                  项目进度
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">总体进度</span>
                      <span className="font-semibold">{project.progress}%</span>
                    </div>
                    <Progress value={project.progress} className="h-3" />
                  </div>
                  <div className="grid grid-cols-3 gap-3 pt-3 border-t">
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">文献收集</div>
                      <Progress value={80} className="h-2 mb-1" />
                      <div className="text-xs font-medium">80%</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">分析整理</div>
                      <Progress value={60} className="h-2 mb-1" />
                      <div className="text-xs font-medium">60%</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">论文撰写</div>
                      <Progress value={40} className="h-2 mb-1" />
                      <div className="text-xs font-medium">40%</div>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-[#0F3B6C]" />
                  项目信息
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">创建时间</div>
                    <div className="font-medium">2024年1月10日</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">截止日期</div>
                    <div className="font-medium">2024年6月30日</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">项目类型</div>
                    <div className="font-medium">{project.template}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">项目状态</div>
                    <Badge>{project.status === 'active' ? '进行中' : '审阅中'}</Badge>
                  </div>
                </div>
              </Card>

              <Card className="p-4">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-[#0F3B6C]" />
                  项目描述
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {project.description}
                </p>
              </Card>
            </TabsContent>

            {/* 文献列表 */}
            <TabsContent value="papers" className="space-y-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">项目文献 ({papersList.length})</h3>
                <Button size="sm" className="bg-[#0F3B6C]">
                  <FileText className="h-4 w-4 mr-2" />
                  添加文献
                </Button>
              </div>
              {papersList.map((paper) => (
                <Card key={paper.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold mb-1">{paper.title}</h4>
                      <p className="text-sm text-muted-foreground mb-2">
                        {paper.authors} · {paper.venue} {paper.year}
                      </p>
                    </div>
                    <Badge variant={
                      paper.status === '已读' ? 'default' : 
                      paper.status === '阅读中' ? 'secondary' : 'outline'
                    }>
                      {paper.status}
                    </Badge>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <Button variant="outline" size="sm">查看详情</Button>
                    <Button variant="outline" size="sm">添加笔记</Button>
                  </div>
                </Card>
              ))}
            </TabsContent>

            {/* 成员列表 */}
            <TabsContent value="members" className="space-y-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">项目成员 ({membersList.length})</h3>
                <Button size="sm" className="bg-[#0F3B6C]">
                  <Users className="h-4 w-4 mr-2" />
                  邀请成员
                </Button>
              </div>
              {membersList.map((member) => (
                <Card key={member.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-full flex items-center justify-center text-white font-semibold">
                      {member.avatar}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold">{member.name}</h4>
                      <p className="text-sm text-muted-foreground">{member.email}</p>
                    </div>
                    <Badge variant="secondary">{member.role}</Badge>
                    {member.role !== '项目负责人' && (
                      <Button variant="ghost" size="sm">移除</Button>
                    )}
                  </div>
                </Card>
              ))}
            </TabsContent>

            {/* 项目动态 */}
            <TabsContent value="activity" className="space-y-3">
              <h3 className="font-semibold mb-4">最近活动</h3>
              {activities.map((activity) => (
                <div key={activity.id} className="flex gap-3 pb-4 border-b last:border-0">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    activity.type === 'paper' ? 'bg-blue-100 text-blue-600' :
                    activity.type === 'comment' ? 'bg-green-100 text-green-600' :
                    activity.type === 'update' ? 'bg-purple-100 text-purple-600' :
                    'bg-orange-100 text-orange-600'
                  }`}>
                    {activity.type === 'paper' && <FileText className="h-5 w-5" />}
                    {activity.type === 'comment' && <MessageSquare className="h-5 w-5" />}
                    {activity.type === 'update' && <Activity className="h-5 w-5" />}
                    {activity.type === 'member' && <Users className="h-5 w-5" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm">
                      <span className="font-semibold">{activity.user}</span>
                      <span className="text-muted-foreground"> {activity.action}</span>
                    </p>
                    {activity.content && (
                      <p className="text-sm text-muted-foreground mt-1">{activity.content}</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </div>

        {/* 底部操作栏 */}
        <div className="border-t p-4 bg-muted/50 flex items-center justify-between">
          <Button
            variant="destructive"
            onClick={handleDelete}
            className="flex items-center gap-2"
          >
            <Trash2 className="h-4 w-4" />
            删除项目
          </Button>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onClose}>
              关闭
            </Button>
            <Button
              className="bg-[#0F3B6C]"
              onClick={() => {
                onClose(); // 先关闭详情对话框
                // 延迟打开编辑对话框，确保详情对话框先关闭
                setTimeout(() => {
                  onEdit(project);
                }, 100);
              }}
            >
              <Edit className="h-4 w-4 mr-2" />
              编辑项目
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

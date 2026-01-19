import React from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Badge } from '@/app/components/ui/badge';
import { Progress } from '@/app/components/ui/progress';
import { FolderOpen, Plus, Search, Clock, Users, FileText } from 'lucide-react';
import { NewProjectDialog } from '@/app/components/NewProjectDialog';
import { EditProjectDialog } from '@/app/components/EditProjectDialog';
import { ProjectDetailDialog } from '@/app/components/ProjectDetailDialog';

export function ProjectsPage() {
  const [isNewProjectDialogOpen, setIsNewProjectDialogOpen] = React.useState(false);
  const [isEditProjectDialogOpen, setIsEditProjectDialogOpen] = React.useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = React.useState(false);
  const [selectedProject, setSelectedProject] = React.useState<any>(null);
  const [projects, setProjects] = React.useState([
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

  const handleCreateProject = (projectData: any) => {
    const newProject = {
      id: projects.length + 1,
      name: projectData.name,
      description: `基于 ${projectData.templateName} 模板创建`,
      papers: 0,
      members: 1,
      progress: 0,
      lastUpdate: '刚刚',
      status: 'active' as const,
      template: projectData.templateName
    };

    setProjects([newProject, ...projects]);
    console.log('创建新项目:', projectData);
  };

  const handleSaveProject = (projectId: number, updatedData: any) => {
    const updatedProjects = projects.map(project => {
      if (project.id === projectId) {
        return {
          ...project,
          ...updatedData,
          lastUpdate: '刚刚'
        };
      }
      return project;
    });

    setProjects(updatedProjects);
    console.log('更新项目:', projectId, updatedData);
  };

  const handleDeleteProject = (projectId: number) => {
    setProjects(projects.filter(p => p.id !== projectId));
    console.log('删除项目:', projectId);
  };

  const handleOpenDetailDialog = (project: any) => {
    setSelectedProject(project);
    setIsDetailDialogOpen(true);
  };

  const handleOpenEditDialog = (project: any) => {
    setSelectedProject(project);
    setIsEditProjectDialogOpen(true);
  };

  return (
    <div className="h-full p-6 bg-background overflow-y-auto">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 头部操作栏 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center">
              <FolderOpen className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">项目管理</h1>
              <p className="text-sm text-muted-foreground">组织和管理您的研究项目</p>
            </div>
          </div>
          <Button className="bg-[#0F3B6C]" onClick={() => setIsNewProjectDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建项目
          </Button>
        </div>

        {/* 搜索和筛选 */}
        <Card className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="搜索项目..." className="pl-10" />
            </div>
            <Button variant="outline">全部状态</Button>
            <Button variant="outline">全部成员</Button>
          </div>
        </Card>

        {/* 项目列表 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {projects.map((project) => (
            <Card key={project.id} className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className="h-12 w-12 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center">
                    <FolderOpen className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{project.name}</h3>
                    <p className="text-sm text-muted-foreground">{project.description}</p>
                  </div>
                </div>
                <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                  {project.status === 'active' ? '进行中' : '审阅中'}
                </Badge>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-muted-foreground">完成度</span>
                    <span className="font-medium">{project.progress}%</span>
                  </div>
                  <Progress value={project.progress} className="h-2" />
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <FileText className="h-4 w-4" />
                      <span>{project.papers} 篇文献</span>
                    </div>
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Users className="h-4 w-4" />
                      <span>{project.members} 位成员</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <span>{project.lastUpdate}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => handleOpenDetailDialog(project)}>查看详情</Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={() => handleOpenEditDialog(project)}>编辑</Button>
              </div>
            </Card>
          ))}
        </div>

        {/* 新建项目对话框 */}
        <NewProjectDialog 
          isOpen={isNewProjectDialogOpen} 
          onClose={() => setIsNewProjectDialogOpen(false)} 
          onCreateProject={handleCreateProject} 
        />
        
        {/* 编辑项目对话框 */}
        <EditProjectDialog 
          isOpen={isEditProjectDialogOpen} 
          onClose={() => setIsEditProjectDialogOpen(false)} 
          onSave={handleSaveProject} 
          project={selectedProject} 
        />
        
        {/* 项目详情对话框 */}
        <ProjectDetailDialog 
          isOpen={isDetailDialogOpen} 
          onClose={() => setIsDetailDialogOpen(false)} 
          project={selectedProject}
          onEdit={handleOpenEditDialog}
          onDelete={handleDeleteProject}
        />
      </div>
    </div>
  );
}
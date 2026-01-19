import React, { useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Badge } from '@/app/components/ui/badge';
import { Progress } from '@/app/components/ui/progress';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { FolderOpen, Plus, Search, Clock, Users, FileText, X } from 'lucide-react';
import { NewProjectDialog } from '@/app/components/NewProjectDialog';
import { EditProjectDialog } from '@/app/components/EditProjectDialog';
import { ProjectDetailDialog } from '@/app/components/ProjectDetailDialog';

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

interface ProjectsListDialogProps {
  isOpen: boolean;
  onClose: () => void;
  projects: Project[];
  setProjects: (projects: Project[]) => void;
}

export function ProjectsListDialog({ 
  isOpen, 
  onClose, 
  projects,
  setProjects
}: ProjectsListDialogProps) {
  const [isNewProjectDialogOpen, setIsNewProjectDialogOpen] = useState(false);
  const [isEditProjectDialogOpen, setIsEditProjectDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen) return null;

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
    setIsNewProjectDialogOpen(false);
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
    setIsEditProjectDialogOpen(false);
  };

  const handleDeleteProject = (projectId: number) => {
    setProjects(projects.filter(p => p.id !== projectId));
    setIsDetailDialogOpen(false);
  };

  const handleOpenDetailDialog = (project: Project) => {
    setSelectedProject(project);
    setIsDetailDialogOpen(true);
  };

  const handleOpenEditDialog = (project: Project) => {
    // 如果是从详情对话框打开的编辑对话框，先关闭详情对话框
    if (isDetailDialogOpen) {
      setIsDetailDialogOpen(false);
    }
    setSelectedProject(project);
    setIsEditProjectDialogOpen(true);
  };

  // 处理关闭详情对话框，确保能返回到列表
  const handleCloseDetailDialog = () => {
    setIsDetailDialogOpen(false);
    setSelectedProject(null);
  };

  // 处理关闭编辑对话框，确保能返回到列表
  const handleCloseEditDialog = () => {
    setIsEditProjectDialogOpen(false);
    setSelectedProject(null);
  };

  // 处理关闭新建对话框，确保能返回到列表
  const handleCloseNewProjectDialog = () => {
    setIsNewProjectDialogOpen(false);
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
      >
        <div 
          className="bg-card rounded-lg max-w-6xl w-full h-[90vh] overflow-hidden flex flex-col shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 头部 */}
          <div className="flex-shrink-0 flex items-center justify-between p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center">
                <FolderOpen className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold">项目管理</h2>
                <p className="text-sm text-muted-foreground">组织和管理您的研究项目</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                className="bg-[#0F3B6C] hover:bg-[#0a2945]" 
                onClick={() => setIsNewProjectDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                新建项目
              </Button>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* 搜索栏 */}
          <div className="flex-shrink-0 p-4 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索项目..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {/* 项目列表 - 可滚动区域 */}
          <div className="flex-1 min-h-0 overflow-hidden">
            <ScrollArea className="h-full w-full">
              <div className="p-6">
            {filteredProjects.length === 0 ? (
              <div className="text-center py-12">
                <FolderOpen className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground mb-4">
                  {searchQuery ? '没有找到匹配的项目' : '暂无项目'}
                </p>
                {!searchQuery && (
                  <Button 
                    className="bg-[#0F3B6C] hover:bg-[#0a2945]"
                    onClick={() => setIsNewProjectDialogOpen(true)}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    创建第一个项目
                  </Button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {filteredProjects.map((project) => (
                  <Card 
                    key={project.id} 
                    className="p-6 hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => handleOpenDetailDialog(project)}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="h-12 w-12 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center flex-shrink-0">
                          <FolderOpen className="h-6 w-6 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold mb-1 truncate">{project.name}</h3>
                          <p className="text-sm text-muted-foreground line-clamp-2">{project.description}</p>
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
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetailDialog(project);
                        }}
                      >
                        查看详情
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="flex-1"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenEditDialog(project);
                        }}
                      >
                        编辑
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>

      {/* 新建项目对话框 */}
      <NewProjectDialog 
        isOpen={isNewProjectDialogOpen} 
        onClose={handleCloseNewProjectDialog} 
        onCreateProject={handleCreateProject} 
      />
      
      {/* 编辑项目对话框 */}
      <EditProjectDialog 
        isOpen={isEditProjectDialogOpen} 
        onClose={handleCloseEditDialog} 
        onSave={handleSaveProject} 
        project={selectedProject} 
      />
      
      {/* 项目详情对话框 */}
      <ProjectDetailDialog 
        isOpen={isDetailDialogOpen} 
        onClose={handleCloseDetailDialog} 
        project={selectedProject}
        onEdit={handleOpenEditDialog}
        onDelete={handleDeleteProject}
      />
    </>
  );
}

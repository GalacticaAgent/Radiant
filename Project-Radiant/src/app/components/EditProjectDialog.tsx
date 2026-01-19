import React, { useState, useEffect } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Textarea } from '@/app/components/ui/textarea';
import { Badge } from '@/app/components/ui/badge';
import { X, Save, AlertCircle } from 'lucide-react';

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

interface EditProjectDialogProps {
  isOpen: boolean;
  project: Project | null;
  onClose: () => void;
  onSave: (projectId: number, updatedData: Partial<Project>) => void;
}

export function EditProjectDialog({ 
  isOpen, 
  project, 
  onClose, 
  onSave 
}: EditProjectDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'active',
    progress: 0
  });

  const [errors, setErrors] = useState({
    name: '',
    description: ''
  });

  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name,
        description: project.description,
        status: project.status,
        progress: project.progress
      });
      setErrors({ name: '', description: '' });
    }
  }, [project]);

  if (!isOpen || !project) return null;

  const validateForm = () => {
    const newErrors = {
      name: '',
      description: ''
    };

    if (!formData.name.trim()) {
      newErrors.name = '项目名称不能为空';
    } else if (formData.name.length < 2) {
      newErrors.name = '项目名称至少需要2个字符';
    } else if (formData.name.length > 100) {
      newErrors.name = '项目名称不能超过100个字符';
    }

    if (!formData.description.trim()) {
      newErrors.description = '项目描述不能为空';
    } else if (formData.description.length < 5) {
      newErrors.description = '项目描述至少需要5个字符';
    } else if (formData.description.length > 500) {
      newErrors.description = '项目描述不能超过500个字符';
    }

    setErrors(newErrors);
    return !newErrors.name && !newErrors.description;
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    onSave(project.id, {
      name: formData.name,
      description: formData.description,
      status: formData.status,
      progress: formData.progress
    });

    onClose();
  };

  const handleCancel = () => {
    if (project) {
      setFormData({
        name: project.name,
        description: project.description,
        status: project.status,
        progress: project.progress
      });
      setErrors({ name: '', description: '' });
    }
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          handleCancel();
        }
      }}
    >
      <div 
        className="bg-card rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="border-b p-6 bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E]">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">编辑项目</h2>
              <p className="text-blue-100 text-sm">修改项目的基本信息和设置</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCancel}
              className="text-white hover:bg-white/20"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* 内容区 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* 项目名称 */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              项目名称 <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="输入项目名称"
              className={`text-base h-11 ${errors.name ? 'border-red-500' : ''}`}
            />
            {errors.name && (
              <div className="flex items-center gap-1 mt-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>{errors.name}</span>
              </div>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              {formData.name.length}/100 字符
            </p>
          </div>

          {/* 项目描述 */}
          <div>
            <label className="block text-sm font-semibold mb-2">
              项目描述 <span className="text-red-500">*</span>
            </label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="简要描述项目的研究目标和内容"
              className={`min-h-[120px] text-base ${errors.description ? 'border-red-500' : ''}`}
            />
            {errors.description && (
              <div className="flex items-center gap-1 mt-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>{errors.description}</span>
              </div>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              {formData.description.length}/500 字符
            </p>
          </div>

          {/* 项目状态 */}
          <div>
            <label className="block text-sm font-semibold mb-3">项目状态</label>
            <div className="flex gap-3">
              <Button
                variant={formData.status === 'active' ? 'default' : 'outline'}
                onClick={() => setFormData({ ...formData, status: 'active' })}
                className={formData.status === 'active' ? 'bg-[#0F3B6C]' : ''}
              >
                进行中
              </Button>
              <Button
                variant={formData.status === 'review' ? 'default' : 'outline'}
                onClick={() => setFormData({ ...formData, status: 'review' })}
                className={formData.status === 'review' ? 'bg-[#0F3B6C]' : ''}
              >
                审阅中
              </Button>
              <Button
                variant={formData.status === 'completed' ? 'default' : 'outline'}
                onClick={() => setFormData({ ...formData, status: 'completed' })}
                className={formData.status === 'completed' ? 'bg-green-600' : ''}
              >
                已完成
              </Button>
              <Button
                variant={formData.status === 'archived' ? 'default' : 'outline'}
                onClick={() => setFormData({ ...formData, status: 'archived' })}
                className={formData.status === 'archived' ? 'bg-gray-600' : ''}
              >
                已归档
              </Button>
            </div>
          </div>

          {/* 项目进度 */}
          <div>
            <label className="block text-sm font-semibold mb-3">
              项目进度：{formData.progress}%
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={formData.progress}
                onChange={(e) => setFormData({ ...formData, progress: parseInt(e.target.value) })}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0F3B6C]"
              />
              <Input
                type="number"
                min="0"
                max="100"
                value={formData.progress}
                onChange={(e) => {
                  const value = Math.min(100, Math.max(0, parseInt(e.target.value) || 0));
                  setFormData({ ...formData, progress: value });
                }}
                className="w-20 text-center"
              />
            </div>
            <div className="mt-3 h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E] transition-all duration-300"
                style={{ width: `${formData.progress}%` }}
              />
            </div>
          </div>

          {/* 项目信息 */}
          <Card className="p-4 bg-muted/50">
            <h4 className="text-sm font-semibold mb-3 text-muted-foreground">项目信息</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">项目模板：</span>
                <Badge variant="secondary" className="ml-2">{project.template}</Badge>
              </div>
              <div>
                <span className="text-muted-foreground">文献数量：</span>
                <span className="font-medium ml-2">{project.papers} 篇</span>
              </div>
              <div>
                <span className="text-muted-foreground">项目成员：</span>
                <span className="font-medium ml-2">{project.members} 位</span>
              </div>
              <div>
                <span className="text-muted-foreground">最后更新：</span>
                <span className="font-medium ml-2">{project.lastUpdate}</span>
              </div>
            </div>
          </Card>
        </div>

        {/* 底部操作栏 */}
        <div className="border-t p-4 bg-muted/50 flex items-center justify-end gap-3">
          <Button variant="outline" onClick={handleCancel}>
            取消
          </Button>
          <Button
            className="bg-[#0F3B6C]"
            onClick={handleSave}
          >
            <Save className="h-4 w-4 mr-2" />
            保存修改
          </Button>
        </div>
      </div>
    </div>
  );
}

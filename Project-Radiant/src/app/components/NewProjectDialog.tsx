import React, { useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Badge } from '@/app/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { 
  X, 
  FileText, 
  Upload, 
  Sparkles, 
  BookOpen, 
  GraduationCap, 
  Briefcase,
  Presentation,
  FileEdit,
  CheckCircle2
} from 'lucide-react';

interface NewProjectDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateProject: (projectData: any) => void;
}

// 项目模板数据
const projectTemplates = [
  {
    id: 'blank',
    name: '空白项目',
    description: '从零开始创建您的研究项目',
    icon: FileEdit,
    color: 'from-slate-500 to-slate-700',
    category: 'basic'
  },
  {
    id: 'ieee-paper',
    name: 'IEEE 会议论文',
    description: '标准 IEEE 双栏会议论文模板',
    icon: FileText,
    color: 'from-blue-500 to-blue-700',
    category: 'paper',
    popular: true
  },
  {
    id: 'acm-paper',
    name: 'ACM 期刊论文',
    description: 'ACM 标准期刊论文格式',
    icon: FileText,
    color: 'from-cyan-500 to-cyan-700',
    category: 'paper',
    popular: true
  },
  {
    id: 'springer-paper',
    name: 'Springer 论文',
    description: 'Springer LNCS 系列论文模板',
    icon: BookOpen,
    color: 'from-green-500 to-green-700',
    category: 'paper'
  },
  {
    id: 'thesis-phd',
    name: '博士学位论文',
    description: '完整的博士论文结构模板',
    icon: GraduationCap,
    color: 'from-purple-500 to-purple-700',
    category: 'thesis',
    popular: true
  },
  {
    id: 'thesis-master',
    name: '硕士学位论文',
    description: '硕士论文标准格式',
    icon: GraduationCap,
    color: 'from-indigo-500 to-indigo-700',
    category: 'thesis'
  },
  {
    id: 'presentation-beamer',
    name: '学术演示（Beamer）',
    description: '基于 Beamer 的学术演讲幻灯片',
    icon: Presentation,
    color: 'from-orange-500 to-orange-700',
    category: 'presentation'
  },
  {
    id: 'research-proposal',
    name: '研究计划书',
    description: '标准研究项目申请书模板',
    icon: Briefcase,
    color: 'from-pink-500 to-pink-700',
    category: 'other'
  },
  {
    id: 'literature-review',
    name: '文献综述',
    description: '系统性文献综述结构模板',
    icon: BookOpen,
    color: 'from-teal-500 to-teal-700',
    category: 'other'
  },
];

export function NewProjectDialog({ isOpen, onClose, onCreateProject }: NewProjectDialogProps) {
  const [projectName, setProjectName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('templates');
  const [selectedCategory, setSelectedCategory] = useState('all');

  if (!isOpen) return null;

  const categories = [
    { id: 'all', name: '全部模板', count: projectTemplates.length },
    { id: 'paper', name: '学术论文', count: projectTemplates.filter(t => t.category === 'paper').length },
    { id: 'thesis', name: '学位论文', count: projectTemplates.filter(t => t.category === 'thesis').length },
    { id: 'presentation', name: '演示文稿', count: projectTemplates.filter(t => t.category === 'presentation').length },
    { id: 'other', name: '其他类型', count: projectTemplates.filter(t => t.category === 'other').length },
  ];

  const filteredTemplates = selectedCategory === 'all' 
    ? projectTemplates 
    : projectTemplates.filter(t => t.category === selectedCategory);

  const handleCreate = () => {
    if (!projectName.trim()) {
      alert('请输入项目名称');
      return;
    }

    const template = projectTemplates.find(t => t.id === selectedTemplate);
    
    onCreateProject({
      name: projectName,
      template: selectedTemplate || 'blank',
      templateName: template?.name || '空白项目',
      createdAt: new Date().toISOString()
    });

    // 重置状态
    setProjectName('');
    setSelectedTemplate(null);
    setActiveTab('templates');
    onClose();
  };

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
        className="bg-card rounded-lg max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="border-b p-6 flex items-center justify-between bg-gradient-to-r from-[#0F3B6C] to-[#4A2E9E]">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">创建新项目</h2>
            <p className="text-blue-100 text-sm">选择模板或从空白项目开始</p>
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

        {/* 内容区 */}
        <div className="flex-1 overflow-y-auto p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3 mb-6">
              <TabsTrigger value="templates" className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                从模板创建
              </TabsTrigger>
              <TabsTrigger value="blank" className="flex items-center gap-2">
                <FileEdit className="h-4 w-4" />
                空白项目
              </TabsTrigger>
              <TabsTrigger value="upload" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                上传项目
              </TabsTrigger>
            </TabsList>

            {/* 从模板创建 */}
            <TabsContent value="templates" className="space-y-6">
              {/* 项目名称输入 */}
              <div>
                <label className="block text-sm font-semibold mb-2">项目名称 *</label>
                <Input
                  placeholder="例如：我的第一篇论文"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="text-base h-11"
                />
              </div>

              {/* 分类筛选 */}
              <div>
                <label className="block text-sm font-semibold mb-3">选择模板类型</label>
                <div className="flex flex-wrap gap-2 mb-6">
                  {categories.map((cat) => (
                    <Button
                      key={cat.id}
                      variant={selectedCategory === cat.id ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedCategory(cat.id)}
                      className={selectedCategory === cat.id ? 'bg-[#0F3B6C]' : ''}
                    >
                      {cat.name}
                      <Badge variant="secondary" className="ml-2 text-xs">
                        {cat.count}
                      </Badge>
                    </Button>
                  ))}
                </div>
              </div>

              {/* 模板网格 */}
              <div>
                <label className="block text-sm font-semibold mb-3">
                  选择项目模板
                  <span className="text-muted-foreground font-normal ml-2">
                    ({filteredTemplates.length} 个模板)
                  </span>
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredTemplates.map((template) => {
                    const Icon = template.icon;
                    const isSelected = selectedTemplate === template.id;
                    
                    return (
                      <Card
                        key={template.id}
                        className={`p-4 cursor-pointer transition-all hover:shadow-lg relative ${
                          isSelected 
                            ? 'ring-2 ring-[#0F3B6C] shadow-lg' 
                            : 'hover:border-[#0F3B6C]/50'
                        }`}
                        onClick={() => setSelectedTemplate(template.id)}
                      >
                        {template.popular && (
                          <Badge 
                            className="absolute -top-2 -right-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
                          >
                            热门
                          </Badge>
                        )}
                        
                        {isSelected && (
                          <div className="absolute -top-2 -left-2 h-6 w-6 bg-[#0F3B6C] rounded-full flex items-center justify-center">
                            <CheckCircle2 className="h-4 w-4 text-white" />
                          </div>
                        )}

                        <div className={`h-12 w-12 bg-gradient-to-br ${template.color} rounded-lg flex items-center justify-center mb-3`}>
                          <Icon className="h-6 w-6 text-white" />
                        </div>
                        
                        <h4 className="font-semibold mb-1">{template.name}</h4>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {template.description}
                        </p>
                      </Card>
                    );
                  })}
                </div>
              </div>
            </TabsContent>

            {/* 空白项目 */}
            <TabsContent value="blank" className="space-y-6">
              <div className="text-center py-12">
                <div className="h-24 w-24 bg-gradient-to-br from-slate-500 to-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <FileEdit className="h-12 w-12 text-white" />
                </div>
                <h3 className="text-2xl font-bold mb-3">创建空白项目</h3>
                <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                  从零开始构建您的研究项目，完全自定义结构和内容
                </p>

                <div className="max-w-md mx-auto">
                  <label className="block text-sm font-semibold mb-2 text-left">项目名称 *</label>
                  <Input
                    placeholder="例如：我的研究项目"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="text-base h-11 mb-4"
                  />
                  
                </div>
              </div>
            </TabsContent>

            {/* 上传项目 */}
            <TabsContent value="upload" className="space-y-6">
              <div className="text-center py-12">
                <div className="h-24 w-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Upload className="h-12 w-12 text-white" />
                </div>
                <h3 className="text-2xl font-bold mb-3">上传已有项目</h3>
                <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                  从您的计算机上传现有的 LaTeX 项目文件或 ZIP 压缩包
                </p>

                <div className="max-w-md mx-auto space-y-4">
                  <label className="block text-sm font-semibold mb-2 text-left">项目名称 *</label>
                  <Input
                    placeholder="例如：导入的项目"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    className="text-base h-11"
                  />

                  <div className="border-2 border-dashed rounded-lg p-8 hover:border-[#0F3B6C] transition-colors cursor-pointer">
                    <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
                    <p className="text-sm font-medium mb-1">点击上传或拖拽文件至此</p>
                    <p className="text-xs text-muted-foreground">
                      支持 .tex, .zip 文件，最大 50MB
                    </p>
                  </div>

                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* 底部操作栏 - 所有标签页都显示 */}
        <div className="flex-shrink-0 border-t p-6 bg-muted/50">
          {activeTab === 'templates' && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {selectedTemplate ? (
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    已选择模板：{projectTemplates.find(t => t.id === selectedTemplate)?.name}
                  </span>
                ) : (
                  '请选择一个项目模板'
                )}
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={onClose}>
                  取消
                </Button>
                <Button
                  className="bg-[#0F3B6C]"
                  onClick={handleCreate}
                  disabled={!projectName.trim() || !selectedTemplate}
                >
                  创建项目
                </Button>
              </div>
            </div>
          )}
          {activeTab === 'blank' && (
            <div className="flex items-center justify-end gap-3">
              <Button variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button
                className="bg-[#0F3B6C]"
                onClick={() => {
                  setSelectedTemplate('blank');
                  handleCreate();
                }}
                disabled={!projectName.trim()}
              >
                创建空白项目
              </Button>
            </div>
          )}
          {activeTab === 'upload' && (
            <div className="flex items-center justify-end gap-3">
              <Button variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button
                className="bg-[#0F3B6C]"
                disabled={!projectName.trim()}
              >
                上传并创建项目
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

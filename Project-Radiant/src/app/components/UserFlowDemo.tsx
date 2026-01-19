import React, { useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { ArrowRight, Play, CheckCircle, Workflow } from 'lucide-react';
import { PageHeader } from '@/app/components/common/PageHeader';

export function UserFlowDemo() {
  const [activeFlow, setActiveFlow] = useState<'research' | 'review' | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const flows = {
    research: {
      title: '场景一：调研新方向',
      description: '从智能助手搜索到知识图谱探索的完整流程',
      steps: [
        {
          title: '智能助手提问',
          description: '在 Dashboard 智能助手输入框输入"介绍一下 McDonald 的研究方向"',
          visual: '💬 智能助手对话界面',
          action: '输入研究问题'
        },
        {
          title: '生成知识图谱',
          description: 'AI 识别问题后，自动调用知识图谱生成功能，跳转到知识图谱浏览器',
          visual: '🌐 知识图谱浏览器',
          action: '自动跳转并生成'
        },
        {
          title: '探索图谱节点',
          description: '知识图谱显示相关论文、作者、机构等节点，点击节点可查看详细信息',
          visual: '🔗 节点网络可视化',
          action: '交互式探索'
        },
        {
          title: '查看节点总结',
          description: '点击节点详情面板的"总结"按钮，AI 生成该节点的详细分析报告',
          visual: '📊 AI 智能总结',
          action: '生成分析报告'
        },
        {
          title: '探索相关资源',
          description: '使用"探索相关"功能发现更多相关论文和代码，或返回 Dashboard 查看相关问题推荐',
          visual: '🔍 相关资源推荐',
          action: '深度探索'
        }
      ]
    },
    review: {
      title: '场景二：论文打磨',
      description: '使用模拟审稿功能优化论文质量',
      steps: [
        {
          title: '上传论文文件',
          description: '在 Dashboard 智能助手界面，点击附件按钮上传论文文件（PDF/Word）',
          visual: '📎 文件上传功能',
          action: '选择并上传'
        },
        {
          title: '启动模拟审稿',
          description: '文件上传成功后，点击输入框左下角的"模拟审稿"按钮',
          visual: '🧠 模拟审稿按钮',
          action: '启动审稿流程'
        },
        {
          title: '选择审稿人',
          description: '在审稿人选择对话框中，查看不同审稿人的专业领域、严格程度和审稿风格，选择最适合的审稿人',
          visual: '👥 审稿人选择界面',
          action: '选择审稿人'
        },
        {
          title: '查看审稿意见',
          description: '审稿完成后，系统显示带标红的论文内容、详细修改意见和修改建议，按重要程度分类',
          visual: '📝 审稿意见展示',
          action: '查看修改建议'
        },
        {
          title: '应用修改建议',
          description: '点击每条意见的"应用修改"按钮，系统会标记原文并提供修改后的建议文本',
          visual: '✅ 应用修改功能',
          action: '采纳建议'
        }
      ]
    }
  };

  const handleStartFlow = (flow: 'research' | 'review') => {
    setActiveFlow(flow);
    setCurrentStep(0);
  };

  const handleNextStep = () => {
    if (activeFlow && currentStep < flows[activeFlow].steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleReset = () => {
    setActiveFlow(null);
    setCurrentStep(0);
  };

  if (!activeFlow) {
    return (
      <div className="h-full flex flex-col overflow-hidden">
        <div className="flex-shrink-0 p-6 pb-4">
          <PageHeader
            icon={Workflow}
            title="用户流程演示"
            subtitle="选择一个典型场景,查看 Radiant 的完整交互流程"
          />
        </div>
        <ScrollArea className="flex-1 px-6">
          <div className="space-y-6 pb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => handleStartFlow('research')}>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">{flows.research.title}</h3>
              <p className="text-sm text-muted-foreground">{flows.research.description}</p>
            </div>
            <div className="space-y-2 mb-4">
              {flows.research.steps.map((step, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <div className="h-6 w-6 rounded-full bg-[#0F3B6C] text-white flex items-center justify-center text-xs">
                    {i + 1}
                  </div>
                  <span>{step.title}</span>
                </div>
              ))}
            </div>
            <Button className="w-full bg-[#0F3B6C]">
              <Play className="mr-2 h-4 w-4" />
              开始演示
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => handleStartFlow('review')}>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">{flows.review.title}</h3>
              <p className="text-sm text-muted-foreground">{flows.review.description}</p>
            </div>
            <div className="space-y-2 mb-4">
              {flows.review.steps.map((step, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <div className="h-6 w-6 rounded-full bg-[#4A2E9E] text-white flex items-center justify-center text-xs">
                    {i + 1}
                  </div>
                  <span>{step.title}</span>
                </div>
              ))}
            </div>
            <Button className="w-full bg-[#4A2E9E]">
              <Play className="mr-2 h-4 w-4" />
              开始演示
            </Button>
          </Card>
        </div>
          </div>
        </ScrollArea>
      </div>
    );
  }

  const flow = flows[activeFlow];
  const step = flow.steps[currentStep];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex-shrink-0 p-6 pb-4 border-b bg-white">
        <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-1">{flow.title}</h1>
          <p className="text-muted-foreground">{flow.description}</p>
        </div>
        <Button variant="outline" onClick={handleReset}>
          返回选择
        </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden min-h-0">
        <ScrollArea className="h-full w-full">
          <div className="p-6 space-y-6">
          {/* 进度指示器 */}
          <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          {flow.steps.map((s, i) => (
            <React.Fragment key={i}>
              <div className="flex flex-col items-center">
                <div
                  className={`h-10 w-10 rounded-full flex items-center justify-center transition-all ${
                    i < currentStep
                      ? 'bg-green-500 text-white'
                      : i === currentStep
                      ? 'bg-[#0F3B6C] text-white'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {i < currentStep ? <CheckCircle className="h-6 w-6" /> : i + 1}
                </div>
                <span className="text-xs mt-2 text-center max-w-[80px]">{s.title}</span>
              </div>
              {i < flow.steps.length - 1 && (
                <div className={`flex-1 h-1 mx-2 ${i < currentStep ? 'bg-green-500' : 'bg-gray-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </Card>

      {/* 当前步骤详情 */}
      <Card className="p-8">
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">{step.visual}</div>
          <Badge className="mb-4">{step.action}</Badge>
          <h2 className="text-2xl font-bold mb-2">第 {currentStep + 1} 步: {step.title}</h2>
          <p className="text-lg text-muted-foreground">{step.description}</p>
        </div>

        <div className="flex justify-center gap-4">
          {currentStep > 0 && (
            <Button variant="outline" onClick={() => setCurrentStep(currentStep - 1)}>
              上一步
            </Button>
          )}
          {currentStep < flow.steps.length - 1 ? (
            <Button className="bg-[#0F3B6C]" onClick={handleNextStep}>
              下一步
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button className="bg-green-600" onClick={handleReset}>
              <CheckCircle className="mr-2 h-4 w-4" />
              完成演示
            </Button>
          )}
        </div>
      </Card>

      {/* 步骤说明 */}
      <Card className="p-6">
        <h3 className="font-semibold mb-3">流程说明</h3>
        <div className="space-y-2">
          {flow.steps.map((s, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg ${
                i === currentStep ? 'bg-accent border-l-4 border-[#0F3B6C]' : 'bg-muted/50'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="h-6 w-6 rounded-full bg-card border-2 border-border flex items-center justify-center text-xs font-semibold">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{s.title}</div>
                  <div className="text-sm text-muted-foreground">{s.description}</div>
                </div>
                {i <= currentStep && <CheckCircle className="h-5 w-5 text-green-500" />}
              </div>
            </div>
          ))}
        </div>
      </Card>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
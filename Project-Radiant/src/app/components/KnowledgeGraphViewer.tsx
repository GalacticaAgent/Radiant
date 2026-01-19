import React, { useCallback, useState, useRef, useEffect } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Slider } from '@/app/components/ui/slider';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Filter, Layers, Clock, Network, ZoomIn, ZoomOut, Maximize2, Sparkles, Loader2, Search, FileText, Code, User, Building, ExternalLink } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select';
import { SimpleKnowledgeGraph } from '@/app/components/SimpleKnowledgeGraph';
import { PageHeader } from '@/app/components/common/PageHeader';
import { COLORS, ICON_BOX_CLASSES } from '@/app/constants/theme';

interface GraphNode {
  id: string;
  name: string;
  type: 'paper' | 'author' | 'institution' | 'code';
  year?: number;
  citations?: number;
  url?: string; // 跳转链接
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: 'authored' | 'cited' | 'affiliated' | 'implemented';
}

interface KnowledgeGraphViewerProps {
  initialQuery?: string;
}

export function KnowledgeGraphViewer({ initialQuery = '' }: KnowledgeGraphViewerProps) {
  const [timeRange, setTimeRange] = useState([2020]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [layoutType, setLayoutType] = useState('force');
  const [query, setQuery] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [exploreLoading, setExploreLoading] = useState(false);
  const [summary, setSummary] = useState<string>('');
  const [relatedNodes, setRelatedNodes] = useState<GraphNode[]>([]);
  const [showSummaryDialog, setShowSummaryDialog] = useState(false);
  const [showExploreDialog, setShowExploreDialog] = useState(false);
  const [graphData, setGraphData] = useState({
    nodes: [] as GraphNode[],
    links: [] as GraphLink[]
  });
  const graphRef = useRef<any>();

  const handleGenerateGraph = useCallback(async (searchQuery: string) => {
    setLoading(true);
    // 模拟异步请求
    setTimeout(() => {
      const data = {
        nodes: [
          { id: '1', name: 'McDonald et al.', type: 'author' as const, url: 'https://scholar.google.com/citations?user=mcdonald' },
          { id: '2', name: 'Deep Learning in NLP', type: 'paper' as const, year: 2023, citations: 245, url: 'https://arxiv.org/abs/2023.12345' },
          { id: '3', name: 'Stanford NLP Lab', type: 'institution' as const, url: 'https://nlp.stanford.edu/' },
          { id: '4', name: 'Transformer Architecture', type: 'paper' as const, year: 2022, citations: 1203, url: 'https://arxiv.org/abs/1706.03762' },
          { id: '5', name: 'BERT Implementation', type: 'code' as const, url: 'https://github.com/google-research/bert' },
          { id: '6', name: 'GPT-3 Analysis', type: 'paper' as const, year: 2023, citations: 567, url: 'https://arxiv.org/abs/2005.14165' },
          { id: '7', name: 'OpenAI Research', type: 'institution' as const, url: 'https://openai.com/research' },
          { id: '8', name: 'Brown et al.', type: 'author' as const, url: 'https://scholar.google.com/citations?user=brown' },
        ],
        links: [
          { source: '1', target: '2', type: 'authored' as const },
          { source: '1', target: '3', type: 'affiliated' as const },
          { source: '2', target: '4', type: 'cited' as const },
          { source: '4', target: '5', type: 'implemented' as const },
          { source: '8', target: '6', type: 'authored' as const },
          { source: '8', target: '7', type: 'affiliated' as const },
          { source: '6', target: '4', type: 'cited' as const },
        ]
      };
      setGraphData(data);
      setLoading(false);
    }, 1000);
  }, []);

  // 当initialQuery变化时，自动生成图谱
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
      handleGenerateGraph(initialQuery);
    }
  }, [initialQuery, handleGenerateGraph]);

  const getNodeColor = (node: GraphNode) => {
    const colors = {
      paper: '#4A90E2',
      author: '#50C878',
      institution: '#E27A4A',
      code: '#F39C12'
    };
    return colors[node.type];
  };

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);
    // 如果节点有URL，在新标签页打开
    if (node.url) {
      window.open(node.url, '_blank', 'noopener,noreferrer');
    }
  }, []);

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    // 悬停时显示节点详情，但不跳转
    if (node) {
      setSelectedNode(node);
    }
  }, []);

  // 生成节点总结
  const handleGenerateSummary = async (node: GraphNode) => {
    setSummaryLoading(true);
    setShowSummaryDialog(true);
    
    // 模拟AI生成总结
    setTimeout(() => {
      let summaryText = '';
      
      switch (node.type) {
        case 'paper':
          summaryText = `## ${node.name}\n\n**发表年份**: ${node.year || '未知'}\n**引用次数**: ${node.citations || 0}\n\n### 主要内容\n\n这是一篇关于${node.name}的重要学术论文。该论文在相关研究领域产生了${node.citations || 0}次引用，显示了其在学术界的重要影响力。\n\n### 核心贡献\n\n- 提出了创新的理论框架\n- 在实验验证方面取得了突破性进展\n- 为后续研究奠定了重要基础\n\n### 研究意义\n\n该论文的研究成果对相关领域的发展具有重要意义，为未来的研究方向提供了新的思路和方法。`;
          break;
        case 'author':
          summaryText = `## ${node.name}\n\n### 研究背景\n\n${node.name}是一位在相关研究领域具有重要影响力的学者。\n\n### 主要研究方向\n\n- 深度学习与自然语言处理\n- 知识图谱构建与应用\n- 学术研究协作工具开发\n\n### 学术成就\n\n- 发表了多篇高质量学术论文\n- 在多个顶级会议和期刊上发表研究成果\n- 指导了众多优秀的研究生和博士生\n\n### 影响力\n\n${node.name}的研究工作对学术界和工业界都产生了重要影响，是相关领域的领军人物之一。`;
          break;
        case 'institution':
          summaryText = `## ${node.name}\n\n### 机构简介\n\n${node.name}是一个在学术研究和教育领域具有重要地位的机构。\n\n### 研究领域\n\n- 人工智能与机器学习\n- 自然语言处理\n- 计算机视觉\n- 知识图谱技术\n\n### 主要成就\n\n- 在多个研究领域取得了突破性进展\n- 培养了大量优秀的科研人才\n- 与工业界建立了紧密的合作关系\n\n### 影响力\n\n该机构的研究成果在全球范围内产生了重要影响，是相关领域的顶级研究机构之一。`;
          break;
        case 'code':
          summaryText = `## ${node.name}\n\n### 项目简介\n\n${node.name}是一个开源代码项目，为相关研究提供了重要的工具和资源。\n\n### 主要功能\n\n- 实现了核心算法和模型\n- 提供了易于使用的API接口\n- 包含完整的文档和示例\n\n### 技术特点\n\n- 代码结构清晰，易于维护\n- 性能优化，支持大规模数据处理\n- 持续更新，保持与最新研究同步\n\n### 应用场景\n\n该项目广泛应用于学术研究和工业实践中，为相关领域的发展提供了重要的技术支撑。`;
          break;
      }
      
      setSummary(summaryText);
      setSummaryLoading(false);
    }, 1500);
  };

  // 探索相关节点
  const handleExploreRelated = async (node: GraphNode) => {
    setExploreLoading(true);
    setShowExploreDialog(true);
    
    // 模拟查找相关节点
    setTimeout(() => {
      const related = graphData.nodes
        .filter(n => {
          // 查找与当前节点有连接的节点
          const hasConnection = graphData.links.some(
            link => (link.source === node.id && link.target === n.id) ||
                    (link.target === node.id && link.source === n.id)
          );
          return hasConnection && n.id !== node.id;
        })
        .slice(0, 5); // 最多显示5个相关节点
      
      // 如果没有找到相关节点，生成一些示例
      if (related.length === 0) {
        const exampleRelated: GraphNode[] = [
          { id: 'rel1', name: '相关研究论文1', type: 'paper', year: 2023, citations: 120, url: 'https://arxiv.org/abs/2023.example1' },
          { id: 'rel2', name: '相关研究论文2', type: 'paper', year: 2022, citations: 89, url: 'https://arxiv.org/abs/2022.example2' },
          { id: 'rel3', name: '相关代码库', type: 'code', url: 'https://github.com/example/repo' },
        ];
        setRelatedNodes(exampleRelated);
      } else {
        setRelatedNodes(related);
      }
      
      setExploreLoading(false);
    }, 1000);
  };

  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(1.5);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(0.667);
    }
  };

  const handleMaximize = () => {
    if (graphRef.current) {
      graphRef.current.zoom(1);
    }
  };

  return (
    <div className="flex h-full gap-4 p-6 bg-background">
      {/* 主图谱区域 */}
      <div className="flex-1 flex flex-col gap-4">
        {/* 页面标题 */}
        <PageHeader
          icon={Network}
          title="知识图谱浏览器"
          subtitle="可视化探索学术知识网络"
        />

        {/* 搜索和生成区域 */}
        <Card className="p-4 bg-gradient-to-r from-accent/30 to-accent/20 dark:from-accent/20 dark:to-accent/10">
          <div className="flex items-center gap-3">
            <div className={ICON_BOX_CLASSES}>
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1 flex items-center gap-2">
              <Input
                placeholder="输入研究主题，AI将生成知识图谱..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && query.trim() && handleGenerateGraph(query)}
                className="flex-1"
                disabled={loading}
              />
              <Button 
                onClick={() => handleGenerateGraph(query)}
                disabled={loading || !query.trim()}
                className="bg-[#0F3B6C]"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Network className="mr-2 h-4 w-4" />
                    生成图谱
                  </>
                )}
              </Button>
            </div>
          </div>
          {query && !loading && graphData.nodes.length > 0 && (
            <div className="mt-2 text-sm text-muted-foreground">
              已为主题 "<span className="font-semibold text-[#0F3B6C]">{query}</span>" 生成知识图谱
            </div>
          )}
        </Card>

        {/* 控制面板 */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="outline" size="sm">
                <Filter className="mr-2 h-4 w-4" />
                筛选
              </Button>
              <Select onValueChange={setLayoutType} value={layoutType}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="布局">
                    {layoutType === 'force' && '力导向'}
                    {layoutType === 'circular' && '圆形'}
                    {layoutType === 'radial' && '径向'}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="force">力导向</SelectItem>
                  <SelectItem value="circular">圆形</SelectItem>
                  <SelectItem value="radial">径向</SelectItem>
                </SelectContent>
              </Select>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">时间范围:</span>
                <div className="w-48">
                  <Slider
                    value={timeRange}
                    onValueChange={setTimeRange}
                    min={2015}
                    max={2024}
                    step={1}
                  />
                </div>
                <span className="text-sm font-medium">{timeRange[0]}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary">
                <Network className="mr-1 h-3 w-3" />
                {graphData.nodes.length} 节点
              </Badge>
            </div>
          </div>
        </Card>

        {/* 图谱可视化 */}
        {graphData.nodes.length > 0 ? (
          <Card className="flex-1 bg-muted/50 relative overflow-hidden">
            {loading && (
              <div className="absolute inset-0 bg-background/80 flex items-center justify-center z-10">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 animate-spin text-[#0F3B6C] mx-auto mb-4" />
                  <p className="text-sm font-medium">正在生成知识图谱...</p>
                  <p className="text-xs text-muted-foreground mt-1">AI正在分析并抓取相关资源</p>
                </div>
              </div>
            )}
            <SimpleKnowledgeGraph
              nodes={graphData.nodes}
              links={graphData.links}
              onNodeClick={handleNodeClick}
              onNodeHover={handleNodeHover}
            />
          </Card>
        ) : (
          <Card className="flex-1 bg-muted/50 flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="h-24 w-24 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Network className="h-12 w-12 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">开始探索知识图谱</h3>
              <p className="text-muted-foreground mb-6">
                输入研究主题，AI将自动抓取相关的论文、学者、代码和机构信息，生成可视化知识图谱
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <Badge
                  variant="outline"
                  className="cursor-pointer hover:bg-[#0F3B6C] hover:text-white hover:border-[#0F3B6C] transition-colors"
                  onClick={() => {
                    setQuery('Transformer 架构');
                    handleGenerateGraph('Transformer 架构');
                  }}
                >
                  Transformer 架构
                </Badge>
                <Badge
                  variant="outline"
                  className="cursor-pointer hover:bg-[#0F3B6C] hover:text-white hover:border-[#0F3B6C] transition-colors"
                  onClick={() => {
                    setQuery('BERT 预训练模型');
                    handleGenerateGraph('BERT 预训练模型');
                  }}
                >
                  BERT 预训练模型
                </Badge>
                <Badge
                  variant="outline"
                  className="cursor-pointer hover:bg-[#0F3B6C] hover:text-white hover:border-[#0F3B6C] transition-colors"
                  onClick={() => {
                    setQuery('深度学习计算机视觉');
                    handleGenerateGraph('深度学习计算机视觉');
                  }}
                >
                  计算机视觉
                </Badge>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* 节点详情面板 */}
      {selectedNode && (
        <Card className="w-80 p-4">
          <h3 className="font-semibold mb-4">节点详情</h3>
          <div className="space-y-4">
            <div>
              <div className="text-sm text-muted-foreground mb-1">名称</div>
              <div className="font-medium">{selectedNode.name}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground mb-1">类型</div>
              <Badge variant="outline">
                {selectedNode.type === 'paper' && '文献'}
                {selectedNode.type === 'author' && '人员'}
                {selectedNode.type === 'institution' && '机构'}
                {selectedNode.type === 'code' && '代码'}
              </Badge>
            </div>
            {selectedNode.year && (
              <div>
                <div className="text-sm text-muted-foreground mb-1">年份</div>
                <div>{selectedNode.year}</div>
              </div>
            )}
            {selectedNode.citations && (
              <div>
                <div className="text-sm text-muted-foreground mb-1">引用次数</div>
                <div>{selectedNode.citations}</div>
              </div>
            )}
            <div className="pt-4 space-y-2">
              {selectedNode.url && (
                <Button 
                  className="w-full" 
                  size="sm"
                  onClick={() => window.open(selectedNode.url, '_blank', 'noopener,noreferrer')}
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  查看详情
                </Button>
              )}
              <Button className="w-full" size="sm">添加到私有图谱</Button>
              <Button 
                className="w-full" 
                variant="outline" 
                size="sm"
                onClick={() => handleGenerateSummary(selectedNode)}
                disabled={summaryLoading}
              >
                {summaryLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    总结
                  </>
                )}
              </Button>
              <Button 
                className="w-full" 
                variant="outline" 
                size="sm"
                onClick={() => handleExploreRelated(selectedNode)}
                disabled={exploreLoading}
              >
                {exploreLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    探索中...
                  </>
                ) : (
                  <>
                    <Network className="mr-2 h-4 w-4" />
                    探索相关
                  </>
                )}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* 总结对话框 */}
      <Dialog open={showSummaryDialog} onOpenChange={setShowSummaryDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {selectedNode?.name} - 智能总结
            </DialogTitle>
            <DialogDescription>
              AI生成的节点内容总结
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh] pr-4">
            {summaryLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-12 w-12 animate-spin text-[#0F3B6C] mb-4" />
                <p className="text-sm text-muted-foreground">AI正在分析并生成总结...</p>
              </div>
            ) : (
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {summary.split('\n').map((line, i) => {
                    if (line.startsWith('##')) {
                      return <h2 key={i} className="text-lg font-bold mt-4 mb-2 text-[#0F3B6C]">{line.replace('##', '')}</h2>;
                    } else if (line.startsWith('###')) {
                      return <h3 key={i} className="text-base font-semibold mt-3 mb-1">{line.replace('###', '')}</h3>;
                    } else if (line.startsWith('-')) {
                      return <li key={i} className="ml-4">{line.replace('-', '')}</li>;
                    } else if (line.startsWith('**') && line.includes('**')) {
                      const parts = line.split('**');
                      return <p key={i} className="mb-2">{parts.map((part, j) => j % 2 === 1 ? <strong key={j}>{part}</strong> : part)}</p>;
                    } else if (line.trim() === '') {
                      return <br key={i} />;
                    } else {
                      return <p key={i} className="mb-2">{line}</p>;
                    }
                  })}
                </div>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* 探索相关对话框 */}
      <Dialog open={showExploreDialog} onOpenChange={setShowExploreDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              {selectedNode?.name} - 相关资源
            </DialogTitle>
            <DialogDescription>
              发现与当前节点相关的论文、代码和资源
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh]">
            {exploreLoading ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-12 w-12 animate-spin text-[#0F3B6C] mb-4" />
                <p className="text-sm text-muted-foreground">正在探索相关资源...</p>
              </div>
            ) : (
              <div className="space-y-3">
                {relatedNodes.length > 0 ? (
                  relatedNodes.map((node) => (
                    <Card key={node.id} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            {node.type === 'paper' && <FileText className="h-4 w-4 text-blue-500" />}
                            {node.type === 'code' && <Code className="h-4 w-4 text-yellow-500" />}
                            {node.type === 'author' && <User className="h-4 w-4 text-green-500" />}
                            {node.type === 'institution' && <Building className="h-4 w-4 text-orange-500" />}
                            <span className="font-semibold">{node.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {node.type === 'paper' && '论文'}
                              {node.type === 'code' && '代码'}
                              {node.type === 'author' && '作者'}
                              {node.type === 'institution' && '机构'}
                            </Badge>
                          </div>
                          {node.year && (
                            <p className="text-sm text-muted-foreground mb-1">年份: {node.year}</p>
                          )}
                          {node.citations && (
                            <p className="text-sm text-muted-foreground mb-1">引用: {node.citations}</p>
                          )}
                        </div>
                        {node.url && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.open(node.url, '_blank', 'noopener,noreferrer')}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </Card>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Network className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>暂未找到相关资源</p>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}
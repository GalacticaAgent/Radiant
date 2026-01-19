import React, { useState, useMemo } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Badge } from '@/app/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Star, Search, FileText, User, Building, Code, Bookmark, Sparkles, TrendingUp } from 'lucide-react';
import { PageHeader } from '@/app/components/common/PageHeader';

type ItemType = 'paper' | 'author' | 'institution' | 'code';

interface BaseItem {
  id: number;
  isFavorite?: boolean;
}

interface Paper extends BaseItem {
  type: 'paper';
  title: string;
  authors: string;
  year: number;
  citations: number;
  tags: string[];
}

interface Author extends BaseItem {
  type: 'author';
  name: string;
  affiliation: string;
  papers: number;
}

interface Institution extends BaseItem {
  type: 'institution';
  name: string;
  members: number;
  papers: number;
}

interface CodeRepo extends BaseItem {
  type: 'code';
  name: string;
  stars: number;
  language: string;
}

type RecommendedItem = Paper | Author | Institution | CodeRepo;

export function FavoritesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('recommended');
  const [favorites, setFavorites] = useState({
    papers: [
      {
        id: 1,
        title: 'Attention Is All You Need',
        authors: 'Vaswani et al.',
        year: 2017,
        citations: 89234,
        tags: ['Transformer', 'NLP']
      },
      {
        id: 2,
        title: 'BERT: Pre-training of Deep Bidirectional Transformers',
        authors: 'Devlin et al.',
        year: 2018,
        citations: 56789,
        tags: ['BERT', 'Pre-training']
      },
      {
        id: 3,
        title: 'GPT-3: Language Models are Few-Shot Learners',
        authors: 'Brown et al.',
        year: 2020,
        citations: 34567,
        tags: ['GPT', 'Few-shot']
      }
    ],
    authors: [
      { id: 1, name: 'Geoffrey Hinton', affiliation: 'Google DeepMind', papers: 342 },
      { id: 2, name: 'Yann LeCun', affiliation: 'Meta AI', papers: 298 },
      { id: 3, name: 'Yoshua Bengio', affiliation: 'MILA', papers: 456 }
    ],
    institutions: [
      { id: 1, name: 'Stanford NLP Lab', members: 45, papers: 1234 },
      { id: 2, name: 'Google Brain', members: 120, papers: 2345 },
      { id: 3, name: 'OpenAI Research', members: 89, papers: 678 }
    ],
    code: [
      { id: 1, name: 'Transformers Library', stars: 95432, language: 'Python' },
      { id: 2, name: 'BERT Implementation', stars: 34567, language: 'PyTorch' },
      { id: 3, name: 'GPT-2 Model', stars: 23456, language: 'TensorFlow' }
    ]
  });

  // 推荐内容（基于用户收藏和热门内容）
  const [recommendedItems, setRecommendedItems] = useState<RecommendedItem[]>([
    {
      id: 101,
      type: 'paper',
      title: 'LLaMA: Open and Efficient Foundation Language Models',
      authors: 'Touvron et al.',
      year: 2023,
      citations: 12345,
      tags: ['LLM', 'Open Source', 'Efficient'],
      isFavorite: false
    },
    {
      id: 102,
      type: 'paper',
      title: 'ChatGPT: Optimizing Language Models for Dialogue',
      authors: 'OpenAI',
      year: 2022,
      citations: 23456,
      tags: ['ChatGPT', 'Dialogue', 'RLHF'],
      isFavorite: false
    },
    {
      id: 103,
      type: 'paper',
      title: 'Vision Transformer (ViT)',
      authors: 'Dosovitskiy et al.',
      year: 2020,
      citations: 45678,
      tags: ['Vision', 'Transformer', 'CV'],
      isFavorite: false
    },
    {
      id: 201,
      type: 'author',
      name: 'Ilya Sutskever',
      affiliation: 'OpenAI',
      papers: 156,
      isFavorite: false
    },
    {
      id: 202,
      type: 'author',
      name: 'Fei-Fei Li',
      affiliation: 'Stanford University',
      papers: 289,
      isFavorite: false
    },
    {
      id: 203,
      type: 'author',
      name: 'Jürgen Schmidhuber',
      affiliation: 'IDSIA',
      papers: 412,
      isFavorite: false
    },
    {
      id: 301,
      type: 'institution',
      name: 'DeepMind',
      members: 200,
      papers: 3456,
      isFavorite: false
    },
    {
      id: 302,
      type: 'institution',
      name: 'MIT CSAIL',
      members: 180,
      papers: 2890,
      isFavorite: false
    },
    {
      id: 401,
      type: 'code',
      name: 'Hugging Face Transformers',
      stars: 120000,
      language: 'Python',
      isFavorite: false
    },
    {
      id: 402,
      type: 'code',
      name: 'PyTorch Lightning',
      stars: 28000,
      language: 'Python',
      isFavorite: false
    },
    {
      id: 403,
      type: 'code',
      name: 'LangChain',
      stars: 75000,
      language: 'Python',
      isFavorite: false
    }
  ]);

  // 根据搜索查询过滤推荐内容
  const filteredRecommended = useMemo(() => {
    if (!searchQuery.trim()) return recommendedItems;
    
    const query = searchQuery.toLowerCase();
    return recommendedItems.filter(item => {
      if (item.type === 'paper') {
        return item.title.toLowerCase().includes(query) ||
               item.authors.toLowerCase().includes(query) ||
               item.tags.some(tag => tag.toLowerCase().includes(query));
      } else if (item.type === 'author') {
        return item.name.toLowerCase().includes(query) ||
               item.affiliation.toLowerCase().includes(query);
      } else if (item.type === 'institution') {
        return item.name.toLowerCase().includes(query);
      } else if (item.type === 'code') {
        return item.name.toLowerCase().includes(query) ||
               item.language.toLowerCase().includes(query);
      }
      return false;
    });
  }, [searchQuery, recommendedItems]);

  // 处理收藏操作
  const handleToggleFavorite = (item: RecommendedItem) => {
    // 获取当前收藏状态
    const currentItem = recommendedItems.find(rec => rec.id === item.id);
    const currentFavoriteState = currentItem?.isFavorite || false;
    const newFavoriteState = !currentFavoriteState;
    
    // 更新推荐列表中的收藏状态
    setRecommendedItems(prev => 
      prev.map(rec => 
        rec.id === item.id ? { ...rec, isFavorite: newFavoriteState } : rec
      )
    );

    // 如果收藏，添加到收藏列表
    if (newFavoriteState) {
      if (item.type === 'paper') {
        const paper = item as Paper;
        setFavorites(prev => ({
          ...prev,
          papers: [...prev.papers, {
            id: paper.id,
            title: paper.title,
            authors: paper.authors,
            year: paper.year,
            citations: paper.citations,
            tags: paper.tags
          }]
        }));
      } else if (item.type === 'author') {
        const author = item as Author;
        setFavorites(prev => ({
          ...prev,
          authors: [...prev.authors, {
            id: author.id,
            name: author.name,
            affiliation: author.affiliation,
            papers: author.papers
          }]
        }));
      } else if (item.type === 'institution') {
        const inst = item as Institution;
        setFavorites(prev => ({
          ...prev,
          institutions: [...prev.institutions, {
            id: inst.id,
            name: inst.name,
            members: inst.members,
            papers: inst.papers
          }]
        }));
      } else if (item.type === 'code') {
        const repo = item as CodeRepo;
        setFavorites(prev => ({
          ...prev,
          code: [...prev.code, {
            id: repo.id,
            name: repo.name,
            stars: repo.stars,
            language: repo.language
          }]
        }));
      }
    } else {
      // 如果取消收藏，从收藏列表中移除
      if (item.type === 'paper') {
        setFavorites(prev => ({
          ...prev,
          papers: prev.papers.filter(p => p.id !== item.id)
        }));
      } else if (item.type === 'author') {
        setFavorites(prev => ({
          ...prev,
          authors: prev.authors.filter(a => a.id !== item.id)
        }));
      } else if (item.type === 'institution') {
        setFavorites(prev => ({
          ...prev,
          institutions: prev.institutions.filter(i => i.id !== item.id)
        }));
      } else if (item.type === 'code') {
        setFavorites(prev => ({
          ...prev,
          code: prev.code.filter(c => c.id !== item.id)
        }));
      }
    }
  };

  // 渲染推荐项
  const renderRecommendedItem = (item: RecommendedItem) => {
    // 从推荐列表中获取最新的收藏状态
    const currentItem = recommendedItems.find(rec => rec.id === item.id);
    const isFavorite = currentItem?.isFavorite || false;

    if (item.type === 'paper') {
      const paper = item as Paper;
      return (
        <Card key={paper.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  推荐
                </Badge>
              </div>
              <h3 className="font-semibold mb-2">{paper.title}</h3>
              <p className="text-sm text-muted-foreground mb-3">
                {paper.authors} · {paper.year} · 引用 {paper.citations.toLocaleString()} 次
              </p>
              <div className="flex gap-2">
                {paper.tags.map((tag, i) => (
                  <Badge key={i} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => handleToggleFavorite(item)}
            >
              <Star className={`h-5 w-5 ${isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
            </Button>
          </div>
        </Card>
      );
    } else if (item.type === 'author') {
      const author = item as Author;
      return (
        <Card key={author.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <div className="h-12 w-12 bg-[#50C878] rounded-full flex items-center justify-center">
                <User className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    推荐
                  </Badge>
                </div>
                <h3 className="font-semibold mb-1">{author.name}</h3>
                <p className="text-sm text-muted-foreground mb-2">{author.affiliation}</p>
                <Badge variant="outline">{author.papers} 篇论文</Badge>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => handleToggleFavorite(item)}
            >
              <Star className={`h-5 w-5 ${isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
            </Button>
          </div>
        </Card>
      );
    } else if (item.type === 'institution') {
      const inst = item as Institution;
      return (
        <Card key={inst.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <div className="h-12 w-12 bg-[#E27A4A] rounded-lg flex items-center justify-center">
                <Building className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    推荐
                  </Badge>
                </div>
                <h3 className="font-semibold mb-1">{inst.name}</h3>
                <div className="flex gap-2 text-sm text-muted-foreground">
                  <span>{inst.members} 成员</span>
                  <span>·</span>
                  <span>{inst.papers} 论文</span>
                </div>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => handleToggleFavorite(item)}
            >
              <Star className={`h-5 w-5 ${isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
            </Button>
          </div>
        </Card>
      );
    } else if (item.type === 'code') {
      const repo = item as CodeRepo;
      return (
        <Card key={repo.id} className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  推荐
                </Badge>
              </div>
              <h3 className="font-semibold mb-2">{repo.name}</h3>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <Badge variant="outline">{repo.language}</Badge>
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4" />
                  <span>{repo.stars.toLocaleString()} stars</span>
                </div>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={() => handleToggleFavorite(item)}
            >
              <Star className={`h-5 w-5 ${isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
            </Button>
          </div>
        </Card>
      );
    }
    return null;
  };

  return (
    <div className="h-full flex flex-col bg-background overflow-hidden">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
        {/* 固定头部区域 */}
        <div className="flex-shrink-0 p-6 pb-4 space-y-4 bg-background">
          <PageHeader
            icon={Bookmark}
            title="收藏夹"
            subtitle="推荐内容、搜索和收藏管理"
            actions={
              <Button variant="outline">
                <Bookmark className="mr-2 h-4 w-4" />
                管理标签
              </Button>
            }
          />

          {/* 搜索栏 */}
          <Card className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={activeTab === 'recommended' ? '搜索推荐内容...' : '搜索收藏内容...'}
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </Card>

          {/* 分类标签页 */}
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="recommended">
              <Sparkles className="mr-2 h-4 w-4" />
              推荐 ({filteredRecommended.length})
            </TabsTrigger>
            <TabsTrigger value="papers">
              <FileText className="mr-2 h-4 w-4" />
              文献 ({favorites.papers.length})
            </TabsTrigger>
            <TabsTrigger value="authors">
              <User className="mr-2 h-4 w-4" />
              作者 ({favorites.authors.length})
            </TabsTrigger>
            <TabsTrigger value="institutions">
              <Building className="mr-2 h-4 w-4" />
              机构 ({favorites.institutions.length})
            </TabsTrigger>
            <TabsTrigger value="code">
              <Code className="mr-2 h-4 w-4" />
              代码 ({favorites.code.length})
            </TabsTrigger>
          </TabsList>
        </div>

        {/* 可滚动内容区域 */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="px-6 py-4">
            {/* 推荐标签页 */}
            <TabsContent value="recommended" className="space-y-4">
          {filteredRecommended.length === 0 ? (
            <Card className="p-8 text-center">
              <Sparkles className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">
                {searchQuery ? '没有找到匹配的推荐内容' : '暂无推荐内容'}
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* 按类型分组显示 */}
              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  推荐文献
                </h3>
                <div className="space-y-3">
                  {filteredRecommended
                    .filter(item => item.type === 'paper')
                    .map(item => renderRecommendedItem(item))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground flex items-center gap-2">
                  <User className="h-4 w-4" />
                  推荐作者
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredRecommended
                    .filter(item => item.type === 'author')
                    .map(item => renderRecommendedItem(item))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  推荐机构
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredRecommended
                    .filter(item => item.type === 'institution')
                    .map(item => renderRecommendedItem(item))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold mb-3 text-muted-foreground flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  推荐代码
                </h3>
                <div className="space-y-3">
                  {filteredRecommended
                    .filter(item => item.type === 'code')
                    .map(item => renderRecommendedItem(item))}
                </div>
              </div>
            </div>
            )}
            </TabsContent>

            <TabsContent value="papers" className="space-y-4">
          {favorites.papers.map((paper) => (
            <Card key={paper.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold mb-2">{paper.title}</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    {paper.authors} · {paper.year} · 引用 {paper.citations.toLocaleString()} 次
                  </p>
                  <div className="flex gap-2">
                    {paper.tags.map((tag, i) => (
                      <Badge key={i} variant="secondary">{tag}</Badge>
                    ))}
                  </div>
                </div>
                <Button variant="ghost" size="icon">
                  <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                </Button>
              </div>
            </Card>
            ))}
            </TabsContent>

            <TabsContent value="authors" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {favorites.authors.map((author) => (
              <Card key={author.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="h-12 w-12 bg-[#50C878] rounded-full flex items-center justify-center">
                      <User className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{author.name}</h3>
                      <p className="text-sm text-muted-foreground mb-2">{author.affiliation}</p>
                      <Badge variant="outline">{author.papers} 篇论文</Badge>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  </Button>
                </div>
              </Card>
            ))}
            </div>
            </TabsContent>

            <TabsContent value="institutions" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {favorites.institutions.map((inst) => (
              <Card key={inst.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="h-12 w-12 bg-[#E27A4A] rounded-lg flex items-center justify-center">
                      <Building className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{inst.name}</h3>
                      <div className="flex gap-2 text-sm text-muted-foreground">
                        <span>{inst.members} 成员</span>
                        <span>·</span>
                        <span>{inst.papers} 论文</span>
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  </Button>
                </div>
              </Card>
            ))}
            </div>
            </TabsContent>

            <TabsContent value="code" className="space-y-4">
          {favorites.code.map((repo) => (
            <Card key={repo.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold mb-2">{repo.name}</h3>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <Badge variant="outline">{repo.language}</Badge>
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4" />
                      <span>{repo.stars.toLocaleString()} stars</span>
                    </div>
                  </div>
                </div>
                <Button variant="ghost" size="icon">
                  <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                </Button>
              </div>
            </Card>
            ))}
            </TabsContent>
            </div>
          </ScrollArea>
        </div>
      </Tabs>
    </div>
  );
}
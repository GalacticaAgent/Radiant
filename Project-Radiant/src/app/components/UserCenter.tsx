import React, { useState, useEffect } from 'react';
import { Card } from '@/app/components/ui/card';
import { Input } from '@/app/components/ui/input';
import { Button } from '@/app/components/ui/button';
import { Label } from '@/app/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { Badge } from '@/app/components/ui/badge';
import { Avatar, AvatarFallback } from '@/app/components/ui/avatar';
import { 
  User, 
  Mail, 
  Shield, 
  History, 
  Settings,
  FileText,
  TrendingUp,
  Award,
  Calendar,
  Loader2,
  CheckCircle,
  AlertCircle,
  BookOpen,
} from 'lucide-react';
import { userService, reviewService } from '@/utils/api/services';
import { ApiError } from '@/utils/api/client';

interface UserCenterProps {
  userToken: string;
  user: any;
  onOpenTutorial?: () => void;
}

export function UserCenter({ userToken, user, onOpenTutorial }: UserCenterProps) {
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState(user?.user_metadata?.name || '');
  const [reviewHistory, setReviewHistory] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalReviews: 0,
    avgScore: 0,
    recentActivity: 0,
  });

  useEffect(() => {
    fetchReviewHistory();
  }, []);

  const fetchReviewHistory = async () => {
    try {
      const data = await reviewService.getHistory(userToken);
      
      if (data.history) {
        setReviewHistory(data.history);
        
        // 计算统计数据
        const total = data.history.length;
        const avgScore = total > 0
          ? data.history.reduce((sum: number, item: any) => sum + item.score.overall, 0) / total
          : 0;
        
        setStats({
          totalReviews: total,
          avgScore: Math.round(avgScore * 10) / 10,
          recentActivity: data.history.filter((item: any) => {
            const reviewDate = new Date(item.timestamp);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return reviewDate > weekAgo;
          }).length,
        });
      }
    } catch (error) {
      console.error('获取审稿历史错误:', error);
      if (error instanceof ApiError) {
        console.error('API错误:', error.message);
      }
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await userService.updateProfile(userToken, { name });
      alert('个人信息更新成功！');
    } catch (error: any) {
      console.error('更新个人信息错误:', error);
      if (error instanceof ApiError) {
        alert(`更新失败: ${error.message}`);
      } else {
        alert('更新失败，请重试');
      }
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="h-full p-6 bg-background overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* 页面标题 */}
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] rounded-lg flex items-center justify-center">
            <User className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">用户中心</h1>
            <p className="text-sm text-muted-foreground">管理您的个人信息和账户设置</p>
          </div>
        </div>

        {/* 用户信息卡片 */}
        <Card className="p-6">
          <div className="flex items-start gap-6">
            <Avatar className="h-24 w-24 border-4 border-[#0F3B6C]">
              <AvatarFallback className="bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] text-white text-2xl">
                {getInitials(name || user?.email || 'User')}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">{name || '未设置姓名'}</h2>
              <div className="flex items-center gap-2 text-muted-foreground mb-4">
                <Mail className="h-4 w-4" />
                <span>{user?.email}</span>
              </div>
              <div className="flex gap-2">
                <Badge variant="secondary" className="bg-[#0F3B6C] text-white">
                  <Shield className="h-3 w-3 mr-1" />
                  已验证
                </Badge>
                <Badge variant="secondary">
                  <Calendar className="h-3 w-3 mr-1" />
                  加入于 {new Date(user?.created_at).toLocaleDateString('zh-CN')}
                </Badge>
              </div>
            </div>
          </div>
        </Card>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <FileText className="h-5 w-5 text-[#0F3B6C]" />
              </div>
              <TrendingUp className="h-4 w-4 text-green-600" />
            </div>
            <div className="text-3xl font-bold mb-1">{stats.totalReviews}</div>
            <div className="text-sm text-muted-foreground">总审稿次数</div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Award className="h-5 w-5 text-[#4A2E9E]" />
              </div>
            </div>
            <div className="text-3xl font-bold mb-1">{stats.avgScore}</div>
            <div className="text-sm text-muted-foreground">平均得分</div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                <History className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <div className="text-3xl font-bold mb-1">{stats.recentActivity}</div>
            <div className="text-sm text-muted-foreground">近7天活跃</div>
          </Card>
        </div>

        {/* 详细信息标签页 */}
        <Card className="p-6">
          <Tabs defaultValue="profile" className="w-full">
            <TabsList className="grid w-full grid-cols-3 mb-6">
              <TabsTrigger value="profile">
                <User className="h-4 w-4 mr-2" />
                个人信息
              </TabsTrigger>
              <TabsTrigger value="history">
                <History className="h-4 w-4 mr-2" />
                审稿历史
              </TabsTrigger>
              <TabsTrigger value="settings">
                <Settings className="h-4 w-4 mr-2" />
                设置
              </TabsTrigger>
            </TabsList>

            <TabsContent value="profile">
              <form onSubmit={handleUpdateProfile} className="space-y-4 max-w-md">
                <div className="space-y-2">
                  <Label htmlFor="name">姓名</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="请输入您的姓名"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={loading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">邮箱</Label>
                  <Input
                    id="email"
                    type="email"
                    value={user?.email}
                    disabled
                    className="bg-muted"
                  />
                  <p className="text-xs text-muted-foreground">邮箱地址不可修改</p>
                </div>

                <div className="space-y-2">
                  <Label>用户ID</Label>
                  <Input
                    value={user?.id}
                    disabled
                    className="bg-muted font-mono text-xs"
                  />
                </div>

                <Button
                  type="submit"
                  className="bg-[#0F3B6C] hover:bg-[#0a2945]"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      保存中...
                    </>
                  ) : (
                    '保存修改'
                  )}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="history">
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">审稿历史记录</h3>
                  <Badge variant="secondary">{reviewHistory.length} 条记录</Badge>
                </div>

                {reviewHistory.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>暂无审稿记录</p>
                    <p className="text-sm mt-2">前往仪表盘开始使用模拟审稿功能</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {reviewHistory.map((item, index) => (
                      <Card key={item.id || index} className="p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline" className="text-xs">
                                {item.reviewType === 'comprehensive' ? '综合审稿' :
                                 item.reviewType === 'methodology' ? '方法论审查' : '语言润色'}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(item.timestamp)}
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground mb-3">
                              {item.contentPreview}...
                            </p>
                            <div className="flex items-center gap-4 text-sm">
                              <div className="flex items-center gap-1">
                                <CheckCircle className="h-4 w-4 text-green-600" />
                                <span className="text-muted-foreground">优点: {item.strengths.length}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <AlertCircle className="h-4 w-4 text-amber-600" />
                                <span className="text-muted-foreground">待改进: {item.weaknesses.length}</span>
                              </div>
                            </div>
                          </div>
                          <div className="text-center ml-4">
                            <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[#0F3B6C] to-[#4A2E9E] flex items-center justify-center">
                              <div className="text-white">
                                <div className="text-2xl font-bold">{item.score.overall}</div>
                                <div className="text-xs opacity-80">总分</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="settings">
              <div className="space-y-6 max-w-md">
                <div>
                  <h3 className="text-lg font-semibold mb-4">账户设置</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">邮箱通知</div>
                        <div className="text-sm text-muted-foreground">接收审稿结果和更新通知</div>
                      </div>
                      <Button variant="outline" size="sm">
                        启用
                      </Button>
                    </div>

                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">双因素认证</div>
                        <div className="text-sm text-muted-foreground">增强账户安全性</div>
                      </div>
                      <Button variant="outline" size="sm">
                        设置
                      </Button>
                    </div>

                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">数据导出</div>
                        <div className="text-sm text-muted-foreground">下载您的审稿历史数据</div>
                      </div>
                      <Button variant="outline" size="sm">
                        导出
                      </Button>
                    </div>

                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">查看引导教程</div>
                        <div className="text-sm text-muted-foreground">重新查看平台使用教程和功能演示</div>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={onOpenTutorial}
                      >
                        <BookOpen className="h-4 w-4 mr-2" />
                        查看教程
                      </Button>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-4 text-red-600">危险操作</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border border-red-200 rounded-lg bg-red-50">
                      <div>
                        <div className="font-medium text-red-900">删除账户</div>
                        <div className="text-sm text-red-700">永久删除您的账户和所有数据</div>
                      </div>
                      <Button variant="destructive" size="sm">
                        删除
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );
}
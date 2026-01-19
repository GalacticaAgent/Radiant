import React, { useEffect, useRef, useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface GraphNode {
  id: string;
  name: string;
  type: 'paper' | 'author' | 'institution' | 'code';
  year?: number;
  citations?: number;
  url?: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: 'authored' | 'cited' | 'affiliated' | 'implemented';
}

interface SimpleKnowledgeGraphProps {
  nodes: Array<{
    id: string;
    name: string;
    type: 'paper' | 'author' | 'institution' | 'code';
    year?: number;
    citations?: number;
    url?: string;
  }>;
  links: GraphLink[];
  onNodeClick?: (node: any) => void;
  onNodeHover?: (node: any) => void;
}

export function SimpleKnowledgeGraph({ nodes: initialNodes, links, onNodeClick, onNodeHover }: SimpleKnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const animationRef = useRef<number>();

  const width = 1200;
  const height = 600;

  // 初始化节点位置
  useEffect(() => {
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 200;

    const initializedNodes = initialNodes.map((node, index) => {
      const angle = (index / initialNodes.length) * 2 * Math.PI;
      return {
        ...node,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        vx: 0,
        vy: 0
      };
    });

    setNodes(initializedNodes);
  }, [initialNodes]);

  // 力导向布局模拟
  useEffect(() => {
    if (nodes.length === 0) return;

    const simulate = () => {
      setNodes(prevNodes => {
        const newNodes = [...prevNodes];
        
        // 斥力
        for (let i = 0; i < newNodes.length; i++) {
          for (let j = i + 1; j < newNodes.length; j++) {
            const dx = newNodes[j].x - newNodes[i].x;
            const dy = newNodes[j].y - newNodes[i].y;
            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = 50000 / (distance * distance);
            
            newNodes[i].vx -= (dx / distance) * force;
            newNodes[i].vy -= (dy / distance) * force;
            newNodes[j].vx += (dx / distance) * force;
            newNodes[j].vy += (dy / distance) * force;
          }
        }

        // 引力（连接的节点）
        links.forEach(link => {
          const source = newNodes.find(n => n.id === link.source);
          const target = newNodes.find(n => n.id === link.target);
          
          if (source && target) {
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = distance * 0.01;
            
            source.vx += (dx / distance) * force;
            source.vy += (dy / distance) * force;
            target.vx -= (dx / distance) * force;
            target.vy -= (dy / distance) * force;
          }
        });

        // 中心引力
        const centerX = width / 2;
        const centerY = height / 2;
        newNodes.forEach(node => {
          const dx = centerX - node.x;
          const dy = centerY - node.y;
          node.vx += dx * 0.001;
          node.vy += dy * 0.001;
        });

        // 更新位置
        newNodes.forEach(node => {
          node.vx *= 0.8; // 阻尼
          node.vy *= 0.8;
          node.x += node.vx;
          node.y += node.vy;
        });

        return newNodes;
      });

      animationRef.current = requestAnimationFrame(simulate);
    };

    animationRef.current = requestAnimationFrame(simulate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [nodes.length, links]);

  // 绘制图谱
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 检测是否为暗色模式
    const isDark = document.documentElement.classList.contains('dark');

    const draw = () => {
      // 清空画布 - 根据主题设置背景色
      ctx.fillStyle = isDark ? '#0a0a0a' : '#f8fafc';
      ctx.fillRect(0, 0, width, height);

      ctx.save();
      ctx.translate(offset.x, offset.y);
      ctx.scale(zoom, zoom);

      // 绘制连接线 - 根据主题设置颜色
      ctx.strokeStyle = isDark ? '#475569' : '#cbd5e1';
      ctx.lineWidth = 2;
      links.forEach(link => {
        const source = nodes.find(n => n.id === link.source);
        const target = nodes.find(n => n.id === link.target);

        if (source && target) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.stroke();

          // 绘制箭头
          const angle = Math.atan2(target.y - source.y, target.x - source.x);
          const arrowLength = 10;
          const arrowX = target.x - Math.cos(angle) * 30;
          const arrowY = target.y - Math.sin(angle) * 30;

          ctx.beginPath();
          ctx.moveTo(arrowX, arrowY);
          ctx.lineTo(
            arrowX - arrowLength * Math.cos(angle - Math.PI / 6),
            arrowY - arrowLength * Math.sin(angle - Math.PI / 6)
          );
          ctx.moveTo(arrowX, arrowY);
          ctx.lineTo(
            arrowX - arrowLength * Math.cos(angle + Math.PI / 6),
            arrowY - arrowLength * Math.sin(angle + Math.PI / 6)
          );
          ctx.stroke();
        }
      });

      // 绘制节点
      nodes.forEach(node => {
        const colors = {
          paper: '#4A90E2',
          author: '#50C878',
          institution: '#E27A4A',
          code: '#F39C12'
        };

        const radius = 25;
        const isHovered = hoveredNode?.id === node.id;

        // 节点圆圈 - 悬停时放大并添加阴影
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius * (isHovered ? 1.2 : 1), 0, 2 * Math.PI);
        ctx.fillStyle = colors[node.type];
        ctx.fill();
        
        // 悬停时的外圈高亮
        if (isHovered) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius * 1.4, 0, 2 * Math.PI);
          ctx.strokeStyle = colors[node.type];
          ctx.lineWidth = 2;
          ctx.globalAlpha = 0.3;
          ctx.stroke();
          ctx.globalAlpha = 1.0;
        }
        
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();

        // 节点文字背景 - 根据主题设置
        ctx.font = '12px sans-serif';
        const textWidth = ctx.measureText(node.name).width;
        ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(255, 255, 255, 0.9)';
        ctx.fillRect(
          node.x - textWidth / 2 - 4,
          node.y + radius + 5,
          textWidth + 8,
          18
        );

        // 节点文字 - 根据主题设置颜色
        ctx.fillStyle = isDark ? '#e2e8f0' : '#334155';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(node.name, node.x, node.y + radius + 8);
      });

      ctx.restore();
    };

    draw();
    const interval = setInterval(draw, 50);

    // 监听主题变化
    const observer = new MutationObserver(() => {
      draw();
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    return () => {
      clearInterval(interval);
      observer.disconnect();
    };
  }, [nodes, links, zoom, offset, hoveredNode]);

  // 获取鼠标位置下的节点
  const getNodeAtPosition = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - offset.x) / zoom;
    const y = (e.clientY - rect.top - offset.y) / zoom;

    return nodes.find(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      return Math.sqrt(dx * dx + dy * dy) < 25;
    }) || null;
  };

  // 处理画布点击
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const clickedNode = getNodeAtPosition(e);
    if (clickedNode && onNodeClick) {
      onNodeClick(clickedNode);
    }
  };

  // 处理鼠标移动（悬停检测）
  const handleMouseMoveForHover = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      handleMouseMove(e);
      return;
    }

    const nodeAtPosition = getNodeAtPosition(e);
    if (nodeAtPosition !== hoveredNode) {
      setHoveredNode(nodeAtPosition);
      if (onNodeHover) {
        onNodeHover(nodeAtPosition);
      }
    }
  };

  // 处理鼠标离开画布
  const handleMouseLeave = () => {
    setIsDragging(false);
    setHoveredNode(null);
    if (onNodeHover) {
      onNodeHover(null);
    }
  };

  // 处理鼠标拖拽
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const nodeAtPosition = getNodeAtPosition(e);
    // 如果点击的是节点，不启动拖拽
    if (nodeAtPosition) {
      return;
    }
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className="relative w-full h-full">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleCanvasClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMoveForHover}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        className="w-full h-full"
        style={{ 
          maxWidth: '100%', 
          maxHeight: '100%',
          cursor: hoveredNode ? 'pointer' : isDragging ? 'grabbing' : 'grab'
        }}
      />
      
      {/* 缩放控制 */}
      <div className="absolute bottom-4 right-4 flex gap-2">
        <Button
          size="sm"
          variant="outline"
          className="bg-card"
          onClick={() => setZoom(Math.min(zoom * 1.2, 3))}
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="bg-card"
          onClick={() => setZoom(Math.max(zoom / 1.2, 0.3))}
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="bg-card"
          onClick={() => {
            setZoom(1);
            setOffset({ x: 0, y: 0 });
          }}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>

      {/* 图例 */}
      <div className="absolute top-4 right-4 bg-card rounded-lg p-3 shadow-md border">
        <div className="text-xs font-semibold mb-2">节点类型</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#4A90E2]"></div>
            <span className="text-xs">论文</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#50C878]"></div>
            <span className="text-xs">作者</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#E27A4A]"></div>
            <span className="text-xs">机构</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#F39C12]"></div>
            <span className="text-xs">代码</span>
          </div>
        </div>
      </div>
    </div>
  );
}

# Radiant（元光体）- 学术研究 Agent 项目

## 项目简介

Radiant 是一个知识图谱原生的科研 Agent Web 应用，专门为学术研究开发。通过整合知识图谱、AI 大模型和多源数据爬取，帮助科研人员进行文献调研、Idea 检验和论文打磨。

## 项目结构

```
demo01/
├── PROJECT_PLAN.md              # 项目总体实现计划
├── README.md                    # 本文件
├── frontend/                    # 前端项目
│   └── FRONTEND_REQUIREMENTS.md # 前端开发需求文档
├── backend/                     # 后端项目
│   └── BACKEND_REQUIREMENTS.md  # 后端开发需求文档
├── database/                    # 数据库设计
│   └── DATABASE_REQUIREMENTS.md # 数据库需求文档
└── api/                         # DeepSeek API 集成
    └── API_REQUIREMENTS.md      # API 集成需求文档
```

## 核心功能

1. **知识图谱维护**：自动爬取学术信息并构建知识图谱
2. **子图提取**：按需求提取相关研究子图
3. **调研功能**：快速了解新研究方向
4. **Idea 检验**：评估研究想法的可行性
5. **审稿人角色扮演**：模拟审稿人视角
6. **论文撰写**：基于审稿意见生成修改建议
7. **私有知识图谱**：用户可创建私有图谱

## 技术栈

### 前端
- React 18 + TypeScript
- Ant Design / Material-UI
- Cytoscape.js (知识图谱可视化)
- Zustand / Redux Toolkit

### 后端
- Python 3.10+
- FastAPI
- Celery + Redis (异步任务)
- Scrapy (爬虫)

### 数据库
- Neo4j (知识图谱)
- PostgreSQL (用户数据)
- Redis (缓存)

### AI
- DeepSeek API (主要 LLM)
- LangChain (Agent 编排)

## 快速开始

### 1. 阅读文档

建议按以下顺序阅读文档：

1. `PROJECT_PLAN.md` - 了解项目整体规划和实现步骤
2. `database/DATABASE_REQUIREMENTS.md` - 了解数据库设计
3. `backend/BACKEND_REQUIREMENTS.md` - 了解后端架构和 API
4. `frontend/FRONTEND_REQUIREMENTS.md` - 了解前端界面和交互
5. `api/API_REQUIREMENTS.md` - 了解 DeepSeek API 集成方案

### 2. 环境准备

参考 `PROJECT_PLAN.md` 中的"阶段一：项目初始化与架构搭建"章节。

### 3. 多人协作

每个模块（前端、后端、数据库、API）都有独立的需求文档，可以分配给不同的开发人员：

- **前端开发**：参考 `frontend/FRONTEND_REQUIREMENTS.md`
- **后端开发**：参考 `backend/BACKEND_REQUIREMENTS.md`
- **数据库工程师**：参考 `database/DATABASE_REQUIREMENTS.md`
- **AI 集成**：参考 `api/API_REQUIREMENTS.md`

## 开发阶段

项目分为 6 个主要阶段，预计 16 周完成：

- **阶段一**（第 1-2 周）：项目初始化与架构搭建
- **阶段二**（第 3-4 周）：数据库设计与知识图谱建模
- **阶段三**（第 5-10 周）：后端核心功能开发
- **阶段四**（第 8-12 周）：前端界面开发
- **阶段五**（第 13-14 周）：系统集成与测试
- **阶段六**（第 15-16 周）：部署与上线

详细的时间线和里程碑请参考 `PROJECT_PLAN.md`。

## 典型使用场景

### 场景 1：调研新方向
用户输入"请你介绍一下深度学习"，系统自动爬取相关文献、研究者信息，构建知识图谱并生成总结。

### 场景 2：检验 Idea 可行性
用户提出新的研究想法，系统搜索相关文献，评估可行性并给出建议。

### 场景 3：论文打磨
用户上传论文初稿，系统推荐审稿人、生成审稿意见，并提供修改建议。

## 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请提交 Issue。

---

**祝开发顺利！**

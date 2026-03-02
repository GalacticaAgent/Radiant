// Radiant 项目 Neo4j 数据库初始化脚本
// 创建约束 - 确保节点 ID 的唯一性

// Paper 节点约束
CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;

// Person 节点约束
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;

// Organization 节点约束
CREATE CONSTRAINT org_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE;

// Code 节点约束
CREATE CONSTRAINT code_id_unique IF NOT EXISTS FOR (c:Code) REQUIRE c.id IS UNIQUE;

// 创建索引 - 提高查询性能

// Paper 节点索引
CREATE INDEX paper_title IF NOT EXISTS FOR (p:Paper) ON (p.title);
CREATE INDEX paper_arxiv_id IF NOT EXISTS FOR (p:Paper) ON (p.arxiv_id);
CREATE INDEX paper_doi IF NOT EXISTS FOR (p:Paper) ON (p.doi);
CREATE INDEX paper_year IF NOT EXISTS FOR (p:Paper) ON (p.year);

// Person 节点索引
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX person_email IF NOT EXISTS FOR (p:Person) ON (p.email);

// Organization 节点索引
CREATE INDEX org_name IF NOT EXISTS FOR (o:Organization) ON (o.name);

// Code 节点索引
CREATE INDEX code_github_url IF NOT EXISTS FOR (c:Code) ON (c.github_url);
CREATE INDEX code_name IF NOT EXISTS FOR (c:Code) ON (c.name);

// 全文搜索索引 - 用于论文内容搜索
CREATE FULLTEXT INDEX paper_fulltext IF NOT EXISTS
FOR (p:Paper)
ON EACH [p.title, p.abstract];

// 插入示例数据（用于测试，可选）

// 创建示例论文节点
MERGE (p1:Paper {
    id: "paper-transformer-2017",
    title: "Attention Is All You Need",
    abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
    year: 2017,
    venue: "NeurIPS",
    arxiv_id: "1706.03762",
    doi: "10.48550/arXiv.1706.03762",
    url: "https://arxiv.org/abs/1706.03762",
    citations: 50000,
    keywords: ["transformer", "attention mechanism", "neural networks", "NLP"],
    created_at: datetime(),
    updated_at: datetime()
});

// 创建示例研究者节点
MERGE (author1:Person {
    id: "person-ashish-vaswani",
    name: "Ashish Vaswani",
    affiliation: "Google Brain",
    research_interests: ["Deep Learning", "NLP", "Transformers"],
    created_at: datetime(),
    updated_at: datetime()
});

MERGE (author2:Person {
    id: "person-noam-shazeer",
    name: "Noam Shazeer",
    affiliation: "Google Brain",
    research_interests: ["Machine Learning", "Neural Networks"],
    created_at: datetime(),
    updated_at: datetime()
});

// 创建示例机构节点
MERGE (org:Organization {
    id: "org-google-brain",
    name: "Google Brain",
    type: "research_institute",
    country: "USA",
    website: "https://research.google/teams/brain/",
    created_at: datetime()
});

// 创建关系
MATCH (author:Person {id: "person-ashish-vaswani"}), (paper:Paper {id: "paper-transformer-2017"})
MERGE (author)-[:AUTHORED {position: 1}]->(paper);

MATCH (author:Person {id: "person-noam-shazeer"}), (paper:Paper {id: "paper-transformer-2017"})
MERGE (author)-[:AUTHORED {position: 2}]->(paper);

MATCH (author:Person {id: "person-ashish-vaswani"}), (org:Organization {id: "org-google-brain"})
MERGE (author)-[:WORKS_AT {position: "Research Scientist"}]->(org);

MATCH (author:Person {id: "person-noam-shazeer"}), (org:Organization {id: "org-google-brain"})
MERGE (author)-[:WORKS_AT {position: "Senior Research Scientist"}]->(org);

MATCH (paper:Paper {id: "paper-transformer-2017"}), (org:Organization {id: "org-google-brain"})
MERGE (paper)-[:BELONGS_TO]->(org);

// 创建示例代码节点
MERGE (code:Code {
    id: "code-transformers-huggingface",
    name: "transformers",
    description: "State-of-the-art Machine Learning for PyTorch, TensorFlow, and JAX",
    github_url: "https://github.com/huggingface/transformers",
    language: "Python",
    stars: 100000,
    forks: 20000,
    topics: ["transformers", "nlp", "pytorch", "tensorflow"],
    created_at: datetime(),
    updated_at: datetime()
});

MATCH (code:Code {id: "code-transformers-huggingface"}), (paper:Paper {id: "paper-transformer-2017"})
MERGE (code)-[:IMPLEMENTS]->(paper);

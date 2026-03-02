import { useEffect, useRef, useState } from 'react'
import { AppLayout } from '../../components/Layout'
import cytoscape from 'cytoscape'
import { App, Input, Button, Select, Drawer, Descriptions, Tag, Tooltip, Spin, Space } from 'antd'
import { SearchOutlined, FilterOutlined, ZoomInOutlined, ZoomOutOutlined, ExpandOutlined, NodeIndexOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { graphAPI } from '../../api/graph'
import './KnowledgeGraph.css'

const { Option } = Select

export default function KnowledgeGraph() {
  const { message } = App.useApp()
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('graph')
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const loadGraph = async (q: string) => {
    if (!cyRef.current || cyRef.current.destroyed()) return
    setLoading(true)
    try {
      const data = await graphAPI.subgraph(q, 2, 120, typeFilter === 'all' ? undefined : typeFilter)
      const elements: cytoscape.ElementDefinition[] = [
        ...data.nodes.map((n: any) => ({ data: { id: n.id, label: n.label, type: n.type, properties: n.properties } })),
        ...data.edges.map((e: any) => ({
          data: { id: `${e.source}-${e.type}-${e.target}`, source: e.source, target: e.target, type: e.type },
        })),
      ]
      cyRef.current.elements().remove()
      cyRef.current.add(elements)
      cyRef.current.layout({ name: 'cose', animate: true }).run()
      if (!data.nodes.length) message.info('未找到子图数据（Neo4j 不可用或无匹配）')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载知识图谱失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!containerRef.current) return

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#722ED1',
            'label': 'data(label)',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'width': '60px',
            'height': '60px',
            'text-outline-width': 2,
            'text-outline-color': '#722ED1'
          }
        },
        {
          selector: 'node[type="paper"]',
          style: {
            'background-color': '#1890ff',
            'text-outline-color': '#1890ff',
            'shape': 'rectangle',
            'width': '80px'
          }
        },
        {
          selector: 'node[type="person"]',
          style: {
            'background-color': '#52c41a',
            'text-outline-color': '#52c41a',
            'shape': 'ellipse'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(type)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-background-opacity': 1,
            'text-background-color': '#fff',
            'color': '#999'
          }
        },
        {
          selector: ':selected',
          style: {
            'border-width': 4,
            'border-color': '#faad14'
          }
        }
      ],
      layout: {
        name: 'grid', // Initial layout
      }
    })

    cyRef.current = cy

    // Event listeners
    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      setSelectedNode(node.data())
      setDrawerVisible(true)
    })

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setDrawerVisible(false)
        setSelectedNode(null)
      }
    })

    loadGraph(searchText)

    return () => {
      if (cyRef.current) {
        // Stop any running layout or animation before destroying
        // @ts-ignore
        cyRef.current.stop()
        cyRef.current.destroy()
        cyRef.current = null
      }
    }
  }, [])

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)
  const handleFit = () => cyRef.current?.fit()

  return (
    <AppLayout>
      <div className="graph-page">
        <div className="graph-toolbar">
           <Input
             placeholder="Search nodes..."
             prefix={<SearchOutlined />}
             style={{ width: 240 }}
             value={searchText}
             onChange={(e) => setSearchText(e.target.value)}
             onPressEnter={() => loadGraph(searchText)}
           />
           <Select value={typeFilter} style={{ width: 120 }} onChange={(v) => setTypeFilter(v)}>
             <Option value="all">All Types</Option>
             <Option value="paper">Paper</Option>
             <Option value="person">Person</Option>
           </Select>
           <Button icon={<FilterOutlined />} onClick={() => loadGraph(searchText)}>Filter</Button>
        </div>

        <div className="graph-container" ref={containerRef} />
        {loading && (
          <div className="graph-loading">
            <Spin size="large" />
          </div>
        )}

        <div className="graph-controls">
          <Tooltip title="Zoom In">
            <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
          </Tooltip>
          <Tooltip title="Zoom Out">
            <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
          </Tooltip>
          <Tooltip title="Fit View">
            <Button icon={<ExpandOutlined />} onClick={handleFit} />
          </Tooltip>
        </div>

        <Drawer
          title="Node Details"
          placement="right"
          onClose={() => setDrawerVisible(false)}
          open={drawerVisible}
          mask={false}
          width={400}
        >
          {selectedNode ? (
            <div className="node-details">
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Label">{selectedNode.label}</Descriptions.Item>
                <Descriptions.Item label="Type">
                  <Tag color={selectedNode.type === 'paper' ? 'blue' : 'green'}>
                    {selectedNode.type.toUpperCase()}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="ID">{selectedNode.id}</Descriptions.Item>
              </Descriptions>
              
              <div style={{ marginTop: 24 }}>
                <h4>Actions</h4>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button block icon={<NodeIndexOutlined />}>Expand Neighbors</Button>
                  <Button block icon={<InfoCircleOutlined />}>View Full Metadata</Button>
                </Space>
              </div>
            </div>
          ) : (
            <p>Select a node to view details</p>
          )}
        </Drawer>
      </div>
    </AppLayout>
  )
}

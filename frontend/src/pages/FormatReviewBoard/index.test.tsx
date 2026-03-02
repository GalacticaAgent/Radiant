import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { App } from 'antd'
import FormatReviewBoard from './index'


describe('FormatReviewBoard', () => {
  it('renders tabs', () => {
    render(
      <App>
        <MemoryRouter initialEntries={['/format-review/test-session-123']}>
          <Routes>
            <Route path="/format-review/:sessionId" element={<FormatReviewBoard />} />
          </Routes>
        </MemoryRouter>
      </App>
    )

    expect(screen.getByText('格式审查')).toBeInTheDocument()
    expect(screen.getByText('审查历史')).toBeInTheDocument()
    expect(screen.getByText('自定义论文审查规则')).toBeInTheDocument()
  })
})


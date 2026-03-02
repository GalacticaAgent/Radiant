import { useEffect, useRef, useState } from 'react'
import './SideNavigation.css'

interface NavItem {
  id: string
  text: string
  level: number
  children?: NavItem[]
}

export default function SideNavigation() {
  const [navItems, setNavItems] = useState<NavItem[]>([])
  const [activeId, setActiveId] = useState<string>('')
  const containerRef = useRef<HTMLDivElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)
  const [showBackToTop, setShowBackToTop] = useState(false)

  // Extract headings from page content
  useEffect(() => {
    const extractHeadings = () => {
      const mainElement = document.querySelector('main')
      if (!mainElement) {
        console.warn('Main element not found')
        return
      }

      const headings = mainElement.querySelectorAll('h2, h3')
      console.log('Found headings:', headings.length)

      const items: NavItem[] = []
      let currentH2: NavItem | null = null

      headings.forEach((heading, index) => {
        const level = parseInt(heading.tagName[1])

        // Generate ID if not present
        if (!heading.id) {
          heading.id = `heading-${index}`
        }

        const item: NavItem = {
          id: heading.id,
          text: heading.textContent || `Heading ${index}`,
          level,
        }

        if (level === 2) {
          currentH2 = item
          items.push(item)
        } else if (level === 3 && currentH2) {
          if (!currentH2.children) {
            currentH2.children = []
          }
          currentH2.children.push(item)
        }
      })

      console.log('Processed items:', items.length)
      setNavItems(items)

      // Setup intersection observer
      const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -80% 0px',
        threshold: 0,
      }

      observerRef.current = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        })
      }, observerOptions)

      headings.forEach((heading) => {
        if (observerRef.current) {
          observerRef.current.observe(heading)
        }
      })
    }

    // Delay to ensure content is rendered
    const timer = setTimeout(extractHeadings, 100)

    return () => {
      clearTimeout(timer)
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [])

  // Handle scroll position for back-to-top button
  useEffect(() => {
    const handleScroll = () => {
      const mainContent = document.querySelector('main')
      if (mainContent) {
        setShowBackToTop(mainContent.scrollTop > 300)
      }
    }

    const mainContent = document.querySelector('main')
    if (mainContent) {
      mainContent.addEventListener('scroll', handleScroll)
      return () => {
        mainContent.removeEventListener('scroll', handleScroll)
      }
    }
  }, [])

  // Smooth scroll to section
  const handleNavClick = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setActiveId(id)
    }
  }

  // Back to top
  const handleBackToTop = () => {
    const mainContent = document.querySelector('main')
    if (mainContent) {
      mainContent.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  if (navItems.length === 0) {
    return null
  }

  const renderNavItems = (items: NavItem[]) => {
    return items.map((item) => (
      <div key={item.id} className="nav-item-wrapper">
        <button
          className={`nav-item ${activeId === item.id ? 'active' : ''}`}
          onClick={() => handleNavClick(item.id)}
        >
          {item.text}
        </button>

        {item.children && item.children.length > 0 && (
          <div className="nav-children">
            {item.children.map((child) => (
              <button
                key={child.id}
                className={`nav-item nav-item-child ${
                  activeId === child.id ? 'active' : ''
                }`}
                onClick={() => handleNavClick(child.id)}
              >
                {child.text}
              </button>
            ))}
          </div>
        )}
      </div>
    ))
  }

  return (
    <nav className="side-navigation" ref={containerRef}>
      <div className="nav-content">
        <div className="nav-header">
          <h3 className="nav-title">目录</h3>
        </div>

        <div className="nav-list">
          {renderNavItems(navItems)}
        </div>

        {showBackToTop && (
          <button className="back-to-top" onClick={handleBackToTop}>
            <span className="arrow-icon">↑</span>
            <span>顶部</span>
          </button>
        )}
      </div>
    </nav>
  )
}

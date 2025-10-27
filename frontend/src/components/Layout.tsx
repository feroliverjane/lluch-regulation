import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Package, 
  FlaskConical, 
  FileCheck2, 
  ListTodo 
} from 'lucide-react'
import './Layout.css'

const Layout = () => {
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Materiales', path: '/materials', icon: Package },
    { name: 'Análisis', path: '/analyses', icon: FlaskConical },
    { name: 'Composites', path: '/composites', icon: FileCheck2 },
    { name: 'Aprobaciones', path: '/workflows', icon: ListTodo },
  ]

  const isActive = (path: string) => location.pathname.startsWith(path)

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Lluch Regulation</h1>
          <p>Composite Management</p>
        </div>
        
        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${isActive(item.path) ? 'active' : ''}`}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>
        
        <div className="sidebar-footer">
          <p>v1.0.0</p>
        </div>
      </aside>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout









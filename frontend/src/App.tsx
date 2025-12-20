                                                                import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Calendar, 
  Menu,
  X,
  CalendarDays
} from 'lucide-react';
import { useState } from 'react';
import Dashboard from './components/Dashboard';
import Schedules from './components/Schedules';
import ScheduleViewer from './components/ScheduleViewer';

function Navbar() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/', label: 'Inicio', icon: LayoutDashboard },
    { path: '/schedules', label: 'Generar Horario', icon: Calendar },
    { path: '/schedule-viewer', label: 'Ver Horario', icon: CalendarDays },
  ];
  
  return (
    <header className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="bg-white/20 p-2 rounded-lg group-hover:bg-white/30 transition-colors">
              <Calendar className="h-6 w-6 text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-lg font-bold text-white">Sistema de Horarios</h1>
              <p className="text-xs text-indigo-200">Generación Automática</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive(item.path) 
                      ? 'bg-white/20 text-white shadow-inner' 
                      : 'text-indigo-100 hover:bg-white/10 hover:text-white'
                    }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg text-white hover:bg-white/10 transition-colors"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-indigo-700/95 backdrop-blur-sm border-t border-white/10">
          <nav className="max-w-7xl mx-auto px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all
                    ${isActive(item.path) 
                      ? 'bg-white/20 text-white' 
                      : 'text-indigo-100 hover:bg-white/10'
                    }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/schedules" element={<Schedules />} />
            <Route path="/schedule-viewer" element={<ScheduleViewer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

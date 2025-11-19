import { AppBar, Box, Container, Toolbar, Typography, IconButton } from '@mui/material'
import SettingsIcon from '@mui/icons-material/Settings'
import { Route, Routes, NavLink, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { useFlowStore } from './store/useFlowStore'
import WelcomePage from './pages/Welcome'
import UploadPage from './pages/Upload'
import PreparePage from './pages/Prepare'
import TargetPage from './pages/Target'
import TrainPage from './pages/Train'
import ReportsPage from './pages/Reports'
import SummaryPage from './pages/Summary'
import Sidebar from './components/Sidebar'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { showMainApp } = useFlowStore()
  if (!showMainApp) {
    return <Navigate to="/welcome" replace />
  }
  return <>{children}</>
}

export default function AppRoutes() {
  const { showMainApp } = useFlowStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  if (!showMainApp) {
    return (
      <Routes>
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="*" element={<Navigate to="/welcome" replace />} />
      </Routes>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" color="default" enableColorOnDark>
        <Toolbar sx={{ gap: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>DataS</Typography>
          <NavLink to="/upload" style={{ color: 'inherit', textDecoration: 'none' }}>Upload</NavLink>
          <NavLink to="/summary" style={{ color: 'inherit', textDecoration: 'none' }}>Summary</NavLink>
          <NavLink to="/prepare" style={{ color: 'inherit', textDecoration: 'none' }}>Prepare</NavLink>
          <NavLink to="/target" style={{ color: 'inherit', textDecoration: 'none' }}>Target</NavLink>
          <NavLink to="/train" style={{ color: 'inherit', textDecoration: 'none' }}>Train</NavLink>
          <NavLink to="/reports" style={{ color: 'inherit', textDecoration: 'none' }}>Reports</NavLink>
          <IconButton color="inherit" onClick={() => setSidebarOpen(true)}>
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Container sx={{ py: 3, flex: 1 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
          <Route path="/summary" element={<ProtectedRoute><SummaryPage /></ProtectedRoute>} />
          <Route path="/prepare" element={<ProtectedRoute><PreparePage /></ProtectedRoute>} />
          <Route path="/target" element={<ProtectedRoute><TargetPage /></ProtectedRoute>} />
          <Route path="/train" element={<ProtectedRoute><TrainPage /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
        </Routes>
      </Container>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    </Box>
  )
}



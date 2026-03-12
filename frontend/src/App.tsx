import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material'
import BatchPredictionIcon from '@mui/icons-material/BatchPrediction'

function App() {
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <AppBar position="static" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar>
          <BatchPredictionIcon sx={{ mr: 2, color: 'primary.main' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Vitae-I: Batch Processing
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Main Content Area */}
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
          Workspace
        </Typography>
        
        <Box sx={{ 
          p: 6, 
          mt: 4, 
          borderRadius: 2, 
          bgcolor: 'background.paper',
          border: '1px dashed',
          borderColor: 'divider',
          textAlign: 'center'
        }}>
          <Typography color="text.secondary">
            Drag and drop area will be implemented in Phase 4.2
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}

export default App

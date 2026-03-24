import { useState, useEffect } from 'react';
import { AppBar, Toolbar, Typography, Container, Box, LinearProgress, Paper, Button } from '@mui/material';
import BatchPredictionIcon from '@mui/icons-material/BatchPrediction';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import DropzoneArea from './components/DropzoneArea';
import ResultsView from './components/ResultsView';

import { apiService, type BatchJobResponse } from './services/api';
import { useJobWebSocket } from './hooks/useJobWebSocket';

// Application State Machine
type AppState = 'IDLE' | 'UPLOADING' | 'PROCESSING' | 'COMPLETED';

// Generate a random session ID on app mount (Phase 4.3 pragmatic auth)
const SESSION_ID = crypto.randomUUID();

export default function App() {
  const [appState, setAppState] = useState<AppState>('IDLE');
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobData, setJobData] = useState<BatchJobResponse | null>(null);

  // Hook handles WebSocket connection automatically when jobId is set
  const { progress, statusMessage, isCompleted } = useJobWebSocket(
    appState === 'PROCESSING' ? jobId : null
  );

  // Triggered when DropzoneArea button is clicked
  const handleProcessFiles = async (files: File[]) => {
    try {
      setAppState('UPLOADING');
      
      // 1. Upload to REST API
      const newJobId = await apiService.uploadBatch(files, SESSION_ID);
      
      // 2. Switch to WebSocket Processing Phase
      setJobId(newJobId);
      setAppState('PROCESSING');
      
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload files. Check the console for details.");
      setAppState('IDLE');
    }
  };

  // Watch for WebSocket completion event
  useEffect(() => {
    if (appState === 'PROCESSING' && isCompleted && jobId) {
      fetchFinalResults(jobId);
    }
  }, [isCompleted, appState, jobId]);

  // Fetch final payload from REST API
  const fetchFinalResults = async (id: string) => {
    try {
      const data = await apiService.getJobResults(id);
      setJobData(data);
      setAppState('COMPLETED');
    } catch (error) {
      console.error("Failed to fetch results:", error);
      alert("Failed to fetch final results.");
      setAppState('IDLE');
    }
  };

  const handleReset = () => {
    setJobId(null);
    setJobData(null);
    setAppState('IDLE');
  };

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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" fontWeight={700}>
            Workspace
          </Typography>
          
          {appState === 'COMPLETED' && (
             <Button startIcon={<ArrowBackIcon />} onClick={handleReset} variant="outlined">
               New Batch
             </Button>
          )}
        </Box>
        
        {/* State: IDLE or UPLOADING */}
        {(appState === 'IDLE' || appState === 'UPLOADING') && (
          <Box sx={{ mt: 2 }}>
            <DropzoneArea 
              onProcess={handleProcessFiles} 
              disabled={appState === 'UPLOADING'} 
            />
          </Box>
        )}

        {/* State: PROCESSING */}
        {appState === 'PROCESSING' && (
          <Paper sx={{ p: 6, mt: 4, textAlign: 'center', borderRadius: 2 }}>
            <Typography variant="h5" gutterBottom>
              Analyzing Resumes...
            </Typography>
            <Box sx={{ width: '100%', mt: 4, mb: 2 }}>
              <LinearProgress variant="determinate" value={progress} sx={{ height: 10, borderRadius: 5 }} />
            </Box>
            <Typography variant="body1" color="text.secondary" fontWeight="medium">
              {progress}%
            </Typography>
            <Typography variant="body2" color="primary" sx={{ mt: 2 }}>
              {statusMessage || 'Connecting to processing engine...'}
            </Typography>
          </Paper>
        )}

        {/* State: COMPLETED */}
        {appState === 'COMPLETED' && jobData && (
          <ResultsView jobData={jobData} />
        )}

      </Container>
    </Box>
  );
}

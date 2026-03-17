import { useEffect, useState } from 'react';

interface WebSocketMessage {
  type: 'progress' | 'completed';
  processed_files?: number;
  total_files?: number;
  latest_file?: string;
  status?: string;
  job_id?: string;
}

export function useJobWebSocket(jobId: string | null) {
  const [progress, setProgress] = useState(0);
  const [processedFiles, setProcessedFiles] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    if (!jobId) {
      // Reset state if jobId becomes null
      setProgress(0);
      setProcessedFiles(0);
      setTotalFiles(0);
      setStatusMessage('');
      setIsCompleted(false);
      return;
    }

    // Initialize WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/jobs/${jobId}`);

    ws.onopen = () => {
      console.log(`WebSocket connected for job ${jobId}`);
      setStatusMessage('Connected. Awaiting processing to start...');
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        if (data.type === 'progress') {
          const current = data.processed_files || 0;
          const total = data.total_files || 1;
          
          setProcessedFiles(current);
          setTotalFiles(total);
          
          // Calculate percentage for progress bar
          const percentage = Math.round((current / total) * 100);
          setProgress(percentage);
          
          const resultMark = data.status === 'SUCCESS' ? '✅' : '❌';
          setStatusMessage(`Processing: ${data.latest_file} ${resultMark}`);
        } 
        else if (data.type === 'completed') {
          setIsCompleted(true);
          setStatusMessage('Processing complete! Fetching results...');
          ws.close(); // Gracefully close connection from client side
        }
      } catch (err) {
        console.error('Error parsing WebSocket message', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setStatusMessage('Connection error occurred.');
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed.');
    };

    // Cleanup: close connection if component unmounts
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [jobId]);

  return {
    progress,
    processedFiles,
    totalFiles,
    statusMessage,
    isCompleted,
  };
}

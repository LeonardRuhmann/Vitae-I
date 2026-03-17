import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { type BatchJobResponse } from '../services/api';

interface ResultsViewProps {
  jobData: BatchJobResponse;
}

export default function ResultsView({ jobData }: ResultsViewProps) {
  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Results Summary
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
        <Chip 
          label={`Total Files: ${jobData.total_files}`} 
          color="primary" 
          variant="outlined" 
        />
        <Chip 
          label={`Status: ${jobData.status}`} 
          color={jobData.status === 'COMPLETED' ? 'success' : 'warning'} 
          variant="outlined" 
        />
      </Box>

      {jobData.results.map((result, index) => (
        <Accordion 
          key={index} 
          defaultExpanded={result.status === 'FAILED'} // Auto-open failed ones
          sx={{ mb: 1, '&:before': { display: 'none' }, borderRadius: 1, overflow: 'hidden' }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{ 
              bgcolor: 'background.paper',
              borderLeft: '4px solid',
              borderColor: result.status === 'SUCCESS' ? 'success.main' : 'error.main'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 2 }}>
              {result.status === 'SUCCESS' ? (
                <CheckCircleIcon color="success" />
              ) : (
                <ErrorIcon color="error" />
              )}
              <Typography sx={{ flexGrow: 1, fontWeight: 500 }}>
                {result.file_name}
              </Typography>
            </Box>
          </AccordionSummary>
          
          <AccordionDetails sx={{ bgcolor: 'action.hover', p: 3 }}>
            {result.status === 'FAILED' ? (
              <Typography color="error" variant="body2">
                <strong>Error:</strong> {result.error_message || 'Unknown processing error'}
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                
                {/* Skills */}
                <Box>
                  <Typography variant="overline" color="text.secondary" fontWeight="bold">
                    Skills ({result.skills?.length || 0})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
                    {result.skills?.length > 0 ? (
                      result.skills.map(skill => (
                        <Chip key={skill} label={skill} color="primary" size="small" />
                      ))
                    ) : (
                      <Typography variant="body2" color="text.disabled">No skills detected</Typography>
                    )}
                  </Box>
                </Box>
                
                <Divider />

                {/* People/Entities */}
                <Box>
                  <Typography variant="overline" color="text.secondary" fontWeight="bold">
                    People Mentioned ({result.people?.length || 0})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
                    {result.people?.length > 0 ? (
                      result.people.map(person => (
                        <Chip key={person} label={person} color="secondary" size="small" />
                      ))
                    ) : (
                       <Typography variant="body2" color="text.disabled">No names detected</Typography>
                    )}
                  </Box>
                </Box>
                
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}

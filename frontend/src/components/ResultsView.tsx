import { useMemo } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { type BatchJobResponse } from '../services/api';

interface ResultsViewProps {
  jobData: BatchJobResponse;
}

// ---------------------------------------------------------------------------
// Score color logic
// ---------------------------------------------------------------------------
function getScoreColor(score: number): 'error' | 'warning' | 'success' {
  if (score < 50) return 'error';
  if (score <= 75) return 'warning';
  return 'success';
}

function getScoreColorHex(score: number): string {
  if (score < 50) return '#f44336';   // red
  if (score <= 75) return '#ff9800';  // orange/amber
  return '#4caf50';                   // green
}

export default function ResultsView({ jobData }: ResultsViewProps) {
  const hasMatchData = jobData.job_requirements && jobData.job_requirements.length > 0;

  // Sort results: highest match_score first, nulls last, then by file_name
  const sortedResults = useMemo(() => {
    return [...jobData.results].sort((a, b) => {
      // Failed results go to the bottom
      if (a.status === 'FAILED' && b.status !== 'FAILED') return 1;
      if (a.status !== 'FAILED' && b.status === 'FAILED') return -1;

      // Sort by match_score descending (nulls last)
      if (hasMatchData) {
        const scoreA = a.match_score ?? -1;
        const scoreB = b.match_score ?? -1;
        if (scoreA !== scoreB) return scoreB - scoreA;
      }

      // Fallback: alphabetical
      return a.file_name.localeCompare(b.file_name);
    });
  }, [jobData.results, hasMatchData]);

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Results Summary
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
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

      {/* JD Requirements extracted — show what was detected */}
      {hasMatchData && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="overline" color="text.secondary" fontWeight="bold">
            Job Requirements Detected ({jobData.job_requirements!.length} skills)
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
            {jobData.job_requirements!.map(skill => (
              <Chip 
                key={skill} 
                label={skill} 
                size="small" 
                variant="outlined"
                sx={{ 
                  borderColor: 'primary.main', 
                  color: 'primary.main',
                  fontWeight: 500,
                  textTransform: 'capitalize',
                }}
              />
            ))}
          </Box>
        </Box>
      )}

      {sortedResults.map((result, index) => (
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

              {/* Match Score Indicator */}
              {result.status === 'SUCCESS' && hasMatchData && result.match_score !== null && (
                <Box sx={{ position: 'relative', display: 'inline-flex', mr: 1 }}>
                  <CircularProgress
                    variant="determinate"
                    value={result.match_score}
                    size={48}
                    thickness={4}
                    sx={{ color: getScoreColorHex(result.match_score) }}
                  />
                  {/* Background track */}
                  <CircularProgress
                    variant="determinate"
                    value={100}
                    size={48}
                    thickness={4}
                    sx={{
                      color: 'action.hover',
                      position: 'absolute',
                      left: 0,
                      zIndex: -1,
                    }}
                  />
                  <Box
                    sx={{
                      top: 0,
                      left: 0,
                      bottom: 0,
                      right: 0,
                      position: 'absolute',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography
                      variant="caption"
                      component="div"
                      fontWeight="bold"
                      sx={{ color: getScoreColorHex(result.match_score), fontSize: '0.7rem' }}
                    >
                      {Math.round(result.match_score)}%
                    </Typography>
                  </Box>
                </Box>
              )}
            </Box>
          </AccordionSummary>
          
          <AccordionDetails sx={{ bgcolor: 'action.hover', p: 3 }}>
            {result.status === 'FAILED' ? (
              <Typography color="error" variant="body2">
                <strong>Error:</strong> {result.error_message || 'Unknown processing error'}
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                
                {/* Match Score Detail */}
                {hasMatchData && result.match_score !== null && (
                  <>
                    <Box>
                      <Typography variant="overline" color="text.secondary" fontWeight="bold">
                        Match Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                        <Chip
                          label={`${result.match_score}%`}
                          color={getScoreColor(result.match_score)}
                          size="small"
                          sx={{ fontWeight: 'bold' }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {(() => {
                            // Count how many JD skills this resume matched
                            const jdSkills = jobData.job_requirements!;
                            const resumeSkillsLower = (result.skills || []).map(s => s.toLowerCase());
                            const matched = jdSkills.filter(s => resumeSkillsLower.includes(s.toLowerCase()));
                            return `${matched.length} of ${jdSkills.length} required skills matched`;
                          })()}
                        </Typography>
                      </Box>
                    </Box>
                    <Divider />
                  </>
                )}

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

import { useState, useCallback } from 'react';
import { useDropzone, type FileRejection } from 'react-dropzone';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Button,
  Alert,
  Paper,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DeleteIcon from '@mui/icons-material/Delete';

const MAX_FILES = 10;

export default function DropzoneArea() {
  const [files, setFiles] = useState<File[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: FileRejection[]) => {
    setErrorMsg(null);

    // Filter out invalid drops first
    if (fileRejections.length > 0) {
      if (fileRejections[0].errors[0].code === 'too-many-files') {
        setErrorMsg(`You can only process up to ${MAX_FILES} resumes at a time.`);
      } else {
        setErrorMsg('Only PDF files are supported.');
      }
      return;
    }

    // Now handle accepted files plus what we already have
    setFiles((prevFiles) => {
      const allFiles = [...prevFiles, ...acceptedFiles];
      
      // Prevent accumulating duplicates by name
      const uniqueFiles = Array.from(new Map(allFiles.map(f => [f.name, f])).values());
      
      if (uniqueFiles.length > MAX_FILES) {
        setErrorMsg(`Limit reached: maximum ${MAX_FILES} resumes allowed per batch.`);
        // Return only the first 10
        return uniqueFiles.slice(0, MAX_FILES);
      }
      
      return uniqueFiles;
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: MAX_FILES,
  });

  const removeFile = (nameToRemove: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== nameToRemove));
    setErrorMsg(null);
  };

  const handleProcess = () => {
    console.log("Preparing to send files to API:", files);
    // TODO: Implement Phase 4.3 POST request here
  };

  // Dynamic styling based on drag state
  let borderColor = 'divider';
  let bgcolor = 'background.paper';
  if (isDragActive && !isDragReject) {
    borderColor = 'primary.main';
    bgcolor = 'action.hover';
  } else if (isDragReject) {
    borderColor = 'error.main';
    bgcolor = 'error.dark';
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Drop Area */}
      <Paper
        {...getRootProps()}
        elevation={0}
        sx={{
          p: 6,
          borderRadius: 2,
          border: '2px dashed',
          borderColor: borderColor,
          bgcolor: bgcolor,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" fontWeight="medium" gutterBottom>
          Drag & drop your PDF resumes here
        </Typography>
        <Typography variant="body2" color="text.secondary">
          or click to select files (Max: {MAX_FILES} files)
        </Typography>
      </Paper>

      {/* Error Alert */}
      {errorMsg && (
        <Alert severity="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
            Selected Resumes ({files.length} / {MAX_FILES})
          </Typography>
          <Paper elevation={1} sx={{ borderRadius: 2, bgcolor: 'background.paper' }}>
            <List disablePadding>
              {files.map((file, index) => (
                <ListItem
                  key={file.name}
                  divider={index < files.length - 1}
                  secondaryAction={
                    <IconButton edge="end" aria-label="delete" onClick={() => removeFile(file.name)}>
                      <DeleteIcon color="error" />
                    </IconButton>
                  }
                >
                  <ListItemIcon>
                    <PictureAsPdfIcon color="error" />
                  </ListItemIcon>
                  <ListItemText
                    primary={file.name}
                    secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                    primaryTypographyProps={{ fontWeight: 500 }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {/* Action Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleProcess}
          disabled={files.length === 0 || files.length > MAX_FILES}
          sx={{ fontWeight: 600, px: 4 }}
        >
          Process Batch
        </Button>
      </Box>
    </Box>
  );
}

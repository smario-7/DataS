import { Box, Button, Checkbox, FormControlLabel, Paper, Stack, TextField, Typography, Alert } from '@mui/material'
import { useFlowStore } from '../store/useFlowStore'
import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { uploadFile } from '../services/api'

export default function UploadPage() {
  const { datasetId, setDatasetId } = useFlowStore()
  const [value, setValue] = useState(datasetId || 'avocado')
  const [useDefault, setUseDefault] = useState(!datasetId)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)

  const uploadMut = useMutation({
    mutationFn: uploadFile,
    onSuccess: (data) => {
      setDatasetId(data.datasetId)
      setValue(data.datasetId)
    }
  })

  const handleFileSelect = (file: File | null) => {
    if (file && file.name.endsWith('.csv')) {
      uploadMut.mutate(file)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = () => {
    setDragActive(false)
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h5">📁 Ładowanie danych</Typography>

      <Paper sx={{ p: 3, border: dragActive ? 2 : 1, borderColor: dragActive ? 'primary.main' : 'divider' }}>
        <Stack spacing={2}>
          <Typography variant="h6">Upload pliku CSV</Typography>
          <Box
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            sx={{
              border: '2px dashed',
              borderColor: dragActive ? 'primary.main' : 'divider',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' }
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              style={{ display: 'none' }}
              onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
            />
            <Typography variant="body1" gutterBottom>
              {dragActive ? 'Upuść plik tutaj' : 'Przeciągnij plik CSV tutaj lub kliknij aby wybrać'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Obsługiwany format: CSV
            </Typography>
          </Box>

          {uploadMut.isPending && <Typography>Przesyłanie pliku...</Typography>}
          {uploadMut.isError && <Alert severity="error">Błąd: {String(uploadMut.error)}</Alert>}
          {uploadMut.isSuccess && (
            <Alert severity="success">
              ✅ Plik przesłany pomyślnie! Dataset ID: {uploadMut.data.datasetId}
            </Alert>
          )}
        </Stack>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Stack spacing={2}>
          <FormControlLabel
            control={
              <Checkbox
                checked={useDefault}
                onChange={(e) => {
                  setUseDefault(e.target.checked)
                  if (e.target.checked) {
                    setDatasetId('avocado')
                    setValue('avocado')
                  }
                }}
              />
            }
            label="Użyj domyślnego pliku (avocado.csv)"
          />

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              label="Dataset ID"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              disabled={useDefault}
              fullWidth
              helperText="Podaj istniejący datasetId lub użyj upload powyżej"
            />
            <Button
              variant="contained"
              onClick={() => setDatasetId(value)}
              disabled={useDefault || !value}
            >
              Ustaw
            </Button>
          </Box>

          {datasetId && (
            <Alert severity="info">
              ✅ Aktywny dataset: <strong>{datasetId}</strong>
            </Alert>
          )}
        </Stack>
      </Paper>
    </Stack>
  )
}

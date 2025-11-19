import { Button, Stack, Typography, Paper, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { featureImportance } from '../services/api'
import { useState } from 'react'
import { useFlowStore } from '../store/useFlowStore'

export default function ReportsPage() {
  const { modelId } = useFlowStore()
  const [fi, setFi] = useState<any>()
  
  const fetchFi = useMutation({
    mutationFn: () => featureImportance(modelId!),
    onSuccess: (d) => setFi(d),
  })

  return (
    <Stack spacing={3}>
      <Typography variant="h5">📈 Wyniki i raporty</Typography>

      {!modelId && (
        <Alert severity="warning">Najpierw wytrenuj model na stronie Train</Alert>
      )}

      {modelId && (
        <>
          <Paper sx={{ p: 3 }}>
            <Button 
              disabled={!modelId || fetchFi.isPending} 
              variant="contained" 
              onClick={() => fetchFi.mutate()}
            >
              Pobierz ważność cech
            </Button>
          </Paper>

          {fetchFi.isPending && <Typography>Ładowanie...</Typography>}
          {fetchFi.isError && <Alert severity="error">Błąd: {String(fetchFi.error)}</Alert>}

          {fi && (
            <>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>📊 Ważność cech (Top 20)</Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>#</TableCell>
                        <TableCell>Cecha</TableCell>
                        <TableCell align="right">Ważność</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {fi.series.slice(0, 20).map((s: any, idx: number) => (
                        <TableRow key={idx}>
                          <TableCell>{idx + 1}</TableCell>
                          <TableCell>{s.name}</TableCell>
                          <TableCell align="right">{s.importance.toFixed(5)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>

              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>📋 Tabela ważności (Top 50)</Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>#</TableCell>
                        <TableCell>Cecha</TableCell>
                        <TableCell align="right">Ważność</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {fi.series.slice(0, 50).map((s: any, idx: number) => (
                        <TableRow key={idx}>
                          <TableCell>{idx + 1}</TableCell>
                          <TableCell>{s.name}</TableCell>
                          <TableCell align="right">{s.importance.toFixed(5)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </>
          )}
        </>
      )}
    </Stack>
  )
}

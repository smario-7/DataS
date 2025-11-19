import { Button, Stack, Typography, Paper, Accordion, AccordionSummary, AccordionDetails, Alert, Box } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { prepareData } from '../services/api'
import { useFlowStore } from '../store/useFlowStore'
import { useState } from 'react'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export default function PreparePage() {
  const { datasetId, setPrepDone } = useFlowStore()
  const [result, setResult] = useState<any>()
  const mut = useMutation({
    mutationFn: () => prepareData({ datasetId: datasetId! }),
    onSuccess: (d) => {
      setResult(d)
      setPrepDone(true)
    },
  })

  const downloadCSV = () => {
    if (!result?.preview?.data) return
    const csv = result.preview.data.map((row: any) => Object.values(row).join(',')).join('\n')
    const headers = Object.keys(result.preview.data[0]).join(',')
    const blob = new Blob([headers + '\n' + csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prepared.csv'
    a.click()
  }

  const downloadLog = () => {
    if (!result?.prepLog) return
    const blob = new Blob([JSON.stringify(result.prepLog, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'prep_log.json'
    a.click()
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h5">🧹 Przygotowanie danych</Typography>
      
      {!datasetId && (
        <Alert severity="warning">Najpierw załaduj dane na stronie Upload</Alert>
      )}

      {datasetId && (
        <>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Typography variant="body1">
                Po kliknięciu uruchomi się automatyczne oczyszczanie danych z logiem zmian.
              </Typography>
              <Button
                disabled={!datasetId || mut.isPending}
                variant="contained"
                onClick={() => mut.mutate()}
                size="large"
              >
                🚿 Rozpocznij oczyszczanie
              </Button>
            </Stack>
          </Paper>

          {mut.isPending && (
            <Alert severity="info">Trwa oczyszczanie danych...</Alert>
          )}

          {mut.isError && (
            <Alert severity="error">Błąd: {String(mut.error)}</Alert>
          )}

          {result && (
            <>
              <Paper sx={{ p: 3 }}>
                <Stack spacing={2}>
                  <Typography variant="h6">📊 Podsumowanie</Typography>
                  <Typography variant="body2">
                    Kształt: {result.preview?.shape?.join(' × ')}
                  </Typography>
                  <Typography variant="body2">
                    Kolumny: {result.preview?.columns?.length}
                  </Typography>
                  <Typography variant="body2">
                    Liczba kroków w logu: {result.prepLog?.length || 0}
                  </Typography>
                </Stack>
              </Paper>

              {result.prepLog && result.prepLog.length > 0 && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>🧭 Dziennik zmian</Typography>
                  <Stack spacing={1}>
                    {result.prepLog.map((entry: any, idx: number) => (
                      <Accordion key={idx}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography>
                            Krok {idx + 1}: {entry.step}
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box component="pre" sx={{ fontSize: '0.875rem', overflow: 'auto' }}>
                            {JSON.stringify(entry, null, 2)}
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Stack>
                </Paper>
              )}

              <Paper sx={{ p: 3 }}>
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="outlined"
                    onClick={downloadCSV}
                    disabled={!result?.preview?.data}
                  >
                    ⬇️ Pobierz oczyszczony CSV
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={downloadLog}
                    disabled={!result?.prepLog}
                  >
                    ⬇️ Pobierz log (JSON)
                  </Button>
                </Stack>
              </Paper>
            </>
          )}
        </>
      )}
    </Stack>
  )
}

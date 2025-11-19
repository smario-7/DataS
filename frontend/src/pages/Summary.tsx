import { Button, Stack, Typography, Paper, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Select, MenuItem, FormControl, InputLabel, Grid } from '@mui/material'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getSummary, detectTarget } from '../services/api'
import { useFlowStore } from '../store/useFlowStore'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function SummaryPage() {
  const {
    datasetId,
    prepDone,
    strategy,
    manualColumnChoice,
    openaiApiKey,
    setAnalysisResult,
    setLastAnalysisParams,
    setMLResults,
    setAISteps,
    mlSettings,
  } = useFlowStore()
  const [sortBy, setSortBy] = useState('missing_ratio')
  const navigate = useNavigate()
  
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['summary', datasetId],
    enabled: !!datasetId,
    queryFn: () => getSummary(datasetId!),
  })

  const runAnalysisMut = useMutation({
    mutationFn: () => {
      let userTarget: string | undefined
      if (strategy === 'manual') {
        if (!manualColumnChoice) {
          throw new Error('⚠️ Proszę wybrać kolumnę docelową dla strategii ręcznej (w sidebar)')
        }
        userTarget = manualColumnChoice
      } else if (strategy === 'heuristics') {
        userTarget = '__force_heuristics__'
      }

      return detectTarget({
        datasetId: datasetId!,
        userTarget,
        openaiApiKey: strategy === 'auto_ai' 
          ? (openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined)
          : undefined,
      })
    },
    onSuccess: (data) => {
      const analysisParams = {
        strategy_label: strategy,
        user_choice: strategy === 'manual' ? manualColumnChoice : strategy === 'heuristics' ? '__force_heuristics__' : undefined,
        ...mlSettings,
      }
      setLastAnalysisParams(analysisParams)
      setAnalysisResult(data)
      setMLResults(undefined)
      setAISteps({})
      navigate('/target')
    },
  })

  const sortedColumns = summary?.columns ? [...summary.columns].sort((a: any, b: any) => {
    const aVal = a[sortBy] ?? 0
    const bVal = b[sortBy] ?? 0
    return typeof aVal === 'number' && typeof bVal === 'number' ? bVal - aVal : String(bVal).localeCompare(String(aVal))
  }) : []

  return (
    <Stack spacing={3}>
      <Typography variant="h5">📊 Podsumowanie danych</Typography>

      {!datasetId && (
        <Alert severity="warning">Najpierw załaduj dane na stronie Upload</Alert>
      )}

      {datasetId && (
        <>
          {isLoading && <Typography>Ładowanie...</Typography>}
          {error && <Alert severity="error">Błąd: {String(error)}</Alert>}

          {summary && (
            <>
              <Paper sx={{ p: 3 }}>
                <Stack spacing={2}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => runAnalysisMut.mutate()}
                    disabled={!prepDone || runAnalysisMut.isPending}
                    fullWidth
                  >
                    🚀 Uruchom analizę
                  </Button>
                  {!prepDone && (
                    <Alert severity="warning">
                      Najpierw przygotuj dane na stronie Prepare
                    </Alert>
                  )}
                  {strategy === 'manual' && !manualColumnChoice && (
                    <Alert severity="warning">
                      ⚠️ Proszę wybrać kolumnę docelową dla strategii ręcznej (w sidebar)
                    </Alert>
                  )}
                  {runAnalysisMut.isError && (
                    <Alert severity="error">Błąd: {String(runAnalysisMut.error)}</Alert>
                  )}
                </Stack>
              </Paper>

              <Paper sx={{ p: 3 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Wiersze</Typography>
                    <Typography variant="h6">{summary.n_rows.toLocaleString()}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Kolumny</Typography>
                    <Typography variant="h6">{summary.n_cols}</Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Kolumny z brakami &gt;10%</Typography>
                    <Typography variant="h6">
                      {summary.columns.filter((c: any) => (c.missing_ratio || 0) > 0.1).length}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Kandydaci na klucz</Typography>
                    <Typography variant="h6">{summary.primary_key_candidates?.length || 0}</Typography>
                  </Grid>
                </Grid>
              </Paper>

              <Paper sx={{ p: 3 }}>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6">
                      Analiza kolumn (sortowanie: <strong>{sortBy}</strong>)
                    </Typography>
                    <FormControl size="small" sx={{ minWidth: 200 }}>
                      <InputLabel>Sortuj według</InputLabel>
                      <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)} label="Sortuj według">
                        <MenuItem value="missing_ratio">Odsetek braków</MenuItem>
                        <MenuItem value="n_unique">Liczba unikalnych</MenuItem>
                        <MenuItem value="unique_ratio">Ratio unikalnych</MenuItem>
                        <MenuItem value="name">Nazwa</MenuItem>
                        <MenuItem value="semantic_type">Typ semantyczny</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>

                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Nazwa</TableCell>
                          <TableCell>Typ pandas</TableCell>
                          <TableCell>Typ semantyczny</TableCell>
                          <TableCell align="right">Unikalne</TableCell>
                          <TableCell align="right">Ratio unikalnych</TableCell>
                          <TableCell align="right">Braki</TableCell>
                          <TableCell align="right">Odsetek braków</TableCell>
                          <TableCell>Unikalna</TableCell>
                          <TableCell>Stała</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sortedColumns.map((col: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell>{col.name}</TableCell>
                            <TableCell>{col.pandas_dtype}</TableCell>
                            <TableCell>{col.semantic_type}</TableCell>
                            <TableCell align="right">{col.n_unique}</TableCell>
                            <TableCell align="right">{(col.unique_ratio || 0).toFixed(3)}</TableCell>
                            <TableCell align="right">{col.n_missing}</TableCell>
                            <TableCell align="right">{((col.missing_ratio || 0) * 100).toFixed(1)}%</TableCell>
                            <TableCell>{col.is_unique ? '✓' : ''}</TableCell>
                            <TableCell>{col.is_constant ? '✓' : ''}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Stack>
              </Paper>

              {summary.notes && summary.notes.length > 0 && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>⚠️ Zauważone problemy</Typography>
                  <Stack spacing={1}>
                    {summary.notes.map((note: string, idx: number) => (
                      <Alert key={idx} severity="warning">{note}</Alert>
                    ))}
                  </Stack>
                </Paper>
              )}

              {strategy === 'manual' && manualColumnChoice && summary && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>👤 Podgląd wybranej kolumny docelowej</Typography>
                  {(() => {
                    const selectedCol = summary.columns.find((c: any) => c.name === manualColumnChoice)
                    if (!selectedCol) return null
                    
                    const isNumeric = selectedCol.pandas_dtype?.includes('int') || selectedCol.pandas_dtype?.includes('float')
                    const problemType = isNumeric ? '📊 Regresja' : '🏷️ Klasyfikacja'
                    const modelType = isNumeric
                      ? 'Regresja (przewidywanie wartości numerycznych)'
                      : 'Klasyfikacja (przewidywanie kategorii)'
                    
                    return (
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">Typ danych</Typography>
                          <Typography variant="body1">{selectedCol.pandas_dtype || 'N/A'}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Unikalne wartości</Typography>
                          <Typography variant="body1">{selectedCol.n_unique || 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">Wartości brakujące</Typography>
                          <Typography variant="body1">{selectedCol.n_missing || 0}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Procent braków</Typography>
                          <Typography variant="body1">
                            {((selectedCol.missing_ratio || 0) * 100).toFixed(1)}%
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">Typ problemu</Typography>
                          <Typography variant="body1">{problemType}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Proponowany model</Typography>
                          <Typography variant="body1" sx={{ fontSize: '0.875rem' }}>{modelType}</Typography>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">Typ semantyczny</Typography>
                          <Typography variant="body1">{selectedCol.semantic_type || 'N/A'}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Ratio unikalnych</Typography>
                          <Typography variant="body1">{(selectedCol.unique_ratio || 0).toFixed(3)}</Typography>
                        </Grid>
                      </Grid>
                    )
                  })()}
                </Paper>
              )}
            </>
          )}
        </>
      )}
    </Stack>
  )
}



import { Button, Stack, Typography, Paper, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Select, MenuItem, FormControl, InputLabel } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { getSummary } from '../services/api'
import { useFlowStore } from '../store/useFlowStore'
import { useState } from 'react'

export default function SummaryPage() {
  const { datasetId } = useFlowStore()
  const [sortBy, setSortBy] = useState('missing_ratio')
  
  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['summary', datasetId],
    enabled: !!datasetId,
    queryFn: () => getSummary(datasetId!),
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
                <Stack direction="row" spacing={2} alignItems="center">
                  <Typography variant="h6">Metryki</Typography>
                  <Typography>Wiersze: <strong>{summary.n_rows.toLocaleString()}</strong></Typography>
                  <Typography>Kolumny: <strong>{summary.n_cols}</strong></Typography>
                  <Typography>
                    Kolumny z brakami &gt;10%: <strong>
                      {summary.columns.filter((c: any) => (c.missing_ratio || 0) > 0.1).length}
                    </strong>
                  </Typography>
                  <Typography>
                    Kandydaci na klucz: <strong>{summary.primary_key_candidates?.length || 0}</strong>
                  </Typography>
                </Stack>
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
            </>
          )}
        </>
      )}
    </Stack>
  )
}



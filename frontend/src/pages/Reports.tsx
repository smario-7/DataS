import {
  Button,
  Stack,
  Typography,
  Paper,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Box,
  Grid,
  LinearProgress,
  Tabs,
  Tab,
} from '@mui/material'
import { useMutation, useQuery } from '@tanstack/react-query'
import { featureImportance, generateLLMReport, jobStatus, downloadReportPDF, downloadReportMarkdown, getReportCharts } from '../services/api'
import { useState, useEffect } from 'react'
import { useFlowStore } from '../store/useFlowStore'
import ReactMarkdown from 'react-markdown'

export default function ReportsPage() {
  const {
    modelId,
    datasetId,
    aiSteps,
    openaiApiKey,
    llmReport,
    llmCharts,
    setLLMReport,
    setLLMCharts,
    setLLMPdf,
  } = useFlowStore()
  const [fi, setFi] = useState<any>()
  const [tabValue, setTabValue] = useState(0)
  const [llmJobId, setLlmJobId] = useState<string>()
  const [reportId, setReportId] = useState<string>()

  const fetchFi = useMutation({
    mutationFn: () => featureImportance(modelId!),
    onSuccess: (d) => setFi(d),
  })

  const generateLLM = useMutation({
    mutationFn: () => {
      if (!aiSteps.step1 || !aiSteps.step2 || !modelId || !datasetId || (!openaiApiKey && openaiApiKeySource !== 'env')) {
        throw new Error('Brakuje wymaganych danych')
      }
      return generateLLMReport({
        datasetId: datasetId!,
        modelId: modelId!,
        businessDomain: aiSteps.step1,
        targetColumn: aiSteps.step2,
        aiSteps: aiSteps,
        openaiApiKey: openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined,
      })
    },
    onSuccess: (d) => {
      setLlmJobId(d.jobId)
    },
  })

  const { data: llmJobStatus } = useQuery({
    queryKey: ['llmJob', llmJobId],
    enabled: !!llmJobId,
    queryFn: () => jobStatus(llmJobId!),
    refetchInterval: llmJobId ? 1500 : false,
  })

  useEffect(() => {
    if (llmJobStatus?.status === 'completed' && llmJobStatus?.details?.reportId) {
      setReportId(llmJobStatus.details.reportId)
      // Pobierz raport i wykresy
      getReportCharts(llmJobStatus.details.reportId).then((charts) => {
        setLLMCharts(charts)
      })
      downloadReportMarkdown(llmJobStatus.details.reportId).then((blob) => {
        blob.text().then((text) => setLLMReport(text))
      })
    }
  }, [llmJobStatus, setLLMCharts, setLLMReport])

  const hasAllDataForLLM =
    aiSteps.step1 && aiSteps.step2 && aiSteps.step3 && aiSteps.step4 && modelId && (openaiApiKey || openaiApiKeySource === 'env')

  const downloadPDF = async () => {
    if (!reportId) return
    const blob = await downloadReportPDF(reportId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'raport_analizy.pdf'
    a.click()
  }

  const downloadMarkdown = async () => {
    if (!reportId || !llmReport) return
    const blob = new Blob([llmReport], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'raport_analizy.md'
    a.click()
  }

  const downloadChartsZip = async () => {
    if (!llmCharts || !reportId) return
    const JSZip = (await import('jszip')).default
    const zip = new JSZip()
    Object.entries(llmCharts).forEach(([name, data]: [string, any]) => {
      if (data) {
        const base64Data = data.replace(/^data:image\/png;base64,/, '')
        zip.file(`${name}.png`, base64Data, { base64: true })
      }
    })
    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'wykresy_analizy.zip'
    a.click()
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h5">📈 Wyniki i raporty</Typography>

      {!modelId && <Alert severity="warning">Najpierw wytrenuj model na stronie Train</Alert>}

      {modelId && (
        <>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label="📊 Ważność cech" />
            <Tab label="⚛️ Raport z LLM" />
          </Tabs>

          {tabValue === 0 && (
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

              {fetchFi.isPending && <LinearProgress />}
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

          {tabValue === 1 && (
            <>
              {!hasAllDataForLLM && (
                <Alert severity="warning">
                  ⚠️ <strong>Brakuje:</strong>{' '}
                  {[
                    !aiSteps.step1 && 'analiza AI (krok 1)',
                    !aiSteps.step2 && 'analiza AI (krok 2)',
                    !aiSteps.step3 && 'analiza AI (krok 3)',
                    !aiSteps.step4 && 'analiza AI (krok 4)',
                    !modelId && 'wytrenowany model ML',
                    !openaiApiKey && openaiApiKeySource !== 'env' && 'klucz API OpenAI',
                  ]
                    .filter(Boolean)
                    .join(', ')}
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    💡 <strong>Wymagane kroki:</strong>
                    <br />
                    1. Wykonaj analizę AI w zakładce Target (wszystkie 4 kroki)
                    <br />
                    2. Wytrenuj model ML w zakładce Train
                    <br />
                    3. Upewnij się, że masz klucz API OpenAI w sidebar
                  </Typography>
                </Alert>
              )}

              {hasAllDataForLLM && !llmReport && (
                <Paper sx={{ p: 3 }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => generateLLM.mutate()}
                    disabled={generateLLM.isPending || !!llmJobId}
                    fullWidth
                  >
                    📊 Wygeneruj raport z LLM
                  </Button>
                  {generateLLM.isPending && <LinearProgress sx={{ mt: 2 }} />}
                  {generateLLM.isError && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      Błąd: {String(generateLLM.error)}
                    </Alert>
                  )}
                </Paper>
              )}

              {llmJobId && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="body2">Job ID: {llmJobId}</Typography>
                  {llmJobStatus && (
                    <>
                      <Typography variant="body2">
                        Status: {llmJobStatus.status} ({Math.round((llmJobStatus.progress || 0) * 100)}%)
                      </Typography>
                      {llmJobStatus.progress && (
                        <LinearProgress variant="determinate" value={llmJobStatus.progress * 100} sx={{ mt: 1 }} />
                      )}
                    </>
                  )}
                </Paper>
              )}

              {llmReport && (
                <>
                  <Paper sx={{ p: 3 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6} md={4}>
                        <Button variant="outlined" fullWidth onClick={downloadMarkdown}>
                          💾 Pobierz jako Markdown
                        </Button>
                      </Grid>
                      <Grid item xs={12} sm={6} md={4}>
                        <Button variant="outlined" fullWidth onClick={downloadPDF} disabled={!reportId}>
                          📄 Pobierz PDF
                        </Button>
                      </Grid>
                      <Grid item xs={12} sm={6} md={4}>
                        <Button variant="outlined" fullWidth onClick={downloadChartsZip} disabled={!llmCharts}>
                          📊 Pobierz wykresy (ZIP)
                        </Button>
                      </Grid>
                    </Grid>
                  </Paper>

                  {llmCharts && (
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h6" gutterBottom>📊 Wykresy i wizualizacje</Typography>
                      <Stack spacing={3}>
                        {llmCharts.temporal_trends && (
                          <Box>
                            <Typography variant="subtitle1">📈 Trendy czasowe</Typography>
                            <Box
                              component="img"
                              src={`data:image/png;base64,${llmCharts.temporal_trends}`}
                              sx={{ width: '100%', height: 'auto' }}
                            />
                          </Box>
                        )}
                        {llmCharts.feature_importance && (
                          <Box>
                            <Typography variant="subtitle1">🎯 Ważność cech</Typography>
                            <Box
                              component="img"
                              src={`data:image/png;base64,${llmCharts.feature_importance}`}
                              sx={{ width: '100%', height: 'auto' }}
                            />
                          </Box>
                        )}
                        {llmCharts.future_prediction && (
                          <Box>
                            <Typography variant="subtitle1">🔮 Prognoza na przyszłość</Typography>
                            <Box
                              component="img"
                              src={`data:image/png;base64,${llmCharts.future_prediction}`}
                              sx={{ width: '100%', height: 'auto' }}
                            />
                          </Box>
                        )}
                        {llmCharts.correlations && (
                          <Box>
                            <Typography variant="subtitle1">🔗 Macierz korelacji</Typography>
                            <Box
                              component="img"
                              src={`data:image/png;base64,${llmCharts.correlations}`}
                              sx={{ width: '100%', height: 'auto' }}
                            />
                          </Box>
                        )}
                        {llmCharts.target_distribution && (
                          <Box>
                            <Typography variant="subtitle1">📊 Rozkład wartości docelowej</Typography>
                            <Box
                              component="img"
                              src={`data:image/png;base64,${llmCharts.target_distribution}`}
                              sx={{ width: '100%', height: 'auto' }}
                            />
                          </Box>
                        )}
                      </Stack>
                    </Paper>
                  )}

                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>📋 Raport analityczny</Typography>
                    <Box sx={{ '& p': { mb: 2 }, '& h1, & h2, & h3': { mt: 3, mb: 2 } }}>
                      <ReactMarkdown>{llmReport}</ReactMarkdown>
                    </Box>
                  </Paper>
                </>
              )}
            </>
          )}
        </>
      )}
    </Stack>
  )
}

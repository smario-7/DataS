import { Button, Stack, TextField, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Alert, LinearProgress, Box, Accordion, AccordionSummary, AccordionDetails, Grid } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { detectTarget, aiStep1, aiStep2, aiStep3, aiStep4 } from '../services/api'
import { useFlowStore } from '../store/useFlowStore'
import { useState, useEffect } from 'react'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export default function TargetPage() {
  const {
    datasetId,
    target,
    setTarget,
    openaiApiKey,
    analysisResult,
    setAnalysisResult,
    aiSteps,
    setAISteps,
    setMLResults,
    setLastAnalysisParams,
  } = useFlowStore()
  const [userTarget, setUserTarget] = useState<string>('')
  const [out, setOut] = useState<any>(analysisResult)
  
  useEffect(() => {
    if (analysisResult) {
      setOut(analysisResult)
      setTarget(analysisResult.suggestedTarget, analysisResult.problemType)
    }
  }, [analysisResult, setTarget])

  const mut = useMutation({
    mutationFn: () => detectTarget({ 
      datasetId: datasetId!, 
      userTarget: userTarget || undefined,
      openaiApiKey: openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined
    }),
    onSuccess: (d) => {
      setOut(d)
      setAnalysisResult(d)
      setTarget(d.suggestedTarget, d.problemType)
    },
  })

  const step1Mut = useMutation({
    mutationFn: () => aiStep1({ 
      datasetId: datasetId!, 
      openaiApiKey: openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined 
    }),
    onSuccess: (d) => setAISteps({ step1: d.businessDomain })
  })

  const step2Mut = useMutation({
    mutationFn: () => aiStep2({ 
      datasetId: datasetId!, 
      businessDomain: aiSteps.step1!, 
      openaiApiKey: openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined 
    }),
    onSuccess: (d) => setAISteps({ step2: d.targetColumn })
  })

  const step3Mut = useMutation({
    mutationFn: () => aiStep3({ 
      datasetId: datasetId!, 
      businessDomain: aiSteps.step1!, 
      targetColumn: aiSteps.step2 || out?.suggestedTarget, 
      openaiApiKey: openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined 
    }),
    onSuccess: (d) => setAISteps({ step3: d })
  })

  const step4Mut = useMutation({
    mutationFn: () => aiStep4({ 
      datasetId: datasetId!, 
      businessDomain: aiSteps.step1!, 
      targetColumn: aiSteps.step2 || out?.suggestedTarget, 
      openaiApiKey: openaiApiKey && openaiApiKey !== '__env__' ? openaiApiKey : undefined 
    }),
    onSuccess: (d) => setAISteps({ step4: d })
  })

  const handleResetAnalysis = () => {
    setAnalysisResult(undefined)
    setAISteps({})
    setMLResults(undefined)
    setLastAnalysisParams(undefined)
    setOut(undefined)
  }

  const sourceMap: Record<string, string> = {
    user_choice: '🙋 Wybór użytkownika',
    llm_guess: '🤖 Propozycja AI',
    heuristics_pick: '🔍 Analiza heurystyczna',
    none: '❌ Brak decyzji'
  }

  const showAiSteps = out?.source === 'llm_guess' && (openaiApiKey || openaiApiKeySource === 'env')

  return (
    <Stack spacing={3}>
      <Typography variant="h5">🎯 Wybór targetu</Typography>

      {!datasetId && (
        <Alert severity="warning">Najpierw załaduj dane na stronie Upload</Alert>
      )}

      {datasetId && (
        <>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <TextField 
                label="Wymuś target (opcjonalnie)" 
                value={userTarget} 
                onChange={(e) => setUserTarget(e.target.value)}
                fullWidth
              />
              <Button 
                disabled={!datasetId || mut.isPending} 
                variant="contained" 
                onClick={() => mut.mutate()}
              >
                Wykryj target
              </Button>
            </Stack>
          </Paper>

          {mut.isPending && <LinearProgress />}
          {mut.isError && <Alert severity="error">Błąd: {String(mut.error)}</Alert>}

          {out && (
            <>
              <Paper sx={{ p: 3 }}>
                <Stack spacing={2}>
                  <Typography variant="h6">Wyniki analizy</Typography>
                  <Typography>Źródło decyzji: {sourceMap[out.source] || out.source}</Typography>
                  <Typography>Kolumna docelowa: <strong>{out.suggestedTarget}</strong></Typography>
                  <Typography>Typ problemu: <strong>{out.problemType}</strong></Typography>
                </Stack>
              </Paper>

              {out.ranking && out.ranking.length > 0 && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>Ranking kandydatów</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Kolumna</TableCell>
                          <TableCell align="right">Score</TableCell>
                          <TableCell>Typ</TableCell>
                          <TableCell align="right">Unikalne</TableCell>
                          <TableCell align="right">Braki %</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {out.ranking.slice(0, 20).map((r: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell>{r.kolumna || r.name}</TableCell>
                            <TableCell align="right">
                              {r.kandydat_score?.toFixed(3) || r.total?.toFixed(3) || '-'}
                            </TableCell>
                            <TableCell>{r.typ_wykryty || r.semantic_type || '-'}</TableCell>
                            <TableCell align="right">{r.n_unikalnych || r.n_unique || '-'}</TableCell>
                            <TableCell align="right">
                              {((r.odsetek_brakow || r.missing_ratio || 0) * 100).toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Paper>
              )}

              {showAiSteps && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>🔍 Dodatkowe analizy AI</Typography>
                  
                  {!aiSteps.step1 && (
                    <Box>
                      <Button 
                        variant="outlined" 
                        onClick={() => step1Mut.mutate()}
                        disabled={step1Mut.isPending}
                      >
                        Krok 1: Określ domenę biznesową
                      </Button>
                      {step1Mut.isPending && <LinearProgress sx={{ mt: 1 }} />}
                    </Box>
                  )}

                  {aiSteps.step1 && !aiSteps.step2 && (
                    <Box>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        ✅ Krok 1: {aiSteps.step1}
                      </Alert>
                      <Button 
                        variant="outlined" 
                        onClick={() => step2Mut.mutate()}
                        disabled={step2Mut.isPending}
                      >
                        Krok 2: Wybierz target z domeną
                      </Button>
                      {step2Mut.isPending && <LinearProgress sx={{ mt: 1 }} />}
                    </Box>
                  )}

                  {aiSteps.step2 && !aiSteps.step3 && (
                    <Box>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        ✅ Krok 2: {aiSteps.step2}
                      </Alert>
                      <Button 
                        variant="outlined" 
                        onClick={() => step3Mut.mutate()}
                        disabled={step3Mut.isPending}
                      >
                        Krok 3: Analiza korelacji
                      </Button>
                      {step3Mut.isPending && <LinearProgress sx={{ mt: 1 }} />}
                    </Box>
                  )}

                  {aiSteps.step3 && !aiSteps.step4 && (
                    <Box>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        ✅ Krok 3: Analiza korelacji zakończona
                      </Alert>
                      <Accordion defaultExpanded>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography>🔗 Relacje między kolumnami</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Stack spacing={2}>
                            {aiSteps.step3.correlations && aiSteps.step3.correlations.length > 0 && (
                              <Box>
                                <Typography variant="subtitle2" gutterBottom>📊 Korelacje między kolumnami</Typography>
                                <TableContainer>
                                  <Table size="small">
                                    <TableHead>
                                      <TableRow>
                                        <TableCell>Kolumna 1</TableCell>
                                        <TableCell>Kolumna 2</TableCell>
                                        <TableCell>Siła korelacji</TableCell>
                                        <TableCell>Typ korelacji</TableCell>
                                        <TableCell>Uzasadnienie biznesowe</TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {aiSteps.step3.correlations.map((c: any, idx: number) => (
                                        <TableRow key={idx}>
                                          <TableCell>{c.column1}</TableCell>
                                          <TableCell>{c.column2}</TableCell>
                                          <TableCell>{c.correlation_strength}</TableCell>
                                          <TableCell>{c.correlation_type}</TableCell>
                                          <TableCell>{c.business_reason}</TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </TableContainer>
                              </Box>
                            )}
                            {aiSteps.step3.targetCorrelations && aiSteps.step3.targetCorrelations.length > 0 && (
                              <Box>
                                <Typography variant="subtitle2" gutterBottom>🎯 Korelacje z kolumną docelową</Typography>
                                <TableContainer>
                                  <Table size="small">
                                    <TableHead>
                                      <TableRow>
                                        <TableCell>Kolumna</TableCell>
                                        <TableCell>Oczekiwany wpływ</TableCell>
                                        <TableCell>Relacja</TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {aiSteps.step3.targetCorrelations.map((c: any, idx: number) => (
                                        <TableRow key={idx}>
                                          <TableCell>{c.column}</TableCell>
                                          <TableCell>{c.expected_impact}</TableCell>
                                          <TableCell>{c.relationship}</TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </TableContainer>
                              </Box>
                            )}
                          </Stack>
                        </AccordionDetails>
                      </Accordion>
                      <Button 
                        variant="outlined" 
                        onClick={() => step4Mut.mutate()}
                        disabled={step4Mut.isPending}
                        sx={{ mt: 2 }}
                      >
                        Krok 4: Sugestie czyszczenia
                      </Button>
                      {step4Mut.isPending && <LinearProgress sx={{ mt: 1 }} />}
                    </Box>
                  )}

                  {aiSteps.step4 && (
                    <Box>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        ✅ Wszystkie analizy AI zakończone!
                      </Alert>
                      
                      <Stack spacing={2}>
                        <Accordion defaultExpanded>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>🏢 Domena biznesowa</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Alert severity="success">
                              <strong>Domena biznesowa:</strong> {aiSteps.step1 || 'Brak'}
                            </Alert>
                          </AccordionDetails>
                        </Accordion>

                        <Accordion defaultExpanded>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>🎯 Kolumna docelowa (AI)</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Alert severity="success">
                              <strong>Kolumna docelowa:</strong> {aiSteps.step2 || 'Brak'}
                            </Alert>
                          </AccordionDetails>
                        </Accordion>

                        <Accordion defaultExpanded>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>🔗 Relacje między kolumnami</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Stack spacing={2}>
                              {aiSteps.step3?.correlations && aiSteps.step3.correlations.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>📊 Korelacje między kolumnami</Typography>
                                  <TableContainer>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Kolumna 1</TableCell>
                                          <TableCell>Kolumna 2</TableCell>
                                          <TableCell>Siła korelacji</TableCell>
                                          <TableCell>Typ korelacji</TableCell>
                                          <TableCell>Uzasadnienie biznesowe</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {aiSteps.step3.correlations.map((c: any, idx: number) => (
                                          <TableRow key={idx}>
                                            <TableCell>{c.column1}</TableCell>
                                            <TableCell>{c.column2}</TableCell>
                                            <TableCell>{c.correlation_strength}</TableCell>
                                            <TableCell>{c.correlation_type}</TableCell>
                                            <TableCell>{c.business_reason}</TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>
                              )}
                              {aiSteps.step3?.targetCorrelations && aiSteps.step3.targetCorrelations.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>🎯 Korelacje z kolumną docelową</Typography>
                                  <TableContainer>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Kolumna</TableCell>
                                          <TableCell>Oczekiwany wpływ</TableCell>
                                          <TableCell>Relacja</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {aiSteps.step3.targetCorrelations.map((c: any, idx: number) => (
                                          <TableRow key={idx}>
                                            <TableCell>{c.column}</TableCell>
                                            <TableCell>{c.expected_impact}</TableCell>
                                            <TableCell>{c.relationship}</TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>
                              )}
                            </Stack>
                          </AccordionDetails>
                        </Accordion>

                        <Accordion defaultExpanded>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>🧹 Sugestie czyszczenia danych</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            <Stack spacing={2}>
                              {aiSteps.step4.missingDataStrategy && Object.keys(aiSteps.step4.missingDataStrategy).length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>🔍 Strategie obsługi brakujących danych</Typography>
                                  <TableContainer>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Kolumna</TableCell>
                                          <TableCell>Strategia</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {Object.entries(aiSteps.step4.missingDataStrategy).map(([col, strat]: [string, any], idx: number) => (
                                          <TableRow key={idx}>
                                            <TableCell>{col}</TableCell>
                                            <TableCell>{strat}</TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>
                              )}
                              {aiSteps.step4.outlierTreatment && Object.keys(aiSteps.step4.outlierTreatment).length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>📊 Obsługa wartości odstających</Typography>
                                  <TableContainer>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Kolumna</TableCell>
                                          <TableCell>Metoda obsługi</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {Object.entries(aiSteps.step4.outlierTreatment).map(([col, treatment]: [string, any], idx: number) => (
                                          <TableRow key={idx}>
                                            <TableCell>{col}</TableCell>
                                            <TableCell>{treatment}</TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>
                              )}
                              {aiSteps.step4.dataTypeConversions && aiSteps.step4.dataTypeConversions.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>🔄 Sugerowane konwersje typów</Typography>
                                  <TableContainer>
                                    <Table size="small">
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Kolumna</TableCell>
                                          <TableCell>Z typu</TableCell>
                                          <TableCell>Na typ</TableCell>
                                          <TableCell>Powód</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {aiSteps.step4.dataTypeConversions.map((conv: any, idx: number) => (
                                          <TableRow key={idx}>
                                            <TableCell>{conv.column}</TableCell>
                                            <TableCell>{conv.from}</TableCell>
                                            <TableCell>{conv.to}</TableCell>
                                            <TableCell>{conv.reason}</TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>
                              )}
                              {aiSteps.step4.qualityIssues && aiSteps.step4.qualityIssues.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>⚠️ Problemy jakościowe</Typography>
                                  <Stack spacing={0.5}>
                                    {aiSteps.step4.qualityIssues.map((issue: string, idx: number) => (
                                      <Typography key={idx} variant="body2">• {issue}</Typography>
                                    ))}
                                  </Stack>
                                </Box>
                              )}
                              {aiSteps.step4.targetSpecificSuggestions && aiSteps.step4.targetSpecificSuggestions.length > 0 && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>🎯 Sugestie specyficzne dla kolumny docelowej</Typography>
                                  <Stack spacing={0.5}>
                                    {aiSteps.step4.targetSpecificSuggestions.map((suggestion: string, idx: number) => (
                                      <Typography key={idx} variant="body2">• {suggestion}</Typography>
                                    ))}
                                  </Stack>
                                </Box>
                              )}
                            </Stack>
                          </AccordionDetails>
                        </Accordion>

                        <Button variant="outlined" onClick={handleResetAnalysis} sx={{ mt: 2 }}>
                          🔄 Uruchom nową analizę
                        </Button>
                      </Stack>
                    </Box>
                  )}
                </Paper>
              )}

              {out.source !== 'llm_guess' && (openaiApiKey || openaiApiKeySource === 'env') && (
                <Alert severity="info">
                  Dodatkowe analizy AI są dostępne tylko gdy źródłem decyzji jest 'Propozycja AI'
                </Alert>
              )}

              {!openaiApiKey && openaiApiKeySource !== 'env' && (
                <Alert severity="warning">
                  Brak klucza API OpenAI - dodatkowe analizy AI wymagają klucza API
                </Alert>
              )}
            </>
          )}
        </>
      )}
    </Stack>
  )
}

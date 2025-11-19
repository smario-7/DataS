import { Button, Stack, TextField, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Alert, LinearProgress, Box, Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { detectTarget, aiStep1, aiStep2, aiStep3, aiStep4 } from '../services/api'
import { useFlowStore } from '../store/useFlowStore'
import { useState } from 'react'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

export default function TargetPage() {
  const { datasetId, target, setTarget, openaiApiKey } = useFlowStore()
  const [userTarget, setUserTarget] = useState<string>('')
  const [out, setOut] = useState<any>()
  const [aiSteps, setAiSteps] = useState<any>({})
  
  const mut = useMutation({
    mutationFn: () => detectTarget({ 
      datasetId: datasetId!, 
      userTarget: userTarget || undefined,
      openaiApiKey: openaiApiKey || undefined
    }),
    onSuccess: (d) => {
      setOut(d)
      setTarget(d.suggestedTarget, d.problemType)
    },
  })

  const step1Mut = useMutation({
    mutationFn: () => aiStep1({ datasetId: datasetId!, openaiApiKey: openaiApiKey! }),
    onSuccess: (d) => setAiSteps((s: any) => ({ ...s, step1: d.businessDomain }))
  })

  const step2Mut = useMutation({
    mutationFn: () => aiStep2({ 
      datasetId: datasetId!, 
      businessDomain: aiSteps.step1, 
      openaiApiKey: openaiApiKey! 
    }),
    onSuccess: (d) => setAiSteps((s: any) => ({ ...s, step2: d.targetColumn }))
  })

  const step3Mut = useMutation({
    mutationFn: () => aiStep3({ 
      datasetId: datasetId!, 
      businessDomain: aiSteps.step1, 
      targetColumn: aiSteps.step2 || out?.suggestedTarget, 
      openaiApiKey: openaiApiKey! 
    }),
    onSuccess: (d) => setAiSteps((s: any) => ({ ...s, step3: d }))
  })

  const step4Mut = useMutation({
    mutationFn: () => aiStep4({ 
      datasetId: datasetId!, 
      businessDomain: aiSteps.step1, 
      targetColumn: aiSteps.step2 || out?.suggestedTarget, 
      openaiApiKey: openaiApiKey! 
    }),
    onSuccess: (d) => setAiSteps((s: any) => ({ ...s, step4: d }))
  })

  const sourceMap: Record<string, string> = {
    user_choice: '🙋 Wybór użytkownika',
    llm_guess: '🤖 Propozycja AI',
    heuristics_pick: '🔍 Analiza heurystyczna',
    none: '❌ Brak decyzji'
  }

  const showAiSteps = out?.source === 'llm_guess' && openaiApiKey

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
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography>Korelacje między kolumnami</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <TableContainer>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell>Kolumna 1</TableCell>
                                  <TableCell>Kolumna 2</TableCell>
                                  <TableCell>Siła</TableCell>
                                  <TableCell>Typ</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {aiSteps.step3.correlations?.slice(0, 10).map((c: any, idx: number) => (
                                  <TableRow key={idx}>
                                    <TableCell>{c.column1}</TableCell>
                                    <TableCell>{c.column2}</TableCell>
                                    <TableCell>{c.correlation_strength}</TableCell>
                                    <TableCell>{c.correlation_type}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
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
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography>Sugestie czyszczenia danych</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Stack spacing={2}>
                            {aiSteps.step4.missingDataStrategy && (
                              <Box>
                                <Typography variant="subtitle2">Strategie obsługi braków</Typography>
                                {Object.entries(aiSteps.step4.missingDataStrategy).slice(0, 5).map(([col, strat]: [string, any]) => (
                                  <Typography key={col} variant="body2">{col}: {strat}</Typography>
                                ))}
                              </Box>
                            )}
                            {aiSteps.step4.qualityIssues && aiSteps.step4.qualityIssues.length > 0 && (
                              <Box>
                                <Typography variant="subtitle2">Problemy jakościowe</Typography>
                                {aiSteps.step4.qualityIssues.slice(0, 5).map((issue: string, idx: number) => (
                                  <Typography key={idx} variant="body2">• {issue}</Typography>
                                ))}
                              </Box>
                            )}
                          </Stack>
                        </AccordionDetails>
                      </Accordion>
                    </Box>
                  )}
                </Paper>
              )}

              {out.source !== 'llm_guess' && openaiApiKey && (
                <Alert severity="info">
                  Dodatkowe analizy AI są dostępne tylko gdy źródłem decyzji jest 'Propozycja AI'
                </Alert>
              )}

              {!openaiApiKey && (
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

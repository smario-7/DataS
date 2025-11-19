import { Box, Button, Card, CardContent, Stack, TextField, Typography, Alert, Grid } from '@mui/material'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useFlowStore } from '../store/useFlowStore'
import { getOpenAIStatus } from '../services/api'

export default function WelcomePage() {
  const { setOpenaiApiKey, setOpenaiApiKeySource, setShowMainApp, openaiApiKey, openaiApiKeySource } = useFlowStore()
  const [apiKey, setApiKey] = useState(openaiApiKey || '')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const { data: envStatus, isLoading: isLoadingEnv } = useQuery({
    queryKey: ['openai-status'],
    queryFn: getOpenAIStatus,
    retry: 1,
  })

  useEffect(() => {
    if (envStatus?.hasEnvKey && openaiApiKeySource !== 'env') {
      setOpenaiApiKeySource('env')
      setOpenaiApiKey('__env__')
    }
  }, [envStatus, setOpenaiApiKey, setOpenaiApiKeySource, openaiApiKeySource])

  const handleStart = () => {
    if (apiKey.trim() && apiKey !== '__env__') {
      setOpenaiApiKey(apiKey.trim())
      setOpenaiApiKeySource('manual')
      setShowMainApp(true)
      navigate('/upload')
    } else if (openaiApiKeySource === 'env' && envStatus?.hasEnvKey) {
      // Automatycznie użyj klucza z .env jeśli jest dostępny
      setOpenaiApiKeySource('env')
      setShowMainApp(true)
      navigate('/upload')
    } else {
      setError('⚠️ Proszę wprowadzić klucz API OpenAI')
    }
  }

  const handleContinueWithoutAI = () => {
    setOpenaiApiKey(null)
    setOpenaiApiKeySource(null)
    setShowMainApp(true)
    navigate('/upload')
  }

  const hasApiKey = (apiKey && apiKey.trim() && apiKey !== '__env__') || (openaiApiKeySource === 'env' && envStatus?.hasEnvKey)
  const hasEnvKey = envStatus?.hasEnvKey === true

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Card sx={{ maxWidth: 1000, width: '100%' }}>
        <CardContent>
          <Stack spacing={3}>
            <Typography variant="h4" component="h1" gutterBottom>
              🤖 AutoML - The Most Important Variables
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Automatyczna analiza danych z inteligentnym wyborem kolumny docelowej i trenowaniem modelu
            </Typography>

            <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={8}>
                  <Stack spacing={2}>
                    <Typography variant="h6">🔑 Konfiguracja OpenAI API</Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Wprowadź swój klucz API OpenAI, aby korzystać z funkcji Auto AI:</strong>
                    </Typography>
                    <Typography component="ul" variant="body2" sx={{ pl: 2 }}>
                      <li>Automatyczny wybór kolumny docelowej przez AI</li>
                      <li>Inteligentna analiza danych</li>
                      <li>Zaawansowane rekomendacje</li>
                    </Typography>

                    <TextField
                      label="Klucz API OpenAI:"
                      type="password"
                      value={apiKey === '__env__' ? '' : apiKey}
                      onChange={(e) => {
                        setApiKey(e.target.value)
                        setError('')
                      }}
                      placeholder="sk-..."
                      helperText="Wprowadź swój klucz API OpenAI. Możesz go znaleźć na platform.openai.com"
                      fullWidth
                      error={!!error}
                    />
                    {error && <Alert severity="error">{error}</Alert>}

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Button
                          variant="contained"
                          onClick={handleStart}
                          fullWidth
                          size="large"
                          disabled={!hasApiKey && !hasEnvKey}
                        >
                          🚀 Rozpocznij analizę
                        </Button>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Button
                          variant="outlined"
                          onClick={handleContinueWithoutAI}
                          fullWidth
                          size="large"
                        >
                          ⏭️ Kontynuuj bez AI
                        </Button>
                      </Grid>
                    </Grid>
                  </Stack>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Stack spacing={2}>
                    <Typography variant="h6">📋 Dostępne funkcje</Typography>
                    
                    {hasApiKey || hasEnvKey ? (
                      <Alert severity="success">
                        <Typography variant="body2" component="div">
                          <strong>✅ Z kluczem API:</strong>
                          {hasEnvKey && openaiApiKeySource === 'env' && (
                            <Typography variant="body2" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                              (Źródło: plik .env)
                            </Typography>
                          )}
                          <Typography component="ul" variant="body2" sx={{ mt: 1, mb: 0, pl: 2 }}>
                            <li>🤖 <strong>Auto AI</strong> - automatyczny wybór kolumny</li>
                            <li>🧠 <strong>Inteligentna analiza</strong> - zaawansowane rekomendacje</li>
                            <li>📊 <strong>Pełna funkcjonalność</strong> - wszystkie opcje</li>
                          </Typography>
                        </Typography>
                      </Alert>
                    ) : (
                      <Alert severity="info">
                        <Typography variant="body2" component="div">
                          <strong>ℹ️ Bez klucza API:</strong>
                          <Typography component="ul" variant="body2" sx={{ mt: 1, mb: 0, pl: 2 }}>
                            <li>🔍 <strong>Heurystyka</strong> - wybór kolumny na podstawie reguł</li>
                            <li>📈 <strong>Analiza danych</strong> - podstawowe funkcje</li>
                            <li>📋 <strong>Raporty</strong> - standardowe raporty</li>
                          </Typography>
                        </Typography>
                      </Alert>
                    )}

                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                        💡 Wskazówki:
                      </Typography>
                      <Typography component="ul" variant="body2" color="text.secondary" sx={{ pl: 2, mt: 1 }}>
                        <li>Klucz API można wprowadzić później w ustawieniach</li>
                        <li>Bez klucza API nadal możesz korzystać z heurystyki</li>
                        <li>Wszystkie dane są przetwarzane lokalnie</li>
                      </Typography>
                    </Box>
                  </Stack>
                </Grid>
              </Grid>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}



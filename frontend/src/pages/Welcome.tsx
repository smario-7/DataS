import { Box, Button, Card, CardContent, Stack, TextField, Typography, Alert } from '@mui/material'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFlowStore } from '../store/useFlowStore'

export default function WelcomePage() {
  const { setOpenaiApiKey, setShowMainApp } = useFlowStore()
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleStart = () => {
    if (apiKey.trim()) {
      setOpenaiApiKey(apiKey.trim())
      setShowMainApp(true)
      navigate('/upload')
    } else {
      setError('Proszę wprowadzić klucz API OpenAI')
    }
  }

  const handleContinueWithoutAI = () => {
    setOpenaiApiKey(null)
    setShowMainApp(true)
    navigate('/upload')
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Card sx={{ maxWidth: 800, width: '100%' }}>
        <CardContent>
          <Stack spacing={3}>
            <Typography variant="h4" component="h1" gutterBottom>
              🤖 AutoML - The Most Important Variables
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Automatyczna analiza danych z inteligentnym wyborem kolumny docelowej i trenowaniem modelu
            </Typography>

            <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
              <Stack spacing={2}>
                <Typography variant="h6">🔑 Konfiguracja OpenAI API</Typography>
                <Typography variant="body2" color="text.secondary">
                  Wprowadź swój klucz API OpenAI, aby korzystać z funkcji Auto AI:
                </Typography>
                <Typography component="ul" variant="body2" sx={{ pl: 2 }}>
                  <li>Automatyczny wybór kolumny docelowej przez AI</li>
                  <li>Inteligentna analiza danych</li>
                  <li>Zaawansowane rekomendacje</li>
                </Typography>

                <TextField
                  label="Klucz API OpenAI"
                  type="password"
                  value={apiKey}
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

                <Stack direction="row" spacing={2}>
                  <Button
                    variant="contained"
                    onClick={handleStart}
                    fullWidth
                    size="large"
                  >
                    🚀 Rozpocznij analizę
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handleContinueWithoutAI}
                    fullWidth
                    size="large"
                  >
                    ⏭️ Kontynuuj bez AI
                  </Button>
                </Stack>
              </Stack>
            </Box>

            <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
              <Typography variant="h6" gutterBottom>📋 Dostępne funkcje</Typography>
              {apiKey && apiKey.trim() ? (
                <Alert severity="success" sx={{ mb: 2 }}>
                  ✅ <strong>Z kluczem API:</strong>
                  <Typography component="ul" variant="body2" sx={{ mt: 1, mb: 0, pl: 2 }}>
                    <li>🤖 <strong>Auto AI</strong> - automatyczny wybór kolumny</li>
                    <li>🧠 <strong>Inteligentna analiza</strong> - zaawansowane rekomendacje</li>
                    <li>📊 <strong>Pełna funkcjonalność</strong> - wszystkie opcje</li>
                  </Typography>
                </Alert>
              ) : (
                <Alert severity="info" sx={{ mb: 2 }}>
                  ℹ️ <strong>Bez klucza API:</strong>
                  <Typography component="ul" variant="body2" sx={{ mt: 1, mb: 0, pl: 2 }}>
                    <li>🔍 <strong>Heurystyka</strong> - wybór kolumny na podstawie reguł</li>
                    <li>📈 <strong>Analiza danych</strong> - podstawowe funkcje</li>
                    <li>📋 <strong>Raporty</strong> - standardowe raporty</li>
                  </Typography>
                </Alert>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                💡 <strong>Wskazówki:</strong>
              </Typography>
              <Typography component="ul" variant="body2" color="text.secondary" sx={{ pl: 2 }}>
                <li>Klucz API można wprowadzić później w ustawieniach</li>
                <li>Bez klucza API nadal możesz korzystać z heurystyki</li>
                <li>Wszystkie dane są przetwarzane lokalnie</li>
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}



import {
  Drawer,
  Box,
  Typography,
  Stack,
  Alert,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Divider,
  IconButton,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import { useFlowStore, Strategy } from '../store/useFlowStore'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSummary } from '../services/api'

const drawerWidth = 320

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const {
    openaiApiKey,
    openaiApiKeySource,
    setOpenaiApiKey,
    setOpenaiApiKeySource,
    setShowMainApp,
    mlSettings,
    setMLSettings,
    strategy,
    setStrategy,
    manualColumnChoice,
    setManualColumnChoice,
    datasetId,
  } = useFlowStore()
  const navigate = useNavigate()
  const [tempApiKey, setTempApiKey] = useState(openaiApiKey || '')

  const { data: summary } = useQuery({
    queryKey: ['summary', datasetId],
    enabled: !!datasetId && open,
    queryFn: () => getSummary(datasetId!),
  })

  useEffect(() => {
    setTempApiKey(openaiApiKey || '')
  }, [openaiApiKey])

  const hasApiKey = (openaiApiKey && openaiApiKey.trim() && openaiApiKey !== '__env__') || openaiApiKeySource === 'env'

  const handleChangeApiKey = () => {
    setOpenaiApiKey(tempApiKey.trim() || null)
  }

  const handleGoToWelcome = () => {
    setShowMainApp(false)
    navigate('/welcome')
  }

  const availableStrategies: { value: Strategy; label: string }[] = hasApiKey
    ? [
        { value: 'auto_ai', label: '🤖 Auto AI - inteligentny wybór przez AI' },
        { value: 'heuristics', label: '🔍 Heurystyka - analiza na podstawie nazw i typów' },
        { value: 'manual', label: '👤 Ręczny - wybierz kolumnę ręcznie' },
      ]
    : [
        { value: 'heuristics', label: '🔍 Heurystyka - analiza na podstawie nazw i typów' },
        { value: 'manual', label: '👤 Ręczny - wybierz kolumnę ręcznie' },
      ]

  const columns = summary?.columns?.map((c: any) => c.name) || []

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Box sx={{ p: 2, overflow: 'auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">⚙️ Ustawienia</Typography>
          <IconButton size="small" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Stack spacing={2}>
          <Typography variant="subtitle1">🔑 Status OpenAI</Typography>

          {hasApiKey ? (
            <>
              <Alert severity="success">
                ✅ Klucz API OpenAI dostępny
                {openaiApiKeySource === 'env' && (
                  <Typography variant="body2" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                    (Źródło: plik .env)
                  </Typography>
                )}
              </Alert>
              <Alert severity="info">🤖 Funkcja Auto AI będzie działać</Alert>
              <Typography variant="body2" color="text.secondary">
                <strong>💡 Wskazówki:</strong>
                <br />
                - Możesz przełączyć na strategię 'Heurystyka' jako alternatywa dla Auto AI
              </Typography>
              <Button variant="outlined" fullWidth onClick={handleGoToWelcome}>
                🔄 Zmień klucz API
              </Button>
            </>
          ) : (
            <>
              <Alert severity="warning">⚠️ Brak klucza API OpenAI</Alert>
              <Alert severity="info">🔍 Automatycznie przejdzie na heurystykę</Alert>
              <Typography variant="body2" color="text.secondary">
                <strong>Aby używać AI:</strong>
                <br />
                1. Kliknij "🔑 Wprowadź klucz API" poniżej
                <br />
                2. Wprowadź swój klucz API OpenAI
                <br />
                3. Klucz będzie przechowywany tylko w tej sesji
              </Typography>
              <Button variant="outlined" fullWidth onClick={handleGoToWelcome}>
                🔑 Wprowadź klucz API
              </Button>
            </>
          )}

          {hasApiKey && (
            <>
              <TextField
                label="Klucz API OpenAI"
                type="password"
                value={tempApiKey}
                onChange={(e) => setTempApiKey(e.target.value)}
                size="small"
                fullWidth
              />
              <Button variant="contained" fullWidth onClick={handleChangeApiKey}>
                Zaktualizuj klucz
              </Button>
            </>
          )}

          <Divider />

          {datasetId && summary && (
            <>
              <Typography variant="subtitle1">🎯 Strategia wyboru kolumny</Typography>
              <FormControl fullWidth size="small">
                <InputLabel>Wybierz strategię</InputLabel>
                <Select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value as Strategy)}
                  label="Wybierz strategię"
                >
                  {availableStrategies.map((s) => (
                    <MenuItem key={s.value} value={s.value}>
                      {s.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {strategy === 'manual' && (
                <>
                  <Typography variant="body2" color="text.secondary">
                    👤 Wybór kolumny docelowej
                  </Typography>
                  <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
                    Wybierz kolumnę, która będzie używana jako zmienna docelowa (target) w modelu ML
                  </Alert>
                  <FormControl fullWidth size="small">
                    <InputLabel>Wybierz kolumnę docelową</InputLabel>
                    <Select
                      value={manualColumnChoice || ''}
                      onChange={(e) => setManualColumnChoice(e.target.value)}
                      label="Wybierz kolumnę docelową"
                    >
                      {columns.map((col: string) => (
                        <MenuItem key={col} value={col}>
                          {col}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </>
              )}

              <Divider />

              <Typography variant="subtitle1">🤖 Ustawienia ML</Typography>

              <TextField
                label="Próbkowanie (0 = pełny zbiór)"
                type="number"
                value={mlSettings.sample_n}
                onChange={(e) => setMLSettings({ sample_n: parseInt(e.target.value) || 0 })}
                inputProps={{ min: 0, step: 500 }}
                size="small"
                fullWidth
              />

              <TextField
                label="Random state"
                type="number"
                value={mlSettings.random_state}
                onChange={(e) => setMLSettings({ random_state: parseInt(e.target.value) || 42 })}
                inputProps={{ min: 0 }}
                size="small"
                fullWidth
              />

              <TextField
                label="Top N cech na wykresie"
                type="number"
                value={mlSettings.top_n_features}
                onChange={(e) => setMLSettings({ top_n_features: parseInt(e.target.value) || 20 })}
                inputProps={{ min: 5, max: 50 }}
                size="small"
                fullWidth
              />

              <TextField
                label="Permutation repeats"
                type="number"
                value={mlSettings.permutation_repeats}
                onChange={(e) => setMLSettings({ permutation_repeats: parseInt(e.target.value) || 5 })}
                inputProps={{ min: 3, max: 20 }}
                size="small"
                fullWidth
              />

              <Box>
                <Typography variant="body2" gutterBottom>
                  Test size: {mlSettings.test_size.toFixed(2)}
                </Typography>
                <Slider
                  value={mlSettings.test_size}
                  onChange={(_, value) => setMLSettings({ test_size: value as number })}
                  min={0.1}
                  max={0.4}
                  step={0.05}
                  marks
                />
              </Box>

              <Divider />

              <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
                Przycisk '🚀 Uruchom analizę' jest teraz w zakładce '📊 Podsumowanie danych'.
              </Alert>

              <Divider />

              <Typography variant="subtitle2">📝 Strategie wyboru:</Typography>
              {availableStrategies.map((s) => (
                <Typography
                  key={s.value}
                  variant="body2"
                  color={strategy === s.value ? 'primary' : 'text.secondary'}
                  sx={{ fontWeight: strategy === s.value ? 'bold' : 'normal' }}
                >
                  {strategy === s.value && strategy === 'manual' && manualColumnChoice
                    ? `${s.label} ✅ (Wybrano: ${manualColumnChoice})`
                    : strategy === s.value
                    ? `${s.label} ✅`
                    : s.label}
                </Typography>
              ))}

              {!hasApiKey && (
                <Alert severity="info" sx={{ mt: 1, fontSize: '0.875rem' }}>
                  ℹ️ <strong>Auto AI</strong> niedostępne - wprowadź klucz API OpenAI
                </Alert>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                <strong>💡 Zmiana strategii nie uruchamia analizy!</strong>
              </Typography>
            </>
          )}

          {!datasetId && (
            <Alert severity="info">⏳ Załaduj poprawnie dane, aby wybrać kolumnę docelową</Alert>
          )}
        </Stack>
      </Box>
    </Drawer>
  )
}


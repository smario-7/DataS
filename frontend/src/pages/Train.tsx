import { Button, Stack, Typography, Paper, LinearProgress, Alert, Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material'
import { useMutation, useQuery } from '@tanstack/react-query'
import { jobStatus, trainModel } from '../services/api'
import { useEffect, useState } from 'react'
import { useFlowStore } from '../store/useFlowStore'
import * as echarts from 'echarts'

export default function TrainPage() {
  const { datasetId, target, problemType, setModelId } = useFlowStore()
  const [jobId, setJobId] = useState<string>()
  const chartRef = useState<HTMLDivElement | null>(null)
  
  const mut = useMutation({
    mutationFn: () => trainModel({ datasetId: datasetId!, target: target!, problemType: problemType! }),
    onSuccess: (d) => setJobId(d.jobId),
  })
  
  const { data: status, refetch } = useQuery({
    queryKey: ['job', jobId],
    enabled: !!jobId,
    queryFn: async () => jobStatus(jobId!),
    refetchInterval: jobId ? 1500 : false,
  })
  
  useEffect(() => {
    if (status?.status === 'completed' && status?.details?.modelId) {
      setModelId(status.details.modelId)
    }
  }, [status, setModelId])

  useEffect(() => {
    if (status?.details?.featureImportance && chartRef[0]) {
      const chart = echarts.init(chartRef[0])
      const data = status.details.featureImportance.slice(0, 20).reverse()
      chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: data.map((d: any) => d.name || d.cecha) },
        series: [{
          type: 'bar',
          data: data.map((d: any) => d.importance || d.waznosc_srednia)
        }]
      })
      return () => chart.dispose()
    }
  }, [status?.details?.featureImportance, chartRef[0]])

  const metrics = status?.details?.metrics || {}
  const isRegression = problemType === 'regresja'

  return (
    <Stack spacing={3}>
      <Typography variant="h5">🤖 Trenowanie modelu</Typography>

      {(!datasetId || !target || !problemType) && (
        <Alert severity="warning">Najpierw wybierz target na stronie Target</Alert>
      )}

      {datasetId && target && problemType && (
        <>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Typography variant="h6">Wybrana kolumna docelowa: <strong>{target}</strong></Typography>
              <Typography variant="body2">Typ problemu: <strong>{problemType}</strong></Typography>
              <Button 
                disabled={mut.isPending || !!jobId} 
                variant="contained" 
                onClick={() => mut.mutate()}
                size="large"
              >
                🚀 Trenuj model ML
              </Button>
            </Stack>
          </Paper>

          {mut.isPending && <LinearProgress />}
          {mut.isError && <Alert severity="error">Błąd: {String(mut.error)}</Alert>}

          {jobId && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="body2">Job ID: {jobId}</Typography>
              {status && (
                <>
                  <Typography variant="body2">
                    Status: {status.status} ({Math.round((status.progress || 0) * 100)}%)
                  </Typography>
                  {status.progress && <LinearProgress variant="determinate" value={status.progress * 100} sx={{ mt: 1 }} />}
                </>
              )}
            </Paper>
          )}

          {status?.status === 'completed' && status.details && (
            <>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>📊 Metryki modelu</Typography>
                <Stack spacing={1}>
                  <Typography>Model: <strong>{metrics.model || 'N/A'}</strong></Typography>
                  {isRegression ? (
                    <>
                      <Typography>R²: <strong>{metrics.R2?.toFixed(3) || 'N/A'}</strong></Typography>
                      <Typography>MAE: <strong>{metrics.MAE?.toFixed(3) || 'N/A'}</strong></Typography>
                      <Typography>RMSE: <strong>{metrics.RMSE?.toFixed(3) || 'N/A'}</strong></Typography>
                    </>
                  ) : (
                    <>
                      <Typography>Balanced Accuracy: <strong>{metrics.balanced_accuracy?.toFixed(3) || 'N/A'}</strong></Typography>
                      <Typography>Accuracy: <strong>{metrics.accuracy?.toFixed(3) || 'N/A'}</strong></Typography>
                      <Typography>F1 Macro: <strong>{metrics.f1_macro?.toFixed(3) || 'N/A'}</strong></Typography>
                    </>
                  )}
                </Stack>
              </Paper>

              {status.details.featureImportance && (
                <>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>📈 Ważność cech</Typography>
                    <Box ref={chartRef} sx={{ width: '100%', height: 400 }} />
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
                            <TableCell align="right">Std</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {status.details.featureImportance.slice(0, 50).map((fi: any, idx: number) => (
                            <TableRow key={idx}>
                              <TableCell>{idx + 1}</TableCell>
                              <TableCell>{fi.name || fi.cecha}</TableCell>
                              <TableCell align="right">{(fi.importance || fi.waznosc_srednia || 0).toFixed(5)}</TableCell>
                              <TableCell align="right">{(fi.std || fi.waznosc_std || 0).toFixed(5)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Paper>
                </>
              )}

              {status.details.recommendations && (
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>💡 Rekomendacje</Typography>
                  <Box component="div" dangerouslySetInnerHTML={{ __html: status.details.recommendations }} />
                </Paper>
              )}
            </>
          )}
        </>
      )}
    </Stack>
  )
}

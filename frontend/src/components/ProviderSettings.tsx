import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

interface ProviderInfo {
  name: string;
  type: string;
  available: boolean;
  description: string;
  features: string[];
}

interface ProviderStatus {
  approval_provider: string;
  memory_provider: string;
  evaluation_provider: string;
}

interface ProvidersList {
  approval_providers: ProviderInfo[];
  memory_providers: ProviderInfo[];
  evaluation_providers: ProviderInfo[];
}

export function ProviderSettings() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [providers, setProviders] = useState<ProvidersList | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, listRes] = await Promise.all([
        api.get<{success: boolean; data?: ProviderStatus}>('/providers/status'),
        api.get<{success: boolean; data?: ProvidersList}>('/providers/list'),
      ]);

      if (statusRes.data.success && statusRes.data.data) {
        setStatus(statusRes.data.data);
      }
      if (listRes.data.success && listRes.data.data) {
        setProviders(listRes.data.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('errors.serverError');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = async (providerType: string, providerName: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post<{success: boolean; message?: string}>('/providers/set', {
        provider_type: providerType,
        provider: providerName,
      });

      if (response.data.success) {
        setSuccess(response.data.message || t('settings.provider.switchSuccess'));
        // 更新状态
        if (status) {
          setStatus({
            ...status,
            [`${providerType}_provider`]: providerName,
          });
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('settings.provider.switchFailed');
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !status) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        {t('settings.provider.title')}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* 审批提供者 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('settings.provider.approvalProvider')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('settings.provider.approvalProviderHint')}
              </Typography>
              
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel id="approval-provider-label">{t('settings.provider.currentProvider')}</InputLabel>
                <Select
                  labelId="approval-provider-label"
                  value={status?.approval_provider || ''}
                  onChange={(e) => handleProviderChange('approval', e.target.value)}
                  disabled={loading}
                  label={t('settings.provider.currentProvider')}
                >
                  {providers?.approval_providers.map((provider) => (
                    <MenuItem key={provider.name} value={provider.name}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                        <Typography>{provider.description}</Typography>
                        {provider.name === status?.approval_provider && (
                          <Chip
                            size="small"
                            label={t('settings.provider.current')}
                            color="primary"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {providers?.approval_providers.map((provider) => (
                <Box key={provider.name} sx={{ mb: 1 }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    {provider.available ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <ErrorIcon color="error" fontSize="small" />
                    )}
                    <Typography variant="subtitle2">{provider.description}</Typography>
                  </Box>
                  <Box sx={{ ml: 3 }}>
                    {provider.features.map((feature, idx) => (
                      <Chip
                        key={idx}
                        label={feature}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* 记忆提供者 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('settings.provider.memoryProvider')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('settings.provider.memoryProviderHint')}
              </Typography>
              
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel id="memory-provider-label">{t('settings.provider.currentProvider')}</InputLabel>
                <Select
                  labelId="memory-provider-label"
                  value={status?.memory_provider || ''}
                  onChange={(e) => handleProviderChange('memory', e.target.value)}
                  disabled={loading}
                  label={t('settings.provider.currentProvider')}
                >
                  {providers?.memory_providers.map((provider) => (
                    <MenuItem key={provider.name} value={provider.name}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                        <Typography>{provider.description}</Typography>
                        {provider.name === status?.memory_provider && (
                          <Chip
                            size="small"
                            label={t('settings.provider.current')}
                            color="primary"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {providers?.memory_providers.map((provider) => (
                <Box key={provider.name} sx={{ mb: 1 }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    {provider.available ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <ErrorIcon color="error" fontSize="small" />
                    )}
                    <Typography variant="subtitle2">{provider.description}</Typography>
                  </Box>
                  <Box sx={{ ml: 3 }}>
                    {provider.features.map((feature, idx) => (
                      <Chip
                        key={idx}
                        label={feature}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* 评估提供者 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('settings.provider.evaluationProvider')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('settings.provider.evaluationProviderHint')}
              </Typography>
              
              <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                <InputLabel id="evaluation-provider-label">{t('settings.provider.currentProvider')}</InputLabel>
                <Select
                  labelId="evaluation-provider-label"
                  value={status?.evaluation_provider || ''}
                  onChange={(e) => handleProviderChange('evaluation', e.target.value)}
                  disabled={loading}
                  label={t('settings.provider.currentProvider')}
                >
                  {providers?.evaluation_providers.map((provider) => (
                    <MenuItem key={provider.name} value={provider.name}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                        <Typography>{provider.description}</Typography>
                        {provider.name === status?.evaluation_provider && (
                          <Chip
                            size="small"
                            label={t('settings.provider.current')}
                            color="primary"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {providers?.evaluation_providers.map((provider) => (
                <Box key={provider.name} sx={{ mb: 1 }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    {provider.available ? (
                      <CheckCircleIcon color="success" fontSize="small" />
                    ) : (
                      <ErrorIcon color="error" fontSize="small" />
                    )}
                    <Typography variant="subtitle2">{provider.description}</Typography>
                  </Box>
                  <Box sx={{ ml: 3 }}>
                    {provider.features.map((feature, idx) => (
                      <Chip
                        key={idx}
                        label={feature}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <Button
          variant="outlined"
          onClick={fetchData}
          disabled={loading}
        >
          {t('settings.provider.refreshStatus')}
        </Button>
      </Box>
    </Box>
  );
}

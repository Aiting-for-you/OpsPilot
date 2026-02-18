import { useState, useEffect } from 'react';
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
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [providers, setProviders] = useState<ProvidersList | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, listRes] = await Promise.all([
        api.get('/providers/status'),
        api.get('/providers/list'),
      ]);

      if (statusRes.data.success) {
        setStatus(statusRes.data);
      }
      if (listRes.data.success) {
        setProviders(listRes.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = async (providerType: string, providerName: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/providers/set', {
        provider_type: providerType,
        provider: providerName,
      });

      if (response.data.success) {
        setSuccess(response.data.message);
        // 更新状态
        if (status) {
          setStatus({
            ...status,
            [`${providerType}_provider`]: providerName,
          });
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '切换失败');
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
        提供者配置
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
                审批提供者
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                选择用于处理敏感操作审批的服务
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>当前审批提供者</InputLabel>
                <Select
                  value={status?.approval_provider || ''}
                  onChange={(e) => handleProviderChange('approval', e.target.value)}
                  disabled={loading}
                >
                  {providers?.approval_providers.map((provider) => (
                    <MenuItem key={provider.name} value={provider.name}>
                      <Box>
                        <Typography>{provider.description}</Typography>
                        {provider.name === status?.approval_provider && (
                          <Chip
                            size="small"
                            label="当前"
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
                记忆提供者
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                选择用于管理对话记忆的服务
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>当前记忆提供者</InputLabel>
                <Select
                  value={status?.memory_provider || ''}
                  onChange={(e) => handleProviderChange('memory', e.target.value)}
                  disabled={loading}
                >
                  {providers?.memory_providers.map((provider) => (
                    <MenuItem key={provider.name} value={provider.name}>
                      <Box>
                        <Typography>{provider.description}</Typography>
                        {provider.name === status?.memory_provider && (
                          <Chip
                            size="small"
                            label="当前"
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
                评估提供者
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                选择用于评估Agent性能的服务
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>当前评估提供者</InputLabel>
                <Select
                  value={status?.evaluation_provider || ''}
                  onChange={(e) => handleProviderChange('evaluation', e.target.value)}
                  disabled={loading}
                >
                  {providers?.evaluation_providers.map((provider) => (
                    <MenuItem key={provider.name} value={provider.name}>
                      <Box>
                        <Typography>{provider.description}</Typography>
                        {provider.name === status?.evaluation_provider && (
                          <Chip
                            size="small"
                            label="当前"
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
          刷新状态
        </Button>
      </Box>
    </Box>
  );
}

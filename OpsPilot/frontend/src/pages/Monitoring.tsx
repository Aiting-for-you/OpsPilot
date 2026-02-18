import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Switch,
  FormControlLabel,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Token as TokenIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  OpenInNew as OpenInNewIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  record_count: number;
}

interface AgentUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  call_count: number;
}

interface ModelUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost: number;
  call_count: number;
}

interface ObservabilityStatus {
  studio: {
    available: boolean;
    initialized: boolean;
    dashboard_url: string | null;
  };
  langsmith: {
    available: boolean;
    initialized: boolean;
    project: string | null;
    project_url: string | null;
  };
}

const Monitoring: React.FC = () => {
  const [tokenUsage, setTokenUsage] = useState<TokenUsage | null>(null);
  const [agentUsage, setAgentUsage] = useState<Record<string, AgentUsage>>({});
  const [modelUsage, setModelUsage] = useState<Record<string, ModelUsage>>({});
  const [observability, setObservability] = useState<ObservabilityStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [usageRes, agentRes, modelRes, obsRes] = await Promise.all([
        api.get('/tokens/usage'),
        api.get('/tokens/by-agent'),
        api.get('/tokens/by-model'),
        api.get('/observability/status'),
      ]);
      
      if (usageRes.data.success) {
        setTokenUsage(usageRes.data.data.total);
      }
      if (agentRes.data.success) {
        setAgentUsage(agentRes.data.data);
      }
      if (modelRes.data.success) {
        setModelUsage(modelRes.data.data);
      }
      if (obsRes.data.success) {
        setObservability(obsRes.data.data);
      }
    } catch (err: any) {
      setError(err.message || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStudioToggle = async () => {
    try {
      if (observability?.studio.initialized) {
        await api.post('/observability/studio/stop');
      } else {
        await api.post('/observability/studio/start');
      }
      fetchAllData();
    } catch (err: any) {
      setError(err.message || '操作失败');
    }
  };

  const handleLangSmithToggle = async () => {
    try {
      if (observability?.langsmith.initialized) {
        await api.post('/observability/langsmith/stop');
      } else {
        await api.post('/observability/langsmith/start');
      }
      fetchAllData();
    } catch (err: any) {
      setError(err.message || '操作失败');
    }
  };

  const handleResetTokens = async () => {
    try {
      await api.post('/tokens/reset');
      fetchAllData();
    } catch (err: any) {
      setError(err.message || '重置失败');
    }
  };

  const formatCost = (cost: number) => `$${cost.toFixed(4)}`;
  const formatTokens = (tokens: number) => tokens.toLocaleString();

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AssessmentIcon /> 监控面板
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchAllData}
          disabled={loading}
        >
          刷新
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Token 使用概览 */}
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <TokenIcon color="primary" /> Token 使用概览
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>
                总 Tokens
              </Typography>
              <Typography variant="h4">
                {tokenUsage ? formatTokens(tokenUsage.total_tokens) : '0'}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8, mt: 1 }}>
                {tokenUsage?.record_count || 0} 次调用
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>
                提示词 Tokens
              </Typography>
              <Typography variant="h4">
                {tokenUsage ? formatTokens(tokenUsage.prompt_tokens) : '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>
                补全 Tokens
              </Typography>
              <Typography variant="h4">
                {tokenUsage ? formatTokens(tokenUsage.completion_tokens) : '0'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ opacity: 0.9 }}>
                总成本
              </Typography>
              <Typography variant="h4">
                {tokenUsage ? formatCost(tokenUsage.total_cost) : '$0.00'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
        <Button
          variant="outlined"
          color="warning"
          onClick={handleResetTokens}
        >
          重置统计
        </Button>
      </Box>

      {/* 可观测性控制 */}
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <MemoryIcon color="primary" /> 可观测性控制
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6">AgentScope Studio</Typography>
                  <Typography variant="body2" color="text.secondary">
                    多智能体可视化监控面板
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={observability?.studio.initialized || false}
                      onChange={handleStudioToggle}
                      disabled={!observability?.studio.available}
                    />
                  }
                  label=""
                />
              </Box>
              
              {observability?.studio.initialized && observability.studio.dashboard_url && (
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    endIcon={<OpenInNewIcon />}
                    onClick={() => window.open(observability.studio.dashboard_url!, '_blank')}
                  >
                    打开 Dashboard
                  </Button>
                </Box>
              )}
              
              {!observability?.studio.available && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  AgentScope 未安装，Studio 功能不可用
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6">LangSmith</Typography>
                  <Typography variant="body2" color="text.secondary">
                    LangChain 链路追踪平台
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={observability?.langsmith.initialized || false}
                      onChange={handleLangSmithToggle}
                      disabled={!observability?.langsmith.available}
                    />
                  }
                  label=""
                />
              </Box>
              
              {observability?.langsmith.initialized && observability.langsmith.project_url && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    项目: {observability.langsmith.project}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    endIcon={<OpenInNewIcon />}
                    onClick={() => window.open(observability.langsmith.project_url!, '_blank')}
                    sx={{ mt: 1 }}
                  >
                    打开 LangSmith
                  </Button>
                </Box>
              )}
              
              {!observability?.langsmith.available && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  LANGCHAIN_API_KEY 未设置
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Agent 使用统计 */}
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUpIcon color="primary" /> Agent Token 使用
      </Typography>

      <Card sx={{ mb: 3 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Agent</TableCell>
                <TableCell align="right">调用次数</TableCell>
                <TableCell align="right">提示词 Tokens</TableCell>
                <TableCell align="right">补全 Tokens</TableCell>
                <TableCell align="right">总 Tokens</TableCell>
                <TableCell align="right">成本</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(agentUsage).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    暂无数据
                  </TableCell>
                </TableRow>
              ) : (
                Object.entries(agentUsage).map(([agent, usage]) => (
                  <TableRow key={agent}>
                    <TableCell>
                      <Chip label={agent} size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell align="right">{usage.call_count}</TableCell>
                    <TableCell align="right">{formatTokens(usage.prompt_tokens)}</TableCell>
                    <TableCell align="right">{formatTokens(usage.completion_tokens)}</TableCell>
                    <TableCell align="right">{formatTokens(usage.total_tokens)}</TableCell>
                    <TableCell align="right">{formatCost(usage.total_cost)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* 模型使用统计 */}
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <MemoryIcon color="primary" /> 模型 Token 使用
      </Typography>

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>模型</TableCell>
                <TableCell align="right">调用次数</TableCell>
                <TableCell align="right">提示词 Tokens</TableCell>
                <TableCell align="right">补全 Tokens</TableCell>
                <TableCell align="right">总 Tokens</TableCell>
                <TableCell align="right">成本</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(modelUsage).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    暂无数据
                  </TableCell>
                </TableRow>
              ) : (
                Object.entries(modelUsage).map(([model, usage]) => (
                  <TableRow key={model}>
                    <TableCell>
                      <Chip label={model} size="small" color="secondary" variant="outlined" />
                    </TableCell>
                    <TableCell align="right">{usage.call_count}</TableCell>
                    <TableCell align="right">{formatTokens(usage.prompt_tokens)}</TableCell>
                    <TableCell align="right">{formatTokens(usage.completion_tokens)}</TableCell>
                    <TableCell align="right">{formatTokens(usage.total_tokens)}</TableCell>
                    <TableCell align="right">{formatCost(usage.total_cost)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {loading && (
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress />
        </Box>
      )}
    </Box>
  );
};

export default Monitoring;
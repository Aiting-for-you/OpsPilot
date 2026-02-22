import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Tab,
  Tabs,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material';
import {
  Build as BuildIcon,
  Search as SearchIcon,
  Compress as CompressIcon,
  Healing as HealingIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

interface IndexedTool {
  name: string;
  category: string;
  keywords: string[];
  description: string;
}

interface RetrievedTool {
  name: string;
  description: string;
  tokens: number;
  relevance: number;
}

interface CompressedTool {
  name: string;
  original_tokens: number;
  compressed_tokens: number;
  compression_ratio: number;
}

const ToolOptimization: React.FC = () => {
  const { t } = useTranslation();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 索引相关状态
  const [indexStats, setIndexStats] = useState<{
    indexed_count: number;
    categories: Record<string, number>;
  } | null>(null);

  // 检索相关状态
  const [query, setQuery] = useState('');
  const [maxTools, setMaxTools] = useState(10);
  const [maxTokens, setMaxTokens] = useState(2000);
  const [strategy, setStrategy] = useState('hybrid');
  const [retrievedTools, setRetrievedTools] = useState<RetrievedTool[]>([]);
  const [retrievalTime, setRetrievalTime] = useState(0);

  // 压缩相关状态
  const [compressLevel, setCompressLevel] = useState('medium');
  const [maxTokensPerTool, setMaxTokensPerTool] = useState(100);
  const [compressedTools, setCompressedTools] = useState<CompressedTool[]>([]);
  const [compressionStats, setCompressionStats] = useState<{
    original_tokens: number;
    compressed_tokens: number;
    compression_ratio: number;
  } | null>(null);

  // 自愈相关状态
  const [healToolName, setHealToolName] = useState('');
  const [healParams, setHealParams] = useState('{}');
  const [healError, setHealError] = useState('{}');
  const [healResult, setHealResult] = useState<any>(null);

  const handleBuildIndex = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<any>('/tools');
      if (response.success) {
        const tools = response.tools || [];
        const indexRes = await api.post<any>('/tools/index', {
          tools,
          force_rebuild: true,
        });
        
        if (indexRes.success) {
          setIndexStats(indexRes);
          setSuccess(t('toolOptimization.indexedSuccess', { count: indexRes.indexed_count }));
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('toolOptimization.indexError'));
    } finally {
      setLoading(false);
    }
  };

  const handleRetrieve = async () => {
    if (!query.trim()) {
      setError(t('toolOptimization.queryRequired'));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post<any>('/tools/retrieve', {
        query,
        max_tools: maxTools,
        max_tokens: maxTokens,
        strategy,
      });

      if (response.success) {
        setRetrievedTools(response.tools);
        setRetrievalTime(response.retrieval_time_ms);
        setSuccess(t('toolOptimization.retrievedSuccess', { count: response.tools.length }));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('toolOptimization.searchError'));
    } finally {
      setLoading(false);
    }
  };

  const handleCompress = async () => {
    if (retrievedTools.length === 0) {
      setError(t('toolOptimization.searchFirst'));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post<any>('/tools/compress', {
        tools: retrievedTools,
        level: compressLevel,
        max_tokens_per_tool: maxTokensPerTool,
      });

      if (response.success) {
        setCompressedTools(response.compressed_tools);
        setCompressionStats({
          original_tokens: response.original_tokens,
          compressed_tokens: response.compressed_tokens,
          compression_ratio: response.compression_ratio,
        });
        setSuccess(t('toolOptimization.compressSuccess', { ratio: (response.compression_ratio * 100).toFixed(1) }));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('toolOptimization.compressError'));
    } finally {
      setLoading(false);
    }
  };

  const handleHeal = async () => {
    if (!healToolName.trim()) {
      setError(t('toolOptimization.toolNameRequired'));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      let params = {};
      let errorInfo = {};
      
      try {
        params = JSON.parse(healParams);
        errorInfo = JSON.parse(healError);
      } catch {
        setError(t('toolOptimization.formatError'));
        setLoading(false);
        return;
      }

      const response = await api.post<any>('/tools/heal', {
        tool_name: healToolName,
        params,
        error_info: errorInfo,
        max_retries: 3,
      });

      if (response.success) {
        setHealResult(response);
        setSuccess(t('toolOptimization.healSuccess'));
      } else {
        setHealResult(response);
        setError(t('toolOptimization.healError'));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('toolOptimization.healError'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BuildIcon /> {t('toolOptimization.title')}
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

      <Card sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab icon={<BuildIcon />} label={t('toolOptimization.toolIndex')} />
          <Tab icon={<SearchIcon />} label={t('toolOptimization.toolSearch')} />
          <Tab icon={<CompressIcon />} label={t('toolOptimization.toolCompress')} />
          <Tab icon={<HealingIcon />} label={t('toolOptimization.toolHeal')} />
        </Tabs>

        <CardContent>
          {/* {t('toolOptimization.toolIndex')} */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  onClick={handleBuildIndex}
                  disabled={loading}
                >
                  {t('toolOptimization.buildIndex')}
                </Button>
              </Grid>

              {indexStats && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {t('toolOptimization.indexStats')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('toolOptimization.indexedTools')}: {indexStats.indexed_count} {t('toolOptimization.tools')}
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          {t('toolOptimization.categoryDistribution')}:
                        </Typography>
                        {Object.entries(indexStats.categories).map(([category, count]) => (
                          <Chip
                            key={category}
                            label={`${category}: ${count}`}
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* {t('toolOptimization.toolSearch')} */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('toolOptimization.queryText')}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={t('toolOptimization.queryPlaceholder')}
                  sx={{ mb: 2 }}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('toolOptimization.maxTools')}
                  value={maxTools}
                  onChange={(e) => setMaxTools(parseInt(e.target.value))}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('toolOptimization.maxTokens')}
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>{t('toolOptimization.searchStrategy')}</InputLabel>
                  <Select
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                  >
                    <MenuItem value="semantic">{t('toolOptimization.semantic')}</MenuItem>
                    <MenuItem value="keyword">{t('toolOptimization.keyword')}</MenuItem>
                    <MenuItem value="hybrid">{t('toolOptimization.hybrid')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={handleRetrieve}
                  disabled={loading}
                >
                  {t('toolOptimization.searchTools')}
                </Button>
              </Grid>

              {retrievedTools.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('toolOptimization.retrieved')} {retrievedTools.length} {t('toolOptimization.toolsFound')} ({t('toolOptimization.timeSpent')}: {retrievalTime}ms)
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>{t('toolOptimization.toolName')}</TableCell>
                          <TableCell>{t('toolOptimization.description')}</TableCell>
                          <TableCell>{t('toolOptimization.tokenCount')}</TableCell>
                          <TableCell>{t('toolOptimization.relevance')}</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {retrievedTools.map((tool, index) => (
                          <TableRow key={index}>
                            <TableCell>{tool.name}</TableCell>
                            <TableCell>{tool.description}</TableCell>
                            <TableCell>{tool.tokens}</TableCell>
                            <TableCell>{(tool.relevance * 100).toFixed(1)}%</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* {t('toolOptimization.toolCompress')} */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('toolOptimization.compressionLevel')}</InputLabel>
                  <Select
                    value={compressLevel}
                    onChange={(e) => setCompressLevel(e.target.value)}
                  >
                    <MenuItem value="low">{t('toolOptimization.low')}</MenuItem>
                    <MenuItem value="medium">{t('toolOptimization.medium')}</MenuItem>
                    <MenuItem value="high">{t('toolOptimization.high')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('toolOptimization.maxTokensPerTool')}
                  value={maxTokensPerTool}
                  onChange={(e) => setMaxTokensPerTool(parseInt(e.target.value))}
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<CompressIcon />}
                  onClick={handleCompress}
                  disabled={loading || retrievedTools.length === 0}
                >
                  {t('toolOptimization.compressDescriptions')}
                </Button>
              </Grid>

              {compressionStats && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {t('toolOptimization.compressionStats')}
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={4}>
                          <Typography variant="body2" color="text.secondary">
                            {t('toolOptimization.originalTokens')}: {compressionStats.original_tokens}
                          </Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="body2" color="text.secondary">
                            {t('toolOptimization.compressedTokens')}: {compressionStats.compressed_tokens}
                          </Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="body2" color="text.secondary">
                            {t('toolOptimization.compressionRatio')}: {(compressionStats.compression_ratio * 100).toFixed(1)}%
                          </Typography>
                        </Grid>
                      </Grid>
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={compressionStats.compression_ratio * 100}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* {t('toolOptimization.toolHeal')} */}
          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('toolOptimization.toolNameLabel')}
                  value={healToolName}
                  onChange={(e) => setHealToolName(e.target.value)}
                  placeholder={t('toolOptimization.toolNamePlaceholder')}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label={t('toolOptimization.toolParams')}
                  value={healParams}
                  onChange={(e) => setHealParams(e.target.value)}
                  placeholder='{"param1": "value1"}'
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label={t('toolOptimization.errorInfo')}
                  value={healError}
                  onChange={(e) => setHealError(e.target.value)}
                  placeholder={t('toolOptimization.errorPlaceholder')}
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<HealingIcon />}
                  onClick={handleHeal}
                  disabled={loading}
                >
                  {t('toolOptimization.executeHeal')}
                </Button>
              </Grid>

              {healResult && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {t('toolOptimization.healResult')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('toolOptimization.success')}: {healResult.success ? t('toolOptimization.success') : t('toolOptimization.fail')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('toolOptimization.strategy')}: {healResult.strategy_used}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('toolOptimization.retryCount')}: {healResult.retry_count}
                      </Typography>
                      {healResult.result && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2">{t('toolOptimization.result')}:</Typography>
                          <pre>{JSON.stringify(healResult.result, null, 2)}</pre>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>

      {loading && <LinearProgress />}
    </Box>
  );
};

export default ToolOptimization;

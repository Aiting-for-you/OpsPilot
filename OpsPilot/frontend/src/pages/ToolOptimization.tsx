import React, { useState } from 'react';
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
      const response = await api.get('/tools');
      if (response.data.success) {
        const tools = response.data.tools || [];
        const indexRes = await api.post('/tools/index', {
          tools,
          force_rebuild: true,
        });
        
        if (indexRes.data.success) {
          setIndexStats(indexRes.data);
          setSuccess(`成功索引 ${indexRes.data.indexed_count} 个工具`);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '索引构建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRetrieve = async () => {
    if (!query.trim()) {
      setError('请输入查询文本');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/tools/retrieve', {
        query,
        max_tools: maxTools,
        max_tokens: maxTokens,
        strategy,
      });

      if (response.data.success) {
        setRetrievedTools(response.data.tools);
        setRetrievalTime(response.data.retrieval_time_ms);
        setSuccess(`检索到 ${response.data.tools.length} 个工具`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '检索失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCompress = async () => {
    if (retrievedTools.length === 0) {
      setError('请先检索工具');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/tools/compress', {
        tools: retrievedTools,
        level: compressLevel,
        max_tokens_per_tool: maxTokensPerTool,
      });

      if (response.data.success) {
        setCompressedTools(response.data.compressed_tools);
        setCompressionStats({
          original_tokens: response.data.original_tokens,
          compressed_tokens: response.data.compressed_tokens,
          compression_ratio: response.data.compression_ratio,
        });
        setSuccess(`压缩完成，压缩率: ${(response.data.compression_ratio * 100).toFixed(1)}%`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '压缩失败');
    } finally {
      setLoading(false);
    }
  };

  const handleHeal = async () => {
    if (!healToolName.trim()) {
      setError('请输入工具名称');
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
        setError('参数或错误信息格式不正确');
        setLoading(false);
        return;
      }

      const response = await api.post('/tools/heal', {
        tool_name: healToolName,
        params,
        error_info: errorInfo,
        max_retries: 3,
      });

      if (response.data.success) {
        setHealResult(response.data);
        setSuccess('自愈成功');
      } else {
        setHealResult(response.data);
        setError('自愈失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '自愈失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BuildIcon /> 工具优化管理
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
          <Tab icon={<BuildIcon />} label="工具索引" />
          <Tab icon={<SearchIcon />} label="工具检索" />
          <Tab icon={<CompressIcon />} label="工具压缩" />
          <Tab icon={<HealingIcon />} label="工具自愈" />
        </Tabs>

        <CardContent>
          {/* 工具索引 */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  onClick={handleBuildIndex}
                  disabled={loading}
                >
                  构建工具索引
                </Button>
              </Grid>

              {indexStats && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        索引统计
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        已索引工具: {indexStats.indexed_count} 个
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          按类别分布:
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

          {/* 工具检索 */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="查询文本"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="输入查询文本，例如：查询供应商信息"
                  sx={{ mb: 2 }}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="最大工具数"
                  value={maxTools}
                  onChange={(e) => setMaxTools(parseInt(e.target.value))}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="最大Token数"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>检索策略</InputLabel>
                  <Select
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                  >
                    <MenuItem value="semantic">语义相似</MenuItem>
                    <MenuItem value="keyword">关键词匹配</MenuItem>
                    <MenuItem value="hybrid">混合策略</MenuItem>
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
                  检索工具
                </Button>
              </Grid>

              {retrievedTools.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    检索到 {retrievedTools.length} 个工具 (耗时: {retrievalTime}ms)
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>工具名称</TableCell>
                          <TableCell>描述</TableCell>
                          <TableCell>Token数</TableCell>
                          <TableCell>相关度</TableCell>
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

          {/* 工具压缩 */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>压缩级别</InputLabel>
                  <Select
                    value={compressLevel}
                    onChange={(e) => setCompressLevel(e.target.value)}
                  >
                    <MenuItem value="low">低压缩</MenuItem>
                    <MenuItem value="medium">中压缩</MenuItem>
                    <MenuItem value="high">高压缩</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="每个工具最大Token数"
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
                  压缩工具描述
                </Button>
              </Grid>

              {compressionStats && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        压缩统计
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={4}>
                          <Typography variant="body2" color="text.secondary">
                            原始Token数: {compressionStats.original_tokens}
                          </Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="body2" color="text.secondary">
                            压缩后Token数: {compressionStats.compressed_tokens}
                          </Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="body2" color="text.secondary">
                            压缩率: {(compressionStats.compression_ratio * 100).toFixed(1)}%
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

          {/* 工具自愈 */}
          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="工具名称"
                  value={healToolName}
                  onChange={(e) => setHealToolName(e.target.value)}
                  placeholder="输入失败的工具名称"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="工具参数 (JSON)"
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
                  label="错误信息 (JSON)"
                  value={healError}
                  onChange={(e) => setHealError(e.target.value)}
                  placeholder='{"error_type": "timeout", "message": "请求超时"}'
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<HealingIcon />}
                  onClick={handleHeal}
                  disabled={loading}
                >
                  执行自愈
                </Button>
              </Grid>

              {healResult && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        自愈结果
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        状态: {healResult.success ? '成功' : '失败'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        使用策略: {healResult.strategy_used}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        重试次数: {healResult.retry_count}
                      </Typography>
                      {healResult.result && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2">结果:</Typography>
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

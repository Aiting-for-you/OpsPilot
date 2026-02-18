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
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Weight as WeightIcon,
  Warning as WarningIcon,
  Merge as MergeIcon,
  Assessment as AssessmentIcon,
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

interface WeightFactors {
  time_decay: number;
  frequency: number;
  relevance: number;
  timeliness: number;
  confidence: number;
}

interface Conflict {
  type: string;
  memory_ids: string[];
  description: string;
  severity: string;
}

interface Resolution {
  strategy: string;
  kept_memory_id: string;
  reason: string;
}

interface MemoryCluster {
  id: string;
  size: number;
  theme: string;
  memories: string[];
}

interface KnowledgePattern {
  pattern: string;
  frequency: number;
  confidence: number;
}

const MemoryOptimization: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 权重相关状态
  const [weightMemoryId, setWeightMemoryId] = useState('');
  const [weightContent, setWeightContent] = useState('');
  const [weightMetadata, setWeightMetadata] = useState('{}');
  const [weightResult, setWeightResult] = useState<{
    weight: number;
    factors: WeightFactors;
  } | null>(null);

  // 冲突相关状态
  const [conflictMemories, setConflictMemories] = useState('[]');
  const [conflictCheckType, setConflictCheckType] = useState('all');
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [resolutions, setResolutions] = useState<Resolution[]>([]);

  // 巩固相关状态
  const [consolidateMemories, setConsolidateMemories] = useState('[]');
  const [consolidateType, setConsolidateType] = useState('auto');
  const [minClusterSize, setMinClusterSize] = useState(3);
  const [clusters, setClusters] = useState<MemoryCluster[]>([]);
  const [patterns, setPatterns] = useState<KnowledgePattern[]>([]);
  const [consolidationStats, setConsolidationStats] = useState<{
    consolidated_count: number;
    reduction_ratio: number;
  } | null>(null);

  // 统计相关状态
  const [memoryStats, setMemoryStats] = useState<{
    total_memories: number;
    weighted_memories: number;
    conflict_count: number;
    consolidated_memories: number;
    patterns_extracted: number;
  } | null>(null);

  const handleCalculateWeight = async () => {
    if (!weightContent.trim()) {
      setError('请输入记忆内容');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      let metadata = {};
      try {
        metadata = JSON.parse(weightMetadata);
      } catch {
        setError('元数据格式不正确');
        setLoading(false);
        return;
      }

      const response = await api.post('/memory/weight', {
        memory_id: weightMemoryId || `mem-${Date.now()}`,
        content: weightContent,
        metadata,
      });

      if (response.data.success) {
        setWeightResult({
          weight: response.data.weight,
          factors: response.data.factors,
        });
        setSuccess(`权重计算完成: ${response.data.weight.toFixed(4)}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '权重计算失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDetectConflicts = async () => {
    setLoading(true);
    setError(null);
    try {
      let memories = [];
      try {
        memories = JSON.parse(conflictMemories);
      } catch {
        setError('记忆列表格式不正确');
        setLoading(false);
        return;
      }

      const response = await api.post('/memory/conflict', {
        memories,
        check_type: conflictCheckType,
      });

      if (response.data.success) {
        setConflicts(response.data.conflicts);
        setResolutions(response.data.resolutions);
        setSuccess(`检测到 ${response.data.conflict_count} 个冲突`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '冲突检测失败');
    } finally {
      setLoading(false);
    }
  };

  const handleConsolidate = async () => {
    setLoading(true);
    setError(null);
    try {
      let memories = [];
      try {
        memories = JSON.parse(consolidateMemories);
      } catch {
        setError('记忆列表格式不正确');
        setLoading(false);
        return;
      }

      const response = await api.post('/memory/consolidate', {
        memories,
        consolidation_type: consolidateType,
        min_cluster_size: minClusterSize,
      });

      if (response.data.success) {
        setClusters(response.data.clusters);
        setPatterns(response.data.patterns);
        setConsolidationStats({
          consolidated_count: response.data.consolidated_count,
          reduction_ratio: response.data.reduction_ratio,
        });
        setSuccess(`巩固完成，压缩率: ${(response.data.reduction_ratio * 100).toFixed(1)}%`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '记忆巩固失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/memory/stats');
      if (response.data.success) {
        setMemoryStats(response.data);
        setSuccess('统计信息获取成功');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '统计信息获取失败');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    handleFetchStats();
  }, []);

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <MemoryIcon /> 记忆优化管理
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

      {/* 统计卡片 */}
      {memoryStats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  总记忆数
                </Typography>
                <Typography variant="h4">{memoryStats.total_memories}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  已加权记忆
                </Typography>
                <Typography variant="h4">{memoryStats.weighted_memories}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  冲突数
                </Typography>
                <Typography variant="h4">{memoryStats.conflict_count}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  已巩固记忆
                </Typography>
                <Typography variant="h4">{memoryStats.consolidated_memories}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  提取模式数
                </Typography>
                <Typography variant="h4">{memoryStats.patterns_extracted}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Card>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab icon={<WeightIcon />} label="权重计算" />
          <Tab icon={<WarningIcon />} label="冲突检测" />
          <Tab icon={<MergeIcon />} label="记忆巩固" />
          <Tab icon={<AssessmentIcon />} label="统计分析" />
        </Tabs>

        <CardContent>
          {/* 权重计算 */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="记忆ID（可选）"
                  value={weightMemoryId}
                  onChange={(e) => setWeightMemoryId(e.target.value)}
                  placeholder="留空将自动生成"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="记忆内容"
                  value={weightContent}
                  onChange={(e) => setWeightContent(e.target.value)}
                  placeholder="输入记忆内容"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="元数据 (JSON)"
                  value={weightMetadata}
                  onChange={(e) => setWeightMetadata(e.target.value)}
                  placeholder='{"source": "user", "timestamp": "2026-02-18"}'
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<WeightIcon />}
                  onClick={handleCalculateWeight}
                  disabled={loading}
                >
                  计算权重
                </Button>
              </Grid>

              {weightResult && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        权重结果
                      </Typography>
                      <Typography variant="h4" color="primary" gutterBottom>
                        {weightResult.weight.toFixed(4)}
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        权重因子:
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            时间衰减: {weightResult.factors.time_decay.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            访问频率: {weightResult.factors.frequency.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            相关性: {weightResult.factors.relevance.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            时效性: {weightResult.factors.timeliness.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            可信度: {weightResult.factors.confidence.toFixed(4)}
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* 冲突检测 */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="记忆列表 (JSON)"
                  value={conflictMemories}
                  onChange={(e) => setConflictMemories(e.target.value)}
                  placeholder='[{"id": "1", "content": "价格=10"}, {"id": "2", "content": "价格=15"}]'
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>检查类型</InputLabel>
                  <Select
                    value={conflictCheckType}
                    onChange={(e) => setConflictCheckType(e.target.value)}
                  >
                    <MenuItem value="all">全部检查</MenuItem>
                    <MenuItem value="contradiction">矛盾检测</MenuItem>
                    <MenuItem value="duplicate">重复检测</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<WarningIcon />}
                  onClick={handleDetectConflicts}
                  disabled={loading}
                >
                  检测冲突
                </Button>
              </Grid>

              {conflicts.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    检测到的冲突
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>冲突类型</TableCell>
                          <TableCell>描述</TableCell>
                          <TableCell>严重程度</TableCell>
                          <TableCell>涉及记忆</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {conflicts.map((conflict, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <Chip label={conflict.type} size="small" />
                            </TableCell>
                            <TableCell>{conflict.description}</TableCell>
                            <TableCell>
                              <Chip
                                label={conflict.severity}
                                size="small"
                                color={conflict.severity === 'high' ? 'error' : 'warning'}
                              />
                            </TableCell>
                            <TableCell>{conflict.memory_ids.join(', ')}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              )}

              {resolutions.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    解决方案
                  </Typography>
                  <List>
                    {resolutions.map((resolution, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={`策略: ${resolution.strategy}`}
                          secondary={`保留记忆: ${resolution.kept_memory_id} - ${resolution.reason}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* 记忆巩固 */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="待巩固记忆列表 (JSON)"
                  value={consolidateMemories}
                  onChange={(e) => setConsolidateMemories(e.target.value)}
                  placeholder='[{"content": "记忆1"}, {"content": "记忆2"}]'
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>巩固类型</InputLabel>
                  <Select
                    value={consolidateType}
                    onChange={(e) => setConsolidateType(e.target.value)}
                  >
                    <MenuItem value="auto">自动</MenuItem>
                    <MenuItem value="cluster">聚类</MenuItem>
                    <MenuItem value="pattern">模式提取</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="最小簇大小"
                  value={minClusterSize}
                  onChange={(e) => setMinClusterSize(parseInt(e.target.value))}
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<MergeIcon />}
                  onClick={handleConsolidate}
                  disabled={loading}
                >
                  执行巩固
                </Button>
              </Grid>

              {consolidationStats && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        巩固统计
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            巩固记忆数: {consolidationStats.consolidated_count}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            压缩率: {(consolidationStats.reduction_ratio * 100).toFixed(1)}%
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {clusters.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    记忆簇 ({clusters.length})
                  </Typography>
                  {clusters.map((cluster) => (
                    <Card key={cluster.id} variant="outlined" sx={{ mb: 1 }}>
                      <CardContent>
                        <Typography variant="subtitle1">
                          {cluster.theme} ({cluster.size} 个记忆)
                        </Typography>
                        <List dense>
                          {cluster.memories.slice(0, 3).map((mem, i) => (
                            <ListItem key={i}>
                              <ListItemText primary={mem} />
                            </ListItem>
                          ))}
                          {cluster.memories.length > 3 && (
                            <ListItem>
                              <ListItemText
                                secondary={`还有 ${cluster.memories.length - 3} 个记忆...`}
                              />
                            </ListItem>
                          )}
                        </List>
                      </CardContent>
                    </Card>
                  ))}
                </Grid>
              )}

              {patterns.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    提取的知识模式
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>模式</TableCell>
                          <TableCell>频率</TableCell>
                          <TableCell>置信度</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {patterns.map((pattern, index) => (
                          <TableRow key={index}>
                            <TableCell>{pattern.pattern}</TableCell>
                            <TableCell>{pattern.frequency}</TableCell>
                            <TableCell>{(pattern.confidence * 100).toFixed(1)}%</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* 统计分析 */}
          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  startIcon={<AssessmentIcon />}
                  onClick={handleFetchStats}
                  disabled={loading}
                >
                  刷新统计
                </Button>
              </Grid>

              {memoryStats && (
                <Grid item xs={12}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            记忆总览
                          </Typography>
                          <List>
                            <ListItem>
                              <ListItemText
                                primary="总记忆数"
                                secondary={memoryStats.total_memories}
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemText
                                primary="已加权记忆"
                                secondary={memoryStats.weighted_memories}
                              />
                            </ListItem>
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            优化统计
                          </Typography>
                          <List>
                            <ListItem>
                              <ListItemText
                                primary="冲突数"
                                secondary={memoryStats.conflict_count}
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemText
                                primary="已巩固记忆"
                                secondary={memoryStats.consolidated_memories}
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemText
                                primary="提取模式数"
                                secondary={memoryStats.patterns_extracted}
                              />
                            </ListItem>
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
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

export default MemoryOptimization;

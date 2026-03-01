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
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Memory as MemoryIcon,
  FitnessCenter as WeightIcon,
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
  const { t } = useTranslation();
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
      setError(t('memoryOptimization.contentRequired'));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      let metadata = {};
      try {
        metadata = JSON.parse(weightMetadata);
      } catch {
        setError(t('memoryOptimization.metadataFormatError'));
        setLoading(false);
        return;
      }

      const response = await api.post<{success: boolean; weight?: number; factors?: string[]}>('/memory/weight', {
        memory_id: weightMemoryId || `mem-${Date.now()}`,
        content: weightContent,
        metadata,
      });

      if (response.data.success) {
        const factors = response.data.factors;
        setWeightResult({
          weight: response.data.weight ?? 0,
          factors: Array.isArray(factors) 
            ? { time_decay: 0, frequency: 0, relevance: 0, timeliness: 0, confidence: 0 }
            : (factors ?? { time_decay: 0, frequency: 0, relevance: 0, timeliness: 0, confidence: 0 }),
        });
        setSuccess(t('memoryOptimization.weightComplete', { weight: (response.data.weight ?? 0).toFixed(4) }));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('memoryOptimization.weightError'));
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
        setError(t('memoryOptimization.memoryListFormatError'));
        setLoading(false);
        return;
      }

      const response = await api.post<{success: boolean; conflicts?: any[]; resolutions?: any[]; conflict_count?: number}>('/memory/conflict', {
        memories,
        check_type: conflictCheckType,
      });

      if (response.data.success) {
        setConflicts(response.data.conflicts ?? []);
        setResolutions(response.data.resolutions ?? []);
        setSuccess(t('memoryOptimization.conflictDetected', { count: response.data.conflict_count ?? 0 }));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('memoryOptimization.conflictError'));
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
        setError(t('memoryOptimization.memoryListFormatError'));
        setLoading(false);
        return;
      }

      const response = await api.post<{success: boolean; clusters?: any[]; patterns?: any[]; consolidated_count?: number; reduction_ratio?: number}>('/memory/consolidate', {
        memories,
        consolidation_type: consolidateType,
        min_cluster_size: minClusterSize,
      });

      if (response.data.success) {
        setClusters(response.data.clusters ?? []);
        setPatterns(response.data.patterns ?? []);
        setConsolidationStats({
          consolidated_count: response.data.consolidated_count ?? 0,
          reduction_ratio: response.data.reduction_ratio ?? 0,
        });
        setSuccess(t('memoryOptimization.consolidateComplete', { ratio: ((response.data.reduction_ratio ?? 0) * 100).toFixed(1) }));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || t('memoryOptimization.consolidateError'));
    } finally {
      setLoading(false);
    }
  };

  const handleFetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<{success: boolean; data?: any}>('/memory/stats');
      if (response.data.success && response.data.data) {
        setMemoryStats(response.data.data);
        setSuccess(t('memoryOptimization.statsSuccess'));
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t('memoryOptimization.statsError');
      setError(message);
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
        <MemoryIcon /> {t('memoryOptimization.title')}
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
                  {t('memoryOptimization.totalMemories')}
                </Typography>
                <Typography variant="h4">{memoryStats.total_memories}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  {t('memoryOptimization.weightedMemories')}
                </Typography>
                <Typography variant="h4">{memoryStats.weighted_memories}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  {t('memoryOptimization.conflictCount')}
                </Typography>
                <Typography variant="h4">{memoryStats.conflict_count}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  {t('memoryOptimization.consolidatedMemories')}
                </Typography>
                <Typography variant="h4">{memoryStats.consolidated_memories}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={2.4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  {t('memoryOptimization.extractedPatterns')}
                </Typography>
                <Typography variant="h4">{memoryStats.patterns_extracted}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Card>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab icon={<WeightIcon />} label={t('memoryOptimization.weightCalc')} />
          <Tab icon={<WarningIcon />} label={t('memoryOptimization.conflictDetect')} />
          <Tab icon={<MergeIcon />} label={t('memoryOptimization.memoryConsolidate')} />
          <Tab icon={<AssessmentIcon />} label={t('memoryOptimization.memoryStats')} />
        </Tabs>

        <CardContent>
          {/* 权重计算 */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('memoryOptimization.memoryId')}
                  value={weightMemoryId}
                  onChange={(e) => setWeightMemoryId(e.target.value)}
                  placeholder={t('memoryOptimization.memoryIdPlaceholder')}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label={t('memoryOptimization.memoryContent')}
                  value={weightContent}
                  onChange={(e) => setWeightContent(e.target.value)}
                  placeholder={t('memoryOptimization.contentPlaceholder')}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label={t('memoryOptimization.metadata')}
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
                  {t('memoryOptimization.calculateWeight')}
                </Button>
              </Grid>

              {weightResult && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {t('memoryOptimization.weightResult')}
                      </Typography>
                      <Typography variant="h4" color="primary" gutterBottom>
                        {weightResult.weight.toFixed(4)}
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        {t('memoryOptimization.weightFactors')}:
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.timeDecay')}: {weightResult.factors.time_decay.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.frequency')}: {weightResult.factors.frequency.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.relevance')}: {weightResult.factors.relevance.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.timeliness')}: {weightResult.factors.timeliness.toFixed(4)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.confidence')}: {weightResult.factors.confidence.toFixed(4)}
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
                  label={t('memoryOptimization.memoryList')}
                  value={conflictMemories}
                  onChange={(e) => setConflictMemories(e.target.value)}
                  placeholder='[{"id": "1", "content": "价格=10"}, {"id": "2", "content": "价格=15"}]'
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>{t('memoryOptimization.checkType')}</InputLabel>
                  <Select
                    value={conflictCheckType}
                    onChange={(e) => setConflictCheckType(e.target.value)}
                  >
                    <MenuItem value="all">{t('memoryOptimization.checkAll')}</MenuItem>
                    <MenuItem value="contradiction">{t('memoryOptimization.contradictionCheck')}</MenuItem>
                    <MenuItem value="duplicate">{t('memoryOptimization.duplicateCheck')}</MenuItem>
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
                  {t('memoryOptimization.detectConflicts')}
                </Button>
              </Grid>

                              {conflicts.length > 0 && (
                              <Grid item xs={12}>
                                <Typography variant="h6" gutterBottom>
                                  {t('memoryOptimization.detectedConflicts')}
                                </Typography>
                                <TableContainer component={Paper}>
                                  <Table>
                                    <TableHead>
                                      <TableRow>
                                        <TableCell>{t('memoryOptimization.conflictType')}</TableCell>
                                        <TableCell>{t('memoryOptimization.description')}</TableCell>
                                        <TableCell>{t('memoryOptimization.severity')}</TableCell>
                                        <TableCell>{t('memoryOptimization.involvedMemories')}</TableCell>
                                      </TableRow>
                                    </TableHead>                      <TableBody>
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
                    {t('memoryOptimization.solution')}
                  </Typography>
                  <List>
                    {resolutions.map((resolution, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={`${t('memoryOptimization.strategy')}: ${resolution.strategy}`}
                          secondary={`${t('memoryOptimization.keptMemory')}: ${resolution.kept_memory_id} - ${resolution.reason}`}
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
                  label={t('memoryOptimization.memoriesToConsolidate')}
                  value={consolidateMemories}
                  onChange={(e) => setConsolidateMemories(e.target.value)}
                  placeholder='[{"content": "记忆1"}, {"content": "记忆2"}]'
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('memoryOptimization.consolidateType')}</InputLabel>
                  <Select
                    value={consolidateType}
                    onChange={(e) => setConsolidateType(e.target.value)}
                  >
                    <MenuItem value="auto">{t('memoryOptimization.auto')}</MenuItem>
                    <MenuItem value="cluster">{t('memoryOptimization.clustering')}</MenuItem>
                    <MenuItem value="pattern">{t('memoryOptimization.patternExtraction')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('memoryOptimization.minClusterSize')}
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
                  {t('memoryOptimization.executeConsolidate')}
                </Button>
              </Grid>

              {consolidationStats && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {t('memoryOptimization.consolidationStats')}
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.consolidatedCount')}: {consolidationStats.consolidated_count}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            {t('memoryOptimization.reductionRatio')}: {(consolidationStats.reduction_ratio * 100).toFixed(1)}%
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
                    {t('memoryOptimization.memoryClusters')} ({clusters.length})
                  </Typography>
                  {clusters.map((cluster) => (
                    <Card key={cluster.id} variant="outlined" sx={{ mb: 1 }}>
                      <CardContent>
                        <Typography variant="subtitle1">
                          {cluster.theme} ({cluster.size} {t('memoryOptimization.memories')})
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
                                secondary={`${t('memoryOptimization.moreMemories')} ${cluster.memories.length - 3}...`}
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
                    {t('memoryOptimization.knowledgePatterns')}
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>{t('memoryOptimization.pattern')}</TableCell>
                          <TableCell>{t('memoryOptimization.frequency')}</TableCell>
                          <TableCell>{t('memoryOptimization.confidence')}</TableCell>
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
                  {t('memoryOptimization.refreshStats')}
                </Button>
              </Grid>

              {memoryStats && (
                <Grid item xs={12}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {t('memoryOptimization.memoryOverview')}
                          </Typography>
                          <List>
                            <ListItem>
                              <ListItemText
                                primary={t('memoryOptimization.totalMemories')}
                                secondary={memoryStats.total_memories}
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemText
                                primary={t('memoryOptimization.weightedMemories')}
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
                            {t('memoryOptimization.optimizationStats')}
                          </Typography>
                          <List>
                            <ListItem>
                              <ListItemText
                                primary={t('memoryOptimization.conflictCount')}
                                secondary={memoryStats.conflict_count}
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemText
                                primary={t('memoryOptimization.consolidatedMemories')}
                                secondary={memoryStats.consolidated_memories}
                              />
                            </ListItem>
                            <ListItem>
                              <ListItemText
                                primary={t('memoryOptimization.patternsExtracted')}
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

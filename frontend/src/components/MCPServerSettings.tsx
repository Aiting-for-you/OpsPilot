import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Server,
  Plus,
  Trash2,
  RefreshCw,
  Play,
  Square,
  Check,
  X,
  ChevronDown,
  ChevronRight,
  Wrench,
  AlertCircle,
  Terminal,
} from 'lucide-react';
import { api } from '../services/api';

// Types
interface MCPServer {
  name: string;
  command: string;
  args: string[];
  enabled: boolean;
  auto_connect: boolean;
  description: string;
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  tool_count: number;
  error_message: string;
  connected_at: string | null;
}

interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
  server?: string;
}

// Status Badge Component
function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const config: Record<string, { bg: string; text: string; label: string }> = {
    connected: { bg: 'bg-success/20', text: 'text-success', label: t('mcp.connected') },
    disconnected: { bg: 'bg-gray-300', text: 'text-gray-600', label: t('mcp.disconnected') },
    connecting: { bg: 'bg-warning/20', text: 'text-warning', label: t('mcp.connecting') },
    error: { bg: 'bg-error/20', text: 'text-error', label: t('mcp.error') },
  };
  const { bg, text, label } = config[status] || config.disconnected;

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-mono ${bg} ${text}`}>
      {label}
    </span>
  );
}

// Server Card Component
function ServerCard({
  server,
  onConnect,
  onDisconnect,
  onDelete,
  onEdit,
  onViewTools,
  loading,
}: {
  server: MCPServer;
  onConnect: () => void;
  onDisconnect: () => void;
  onDelete: () => void;
  onEdit: () => void;
  onViewTools: () => void;
  loading: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useTranslation();

  const isConnected = server.status === 'connected';
  const isConnecting = server.status === 'connecting';
  const hasError = server.status === 'error';

  return (
    <div className="card">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              isConnected ? 'bg-success/10' : 'bg-gray-200'
            }`}
          >
            <Server
              className={`w-5 h-5 ${
                isConnected ? 'text-success' : 'text-gray-500'
              }`}
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display text-sm font-semibold text-gray-900">
                {server.name}
              </span>
              <StatusBadge status={server.status} />
              {server.enabled && (
                <span className="px-2 py-0.5 bg-electric/20 text-electric text-xs rounded font-mono">
                  ENABLED
                </span>
              )}
              {server.tool_count > 0 && (
                <span className="text-xs text-gray-400">
                  {server.tool_count} tools
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5 font-mono">
              {server.command} {server.args.join(' ')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="mt-5 pt-5 border-t border-gray-200/50 space-y-4">
          {/* Description */}
          {server.description && (
            <div className="p-3 rounded-lg bg-white/50 border border-gray-200/50">
              <p className="text-sm text-gray-600">{server.description}</p>
            </div>
          )}

          {/* Error Message */}
          {hasError && server.error_message && (
            <div className="p-3 rounded-lg bg-error/10 border border-error/20 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-error flex-shrink-0 mt-0.5" />
              <span className="text-sm text-error">{server.error_message}</span>
            </div>
          )}

          {/* Connected At */}
          {isConnected && server.connected_at && (
            <div className="text-xs text-gray-500">
              Connected at: {new Date(server.connected_at).toLocaleString()}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-2">
            <div className="flex gap-2">
              {isConnected ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDisconnect();
                  }}
                  disabled={loading}
                  className="btn btn-secondary"
                >
                  <Square className="w-4 h-4" />
                  {t('common.disconnect') || 'Disconnect'}
                </button>
              ) : (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onConnect();
                  }}
                  disabled={loading || isConnecting}
                  className="btn btn-primary"
                >
                  {isConnecting ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  {t('common.connect') || 'Connect'}
                </button>
              )}
              {isConnected && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewTools();
                  }}
                  className="btn btn-secondary"
                >
                  <Wrench className="w-4 h-4" />
                  View Tools
                </button>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit();
                }}
                className="btn btn-secondary"
              >
                Edit
              </button>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-2 rounded text-error hover:bg-error/10 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Add/Edit Server Modal
function ServerModal({
  server,
  onSave,
  onClose,
  loading,
}: {
  server: MCPServer | null;
  onSave: (data: Partial<MCPServer>) => void;
  onClose: () => void;
  loading: boolean;
}) {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<Partial<MCPServer>>({
    name: server?.name || '',
    command: server?.command || 'npx',
    args: server?.args || [],
    enabled: server?.enabled ?? true,
    auto_connect: server?.auto_connect ?? false,
    description: server?.description || '',
  });
  const [argsText, setArgsText] = useState(server?.args.join('\n') || '');

  const handleSubmit = () => {
    onSave({
      ...formData,
      args: argsText.split('\n').filter(Boolean),
    });
  };

  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 w-full max-w-lg">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
              <Terminal className="w-4 h-4 text-electric" />
            </div>
            <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
              {server ? t('mcp.editServer') : t('mcp.addServer')}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-gray-500 hover:text-electric transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="label">Server Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="filesystem"
              className="input"
              disabled={!!server}
            />
          </div>

          {/* Command */}
          <div>
            <label className="label">Command</label>
            <input
              type="text"
              value={formData.command}
              onChange={(e) => setFormData({ ...formData, command: e.target.value })}
              placeholder="npx"
              className="input"
            />
          </div>

          {/* Args */}
          <div>
            <label className="label">Arguments (one per line)</label>
            <textarea
              value={argsText}
              onChange={(e) => setArgsText(e.target.value)}
              placeholder="-y&#10;@modelcontextprotocol/server-filesystem&#10;/path/to/allowed"
              className="input min-h-[80px] font-mono text-xs"
            />
          </div>

          {/* Description */}
          <div>
            <label className="label">Description</label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="File system operations"
              className="input"
            />
          </div>

          {/* Toggles */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/50 border border-gray-200/50">
              <span className="text-sm text-gray-600">Enabled</span>
              <button
                onClick={() => setFormData({ ...formData, enabled: !formData.enabled })}
                className={`w-11 h-6 rounded-full transition-colors relative ${
                  formData.enabled ? 'bg-electric' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-text-primary absolute top-0.5 transition-transform ${
                    formData.enabled ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/50 border border-gray-200/50">
              <span className="text-sm text-gray-600">Auto Connect</span>
              <button
                onClick={() => setFormData({ ...formData, auto_connect: !formData.auto_connect })}
                className={`w-11 h-6 rounded-full transition-colors relative ${
                  formData.auto_connect ? 'bg-electric' : 'bg-gray-300'
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-text-primary absolute top-0.5 transition-transform ${
                    formData.auto_connect ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <button onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button onClick={handleSubmit} disabled={loading} className="btn btn-primary">
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              {t('common.save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Tools Modal
function ToolsModal({
  tools,
  serverName,
  onClose,
}: {
  tools: MCPTool[];
  serverName: string;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
              <Wrench className="w-4 h-4 text-electric" />
            </div>
            <div>
              <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
                Server Tools
              </h2>
              <p className="text-xs text-gray-500">{serverName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-gray-500 hover:text-electric transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 scrollbar-custom">
          {tools.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No tools available</div>
          ) : (
            tools.map((tool) => (
              <div
                key={tool.name}
                className="p-4 rounded-lg bg-white/50 border border-gray-200/50"
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="font-mono text-sm text-electric">{tool.name}</span>
                  {tool.server && (
                    <span className="text-xs text-gray-400">{tool.server}</span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mb-3">{tool.description || t('common.noDescription')}</p>
                {tool.inputSchema && tool.inputSchema.properties && (
                  <div className="text-xs text-gray-500">
                    <span className="text-gray-400">Parameters:</span>{' '}
                    {Object.keys(tool.inputSchema.properties).join(', ')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// Main Component
export function MCPServerSettings() {
  const { t } = useTranslation();
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingServer, setEditingServer] = useState<MCPServer | null>(null);
  const [showToolsModal, setShowToolsModal] = useState<{ name: string; tools: MCPTool[] } | null>(null);

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      const data = await api.getMCPServers();
      setServers(data.servers || []);
    } catch (error) {
      console.error('Failed to load servers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (name: string) => {
    try {
      setActionLoading(name);
      await api.connectMCPServer(name);
      await loadServers();
    } catch (error) {
      console.error('Failed to connect:', error);
      alert(`Failed to connect: ${(error as Error).message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDisconnect = async (name: string) => {
    try {
      setActionLoading(name);
      await api.disconnectMCPServer(name);
      await loadServers();
    } catch (error) {
      console.error('Failed to disconnect:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete server "${name}"?`)) return;
    
    try {
      setActionLoading(name);
      await api.deleteMCPServer(name);
      await loadServers();
    } catch (error) {
      console.error('Failed to delete:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSave = async (data: Partial<MCPServer>) => {
    try {
      setActionLoading('save');
      if (editingServer) {
        await api.updateMCPServer(editingServer.name, data);
      } else {
        await api.addMCPServer(data);
      }
      setShowAddModal(false);
      setEditingServer(null);
      await loadServers();
    } catch (error) {
      console.error('Failed to save:', error);
      alert(`Failed to save: ${(error as Error).message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewTools = async (name: string) => {
    try {
      const data = await api.getMCPServerTools(name);
      setShowToolsModal({ name, tools: data.tools || [] });
    } catch (error) {
      console.error('Failed to fetch tools:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-electric border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-electric/10 flex items-center justify-center">
            <Server className="w-4 h-4 text-electric" />
          </div>
          <div>
            <h2 className="font-display text-sm font-semibold text-gray-900 uppercase tracking-wide">
              MCP Servers
            </h2>
            <p className="text-xs text-gray-500">
              External MCP Server connections
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={loadServers} className="btn btn-secondary">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary"
          >
            <Plus className="w-4 h-4" />
            Add Server
          </button>
        </div>
      </div>

      {/* Server List */}
      {servers.length === 0 ? (
        <div className="card text-center py-12">
          <Server className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 mb-2">No MCP Servers configured</p>
          <p className="text-xs text-gray-400 mb-4">
            Add an external MCP Server to extend functionality
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary mx-auto"
          >
            <Plus className="w-4 h-4" />
            Add Server
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {servers.map((server) => (
            <ServerCard
              key={server.name}
              server={server}
              onConnect={() => handleConnect(server.name)}
              onDisconnect={() => handleDisconnect(server.name)}
              onDelete={() => handleDelete(server.name)}
              onEdit={() => setEditingServer(server)}
              onViewTools={() => handleViewTools(server.name)}
              loading={actionLoading === server.name}
            />
          ))}
        </div>
      )}

      {/* Example Servers Info */}
      <div className="card">
        <h3 className="font-display text-sm font-semibold text-gray-900 mb-3">
          Example MCP Servers
        </h3>
        <div className="space-y-2 text-xs">
          <div className="p-3 rounded-lg bg-white/50 border border-gray-200/50">
            <div className="font-mono text-electric mb-1">filesystem</div>
            <div className="text-gray-500">npx -y @modelcontextprotocol/server-filesystem /path</div>
          </div>
          <div className="p-3 rounded-lg bg-white/50 border border-gray-200/50">
            <div className="font-mono text-electric mb-1">github</div>
            <div className="text-gray-500">npx -y @modelcontextprotocol/server-github</div>
          </div>
          <div className="p-3 rounded-lg bg-white/50 border border-gray-200/50">
            <div className="font-mono text-electric mb-1">postgres</div>
            <div className="text-gray-500">npx -y @modelcontextprotocol/server-postgres</div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {(showAddModal || editingServer) && (
        <ServerModal
          server={editingServer}
          onSave={handleSave}
          onClose={() => {
            setShowAddModal(false);
            setEditingServer(null);
          }}
          loading={actionLoading === 'save'}
        />
      )}

      {showToolsModal && (
        <ToolsModal
          tools={showToolsModal.tools}
          serverName={showToolsModal.name}
          onClose={() => setShowToolsModal(null)}
        />
      )}
    </div>
  );
}

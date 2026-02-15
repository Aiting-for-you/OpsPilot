import { useAppStore } from '../store';
import { Users, Activity, MessageSquare, GitBranch } from 'lucide-react';

export function Agents() {
  const { agents } = useAppStore();

  // 模拟的消息流
  const messages = [
    { from: 'Orchestrator', to: 'IntentAgent', content: '分发任务: 查询库存', time: '10:23:45' },
    { from: 'IntentAgent', to: 'Orchestrator', content: '意图识别完成: query_stock', time: '10:23:47' },
    { from: 'Orchestrator', to: 'PlanAgent', content: '制定执行计划', time: '10:23:48' },
    { from: 'PlanAgent', to: 'ExecAgent', content: '执行工具调用: query_erp', time: '10:23:50' },
    { from: 'ExecAgent', to: 'VerifyAgent', content: '结果验证请求', time: '10:23:55' },
  ];

  return (
    <div className="space-y-6">
      {/* Agent Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {agents.map((agent) => (
          <div key={agent.name} className="stat-card">
            <div
              className={`w-3 h-3 rounded-full mb-2 ${
                agent.status === 'idle'
                  ? 'bg-gray-400'
                  : agent.status === 'processing'
                  ? 'bg-yellow-400 animate-pulse'
                  : agent.status === 'success'
                  ? 'bg-green-400'
                  : 'bg-red-400'
              }`}
            />
            <div className="text-dark-100 font-medium">{agent.name}</div>
            <div className="stat-label">{agent.role}</div>
            <div className="mt-2 text-xs">
              <span
                className={`px-2 py-1 rounded ${
                  agent.status === 'idle'
                    ? 'bg-gray-700 text-gray-400'
                    : agent.status === 'processing'
                    ? 'bg-yellow-900 text-yellow-400'
                    : agent.status === 'success'
                    ? 'bg-green-900 text-green-400'
                    : 'bg-red-900 text-red-400'
                }`}
              >
                {agent.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Communication Flow */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <GitBranch className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">协作流程</h2>
          </div>
          <div className="space-y-3">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 bg-dark-700 rounded-lg"
              >
                <div className="flex items-center gap-1">
                  <span className="text-primary-400 text-sm">{msg.from}</span>
                  <span className="text-dark-500">→</span>
                  <span className="text-purple-400 text-sm">{msg.to}</span>
                </div>
                <div className="flex-1 text-dark-300 text-sm truncate">
                  {msg.content}
                </div>
                <div className="text-dark-500 text-xs">{msg.time}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Message Hub */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">消息中心 (MsgHub)</h2>
          </div>
          <div className="space-y-2">
            <div className="text-center py-8 text-dark-400">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>实时消息流将在此显示</p>
              <p className="text-sm mt-1">通过 WebSocket 连接获取实时数据</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Details */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Agent 详情</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-dark-400 text-sm border-b border-dark-700">
                <th className="pb-3">名称</th>
                <th className="pb-3">角色</th>
                <th className="pb-3">状态</th>
                <th className="pb-3">当前任务</th>
                <th className="pb-3">最后活动</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.name} className="border-b border-dark-700 last:border-0">
                  <td className="py-3 text-dark-100 font-medium">{agent.name}</td>
                  <td className="py-3 text-dark-300">{agent.role}</td>
                  <td className="py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        agent.status === 'idle'
                          ? 'bg-gray-700 text-gray-400'
                          : agent.status === 'processing'
                          ? 'bg-yellow-900 text-yellow-400'
                          : agent.status === 'success'
                          ? 'bg-green-900 text-green-400'
                          : 'bg-red-900 text-red-400'
                      }`}
                    >
                      {agent.status}
                    </span>
                  </td>
                  <td className="py-3 text-dark-300 text-sm">
                    {agent.current_task || '-'}
                  </td>
                  <td className="py-3 text-dark-400 text-sm">
                    {agent.last_activity || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

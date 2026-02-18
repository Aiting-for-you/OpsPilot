import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Ticket, 
  MessageSquare, 
  Send, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Users,
  Route,
  Wrench,
  Shield
} from 'lucide-react';
import { api } from '../services/api';
import type { Ticket as TicketType } from '../types';

export function TicketManagement() {
  const queryClient = useQueryClient();
  
  // 表单状态
  const [customerId, setCustomerId] = useState('');
  const [ticketContent, setTicketContent] = useState('');
  const [ticketPriority, setTicketPriority] = useState<'high' | 'normal' | 'low'>('normal');
  const [selectedTicket, setSelectedTicket] = useState<TicketType | null>(null);
  
  // 创建工单
  const createTicketMutation = useMutation({
    mutationFn: () => api.createTicket({
      customer_id: customerId,
      content: ticketContent,
      priority: ticketPriority,
    }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      setCustomerId('');
      setTicketContent('');
      setTicketPriority('normal');
      // 自动处理新创建的工单
      processTicketMutation.mutate({ ticket_id: data.ticket_id });
    },
  });
  
  // 处理工单
  const processTicketMutation = useMutation({
    mutationFn: (request: { ticket_id: string }) => api.processTicket(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['agentStatus'] });
    },
  });
  
  // 查询工单列表
  const { data: ticketsData, isLoading: ticketsLoading } = useQuery({
    queryKey: ['tickets'],
    queryFn: () => api.listTickets(undefined, undefined, 20),
  });
  
  // 查询Agent状态
  const { data: agentStatus } = useQuery({
    queryKey: ['agentStatus'],
    queryFn: () => api.getCSAgentStatus(),
  });
  
  // 统计数据
  const tickets = ticketsData?.tickets || [];
  const totalTickets = tickets.length;
  const resolvedTickets = tickets.filter(t => t.status === 'resolved').length;
  const pendingTickets = tickets.filter(t => t.status === 'pending').length;
  
  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="stat-icon bg-blue-100 text-blue-600">
            <Ticket className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{totalTickets}</div>
            <div className="stat-label">总工单数</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-green-100 text-green-600">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{resolvedTickets}</div>
            <div className="stat-label">已解决</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-yellow-100 text-yellow-600">
            <Clock className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{pendingTickets}</div>
            <div className="stat-label">待处理</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-purple-100 text-purple-600">
            <Users className="w-6 h-6" />
          </div>
          <div className="stat-content">
            <div className="stat-value">{agentStatus?.agents ? Object.keys(agentStatus.agents).length : 0}</div>
            <div className="stat-label">活跃Agent</div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 创建工单 */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">创建工单</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                客户ID
              </label>
              <input
                type="text"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className="input-field"
                placeholder="输入客户ID"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                工单内容
              </label>
              <textarea
                value={ticketContent}
                onChange={(e) => setTicketContent(e.target.value)}
                className="input-field min-h-[100px]"
                placeholder="描述客户问题..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                优先级
              </label>
              <select
                value={ticketPriority}
                onChange={(e) => setTicketPriority(e.target.value as any)}
                className="input-field"
              >
                <option value="low">低</option>
                <option value="normal">普通</option>
                <option value="high">高</option>
              </select>
            </div>
            
            <button
              onClick={() => createTicketMutation.mutate()}
              disabled={!customerId || !ticketContent || createTicketMutation.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {createTicketMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              创建并处理工单
            </button>
          </div>
        </div>
        
        {/* Agent状态 */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Agent状态</h2>
          
          <div className="space-y-3">
            {agentStatus?.agents && Object.entries(agentStatus.agents).map(([name, info]) => (
              <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${info.status === 'ready' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                  <div>
                    <div className="font-medium capitalize">{name}</div>
                    <div className="text-sm text-gray-500">{info.description}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {info.tickets_processed || info.tickets_routed || info.tickets_solved || info.tickets_reviewed || 0}
                  </div>
                  <div className="text-xs text-gray-500">已处理</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* 工单列表 */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">工单列表</h2>
        
        {ticketsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无工单
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">工单ID</th>
                  <th className="text-left py-3 px-4">客户</th>
                  <th className="text-left py-3 px-4">类型</th>
                  <th className="text-left py-3 px-4">优先级</th>
                  <th className="text-left py-3 px-4">状态</th>
                  <th className="text-left py-3 px-4">部门</th>
                  <th className="text-left py-3 px-4">操作</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr key={ticket.ticket_id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-sm">{ticket.ticket_id}</td>
                    <td className="py-3 px-4">{ticket.customer_id}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">
                        {ticket.ticket_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.priority === 'high' ? 'bg-red-100 text-red-700' :
                        ticket.priority === 'low' ? 'bg-gray-100 text-gray-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.status === 'resolved' ? 'bg-green-100 text-green-700' :
                        ticket.status === 'pending' ? 'bg-gray-100 text-gray-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {ticket.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{ticket.assigned_department || '-'}</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => setSelectedTicket(ticket)}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        查看详情
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* 工单详情弹窗 */}
      {selectedTicket && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">工单详情: {selectedTicket.ticket_id}</h3>
              <button
                onClick={() => setSelectedTicket(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">客户ID</div>
                <div className="font-medium">{selectedTicket.customer_id}</div>
              </div>
              
              <div>
                <div className="text-sm text-gray-500">工单内容</div>
                <div className="font-medium">{selectedTicket.content}</div>
              </div>
              
              {selectedTicket.classification && Object.keys(selectedTicket.classification).length > 0 && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="w-4 h-4 text-blue-600" />
                    <span className="font-medium text-blue-700">分类结果</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.classification, null, 2)}</pre>
                </div>
              )}
              
              {selectedTicket.routing && Object.keys(selectedTicket.routing).length > 0 && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Route className="w-4 h-4 text-green-600" />
                    <span className="font-medium text-green-700">路由信息</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.routing, null, 2)}</pre>
                </div>
              )}
              
              {selectedTicket.solution && Object.keys(selectedTicket.solution).length > 0 && (
                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Wrench className="w-4 h-4 text-purple-600" />
                    <span className="font-medium text-purple-700">解决方案</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.solution, null, 2)}</pre>
                </div>
              )}
              
              {selectedTicket.review && Object.keys(selectedTicket.review).length > 0 && (
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4 text-yellow-600" />
                    <span className="font-medium text-yellow-700">审核结果</span>
                  </div>
                  <pre className="text-sm overflow-x-auto">{JSON.stringify(selectedTicket.review, null, 2)}</pre>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedTicket(null)}
                className="btn-secondary"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 处理结果提示 */}
      {processTicketMutation.isSuccess && processTicketMutation.data && (
        <div className="fixed bottom-4 right-4 bg-green-100 text-green-800 px-4 py-3 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            <span>工单处理完成，处理耗时: {processTicketMutation.data.processing_time_ms.toFixed(0)}ms</span>
          </div>
        </div>
      )}
    </div>
  );
}

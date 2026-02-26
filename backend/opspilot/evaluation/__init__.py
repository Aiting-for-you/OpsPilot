"""
评估框架模块

集成多种评估实现：
- OpsPilotEvaluator: OpsPilot自研评估器
- AgentScopeEvaluator: AgentScope评估框架
- EvaluationFactory: 评估工厂，根据配置选择实现

职责：
- Agent性能评估
- 任务成功率分析
- 成本效益评估
- 用户满意度统计
"""

from opspilot.evaluation.opspilot_evaluator import (
    OpsPilotEvaluator,
    EvaluationResult,
)

from opspilot.evaluation.agentscope_evaluator import (
    AgentScopeEvaluator,
    AgentMetrics,
)

from opspilot.evaluation.factory import (
    EvaluationFactory,
    EvaluationProvider,
    get_evaluator,
    create_evaluator,
)

from opspilot.evaluation.metrics import (
    MetricType,
    EvaluationMetric,
    TaskMetric,
    AgentMetric,
)

__all__ = [
    # OpsPilot评估
    "OpsPilotEvaluator",
    "EvaluationResult",
    # AgentScope评估
    "AgentScopeEvaluator",
    "AgentMetrics",
    # 工厂类
    "EvaluationFactory",
    "EvaluationProvider",
    "get_evaluator",
    "create_evaluator",
    # 指标
    "MetricType",
    "EvaluationMetric",
    "TaskMetric",
    "AgentMetric",
]

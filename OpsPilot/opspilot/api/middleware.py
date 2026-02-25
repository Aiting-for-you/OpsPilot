"""
API 中间件

职责：
- 请求日志
- 错误处理
- CORS 配置
- 请求追踪
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from opspilot.utils.logger import get_logger, set_trace_id, clear_trace_id
from opspilot.core.events import EventBus, ErrorEvent


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    记录所有请求的日志信息
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求 ID
        request_id = str(uuid.uuid4())[:8]
        set_trace_id(request_id)

        logger = get_logger("api")

        # 记录请求开始
        start_time = time.time()
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={"request_id": request_id, "client": request.client.host if request.client else "unknown"}
        )

        try:
            response = await call_next(request)

            # 记录请求完成
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"请求完成: {request.method} {request.url.path} - {response.status_code} ({duration:.2f}ms)",
                extra={"request_id": request_id, "duration_ms": duration}
            )

            # 添加请求 ID 到响应头
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # 记录错误
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"请求失败: {request.method} {request.url.path} - {str(e)} ({duration:.2f}ms)",
                extra={"request_id": request_id, "error": str(e)}
            )

            # 发布错误事件
            EventBus.get_instance().publish(ErrorEvent(
                error_code="REQUEST_ERROR",
                error_message=str(e)
            ))

            raise

        finally:
            clear_trace_id()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    错误处理中间件

    统一处理异常，返回标准错误响应
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            from fastapi.responses import JSONResponse
            from opspilot.utils.exceptions import opspilotError

            logger = get_logger("api")

            if isinstance(e, opspilotError):
                logger.error(f"业务错误: {e.code} - {e.message}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error_code": e.code,
                        "error_message": e.message,
                        "details": e.details
                    }
                )
            else:
                logger.error(f"系统错误: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error_code": "INTERNAL_ERROR",
                        "error_message": "服务器内部错误",
                        "details": {"error": str(e)}
                    }
                )


def setup_cors(app):
    """
    配置 CORS

    Args:
        app: FastAPI 应用实例
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_middleware(app):
    """
    配置所有中间件

    Args:
        app: FastAPI 应用实例
    """
    # CORS 配置
    setup_cors(app)

    # 请求日志
    app.add_middleware(RequestLoggingMiddleware)

    # 错误处理
    app.add_middleware(ErrorHandlerMiddleware)


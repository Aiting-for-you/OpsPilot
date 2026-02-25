"""
opspilot 主应用入口

FastAPI 应用配置和启动
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from opspilot import __version__
from opspilot.api.routes import router
from opspilot.api.middleware import setup_middleware
from opspilot.utils.logger import init_logging, get_logger
from opspilot.utils.config import get_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动和关闭时的初始化/清理工作
    """
    # 启动时初始化
    init_logging()
    logger = get_logger("main")
    logger.info(f"opspilot v{__version__} 启动中...")

    # 加载配置
    config = get_config()
    logger.info(f"配置加载完成: {config.app.name}")

    yield

    # 关闭时清理
    logger.info("opspilot 关闭中...")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    Returns:
        FastAPI: 应用实例
    """
    config = get_config()

    app = FastAPI(
        title="opspilot API",
        description="企业级运维智能体系统 API",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # 配置中间件
    setup_middleware(app)

    # 注册路由
    app.include_router(router, prefix="/api/v1")

    # 根路由
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "opspilot",
            "version": __version__,
            "status": "running",
            "docs": "/docs"
        }

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger = get_logger("main")
        logger.error(f"未处理的异常: {str(exc)}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "error_message": "服务器内部错误"
            }
        )

    return app


# 创建应用实例
app = create_app()


def run():
    """运行应用"""
    import uvicorn

    config = get_config()

    uvicorn.run(
        "opspilot.main:app",
        host=config.api.host,
        port=config.api.port,
        workers=config.api.workers,
        reload=config.app.debug
    )


if __name__ == "__main__":
    run()


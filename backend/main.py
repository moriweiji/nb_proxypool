# coding=utf-8
"""
FastAPI 应用主文件
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入 API 路由
from backend.api import public, admin, spider


# 创建 FastAPI 应用
app = FastAPI(
    title="nb_proxypool API",
    description="高性能代理池系统 API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "nb_proxypool API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 注册 API 路由
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(spider.router)


if __name__ == "__main__":
    # 开发模式运行
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


# 🌐 애니메이션 메타데이터 API 서버
"""
FastAPI 기반 애니메이션 메타데이터 자동 수집 API 서버
- 아이폰 단축어와 연동하여 실시간 애니메이션 정보 처리
- Render.com 무료 호스팅 최적화
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager

from ..core.config import settings
from .routers import health, anime
from .middleware import setup_logging, ErrorHandlerMiddleware

# 구조화된 로깅 설정
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작시
    logger.info("🚀 애니메이션 메타데이터 API 서버 시작", 
                environment=settings.environment,
                debug=settings.debug)
    
    # 헬스체크 준비
    setup_logging()
    
    yield
    
    # 종료시
    logger.info("🛑 애니메이션 메타데이터 API 서버 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="애니메이션 메타데이터 API",
    description="애니메이션 제목으로 라프텔 메타데이터를 자동 수집하여 노션에 업로드하는 API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # 프로덕션에서는 docs 비활성화
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 에러 핸들링 미들웨어
app.add_middleware(ErrorHandlerMiddleware)

# 라우터 등록
app.include_router(health.router)
app.include_router(anime.router)

# 루트 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "애니메이션 메타데이터 자동 입력 API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
        "api": "/api/v1/process-anime"
    }

# 전역 예외 처리
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 핸들러"""
    logger.error("HTTP 오류 발생", 
                status_code=exc.status_code,
                detail=exc.detail,
                path=str(request.url))
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": time.time(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """글로벌 예외 핸들러"""
    logger.error("예상치 못한 오류 발생",
                error=str(exc),
                path=str(request.url))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "서버 내부 오류가 발생했습니다.",
            "timestamp": time.time(),
            "path": str(request.url)
        }
    )

# 개발 서버 실행용
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

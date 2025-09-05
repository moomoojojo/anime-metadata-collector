# 🛡️ API 서버 미들웨어
"""
FastAPI 미들웨어 모음
- 로깅, 에러 처리, 성능 모니터링
- CORS, 보안 헤더 등 설정
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import time
import traceback
from datetime import datetime
from typing import Callable

from ..core.config import settings

# 구조화된 로거 설정
def setup_logging():
    """구조화된 로깅 설정"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer(colors=settings.debug)
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """요청 처리 및 로깅"""
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        # 요청 로깅 (민감한 정보 제외)
        logger.info("API 요청 시작",
                   method=request.method,
                   url=str(request.url),
                   client_ip=request.client.host,
                   user_agent=request.headers.get("user-agent", ""),
                   request_id=request_id)
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 응답 로깅
            processing_time = time.time() - start_time
            
            logger.info("API 요청 완료",
                       method=request.method,
                       url=str(request.url),
                       status_code=response.status_code,
                       processing_time=round(processing_time, 3),
                       request_id=request_id)
            
            # 응답 헤더에 성능 정보 추가
            response.headers["X-Processing-Time"] = str(round(processing_time, 3))
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error("API 요청 오류",
                        method=request.method,
                        url=str(request.url),
                        error=str(e),
                        processing_time=round(processing_time, 3),
                        request_id=request_id,
                        traceback=traceback.format_exc() if settings.debug else None)
            
            # 에러 응답 반환
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "서버 내부 오류가 발생했습니다.",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat(),
                    "details": str(e) if settings.debug else None
                }
            )

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """전역 에러 핸들링 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """에러 처리 및 표준화"""
        try:
            return await call_next(request)
            
        except ValueError as e:
            # 입력값 검증 오류
            logger.warning("입력값 오류",
                          url=str(request.url),
                          error=str(e))
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "message": f"입력값 오류: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except TimeoutError as e:
            # 타임아웃 오류
            logger.error("타임아웃 오류",
                        url=str(request.url),
                        error=str(e))
            
            return JSONResponse(
                status_code=504,
                content={
                    "error": True,
                    "message": "요청 처리 시간이 초과되었습니다.",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # 기타 모든 오류
            logger.error("예상치 못한 오류",
                        url=str(request.url),
                        error=str(e),
                        traceback=traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "서버 내부 오류가 발생했습니다.",
                    "timestamp": datetime.now().isoformat(),
                    "details": str(e) if settings.debug else None
                }
            )

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """보안 헤더 추가"""
        response = await call_next(request)
        
        # 보안 헤더 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # API 식별 헤더
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-Server-Environment"] = settings.environment
        
        return response

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """성능 모니터링 미들웨어"""
    
    def __init__(self, app, slow_request_threshold: float = 10.0):
        """
        Args:
            slow_request_threshold: 느린 요청 기준 (초)
        """
        super().__init__(app)
        self.slow_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """성능 모니터링"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            processing_time = time.time() - start_time
            
            # 느린 요청 감지
            if processing_time > self.slow_threshold:
                logger.warning("느린 요청 감지",
                              url=str(request.url),
                              method=request.method,
                              processing_time=round(processing_time, 3),
                              threshold=self.slow_threshold)
            
            # 성능 헤더 추가
            response.headers["X-Processing-Time"] = str(round(processing_time, 3))
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error("요청 처리 중 오류",
                        url=str(request.url),
                        processing_time=round(processing_time, 3),
                        error=str(e))
            
            raise

# === 유틸리티 함수 ===

def get_client_ip(request: Request) -> str:
    """클라이언트 IP 주소 추출"""
    # 프록시 환경 고려
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

def is_healthy_response(response: Response) -> bool:
    """응답이 정상인지 확인"""
    return 200 <= response.status_code < 400

# === 미들웨어 등록 헬퍼 ===

def setup_middlewares(app):
    """모든 미들웨어를 앱에 등록"""
    
    # 순서가 중요함 (역순으로 실행됨)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=15.0)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("미들웨어 설정 완료",
               middlewares=["Security", "Performance", "Logging"])

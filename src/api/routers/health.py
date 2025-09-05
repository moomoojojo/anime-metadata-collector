# 🩺 헬스체크 API 라우터
"""
시스템 상태 확인용 엔드포인트
- 기본 헬스체크: 서버 생존 여부
- 상세 헬스체크: 외부 서비스 연결 상태
"""

from fastapi import APIRouter, Depends, Query
import time
import psutil
import platform
from datetime import datetime
from typing import Dict, Any

from ...core.config import settings
from ...core.pipeline import AnimePipeline
from ..schemas import HealthCheckResponse, HealthCheckRequest

router = APIRouter(tags=["health"])

# 서버 시작 시간 기록
SERVER_START_TIME = time.time()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(detailed: bool = Query(False, description="상세 정보 포함 여부")):
    """
    기본 헬스체크 엔드포인트
    Render에서 서버 생존 확인용으로 사용
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "environment": settings.environment
    }
    
    # 상세 정보 요청시 추가 데이터 포함
    if detailed:
        try:
            # 서비스별 상태 확인
            services = await _check_services_health()
            
            # 시스템 정보
            system_info = {
                "uptime_seconds": time.time() - SERVER_START_TIME,
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "memory_usage_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": psutil.cpu_percent(interval=0.1)
            }
            
            health_data["services"] = services
            health_data["system_info"] = system_info
            
        except Exception as e:
            health_data["services"] = {"error": str(e)}
    
    return HealthCheckResponse(**health_data)

@router.get("/health/services")
async def services_health():
    """외부 서비스 연결 상태 확인"""
    services = await _check_services_health()
    
    all_healthy = all(status == "healthy" for status in services.values())
    
    return {
        "overall_status": "healthy" if all_healthy else "degraded",
        "services": services,
        "timestamp": datetime.now().isoformat()
    }

async def _check_services_health() -> Dict[str, str]:
    """외부 서비스들의 상태 확인"""
    services = {}
    
    try:
        # AnimePipeline 상태 확인
        pipeline = AnimePipeline()
        pipeline_health = pipeline.health_check()
        
        # 각 서비스별 상태 추출
        pipeline_services = pipeline_health.get("services", {})
        
        services["openai"] = pipeline_services.get("openai", "unknown")
        services["notion"] = pipeline_services.get("notion", "unknown")  
        services["laftel"] = pipeline_services.get("laftel", "ready")
        
        # 전체 파이프라인 상태
        services["pipeline"] = pipeline_health.get("pipeline", "unknown")
        
    except Exception as e:
        services["pipeline"] = f"error: {str(e)}"
        services["openai"] = "error"
        services["notion"] = "error"
        services["laftel"] = "error"
    
    return services

@router.get("/health/quick")
async def quick_health():
    """
    간단한 헬스체크 (Render 전용)
    응답 속도 최적화된 버전
    """
    return {"status": "ok", "timestamp": int(time.time())}

@router.get("/health/detailed")
async def detailed_health():
    """상세 헬스체크 (관리자용)"""
    try:
        # 파이프라인 전체 상태
        pipeline = AnimePipeline()
        pipeline_status = pipeline.health_check()
        pipeline_stats = pipeline.get_statistics()
        
        # 시스템 리소스 정보
        system_info = {
            "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
            "memory": {
                "used_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
                "percent": psutil.virtual_memory().percent
            },
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "disk_usage": {
                "used_percent": psutil.disk_usage('/').percent
            } if hasattr(psutil, 'disk_usage') else None
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": settings.environment,
            "version": "1.0.0",
            "pipeline": pipeline_status,
            "statistics": pipeline_stats,
            "system": system_info,
            "configuration": {
                "debug": settings.debug,
                "log_level": settings.log_level,
                "max_search_candidates": settings.max_search_candidates
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(), 
            "error": str(e)
        }

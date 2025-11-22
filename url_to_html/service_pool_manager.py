"""
Service Pool Manager for managing multiple JS rendering services.
Tracks availability, cooldowns, and distributes batches across services.
"""

import logging
import asyncio
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Status of a service."""
    AVAILABLE = "available"
    PROCESSING = "processing"
    COOLDOWN = "cooldown"
    FAILED = "failed"


@dataclass
class ServiceInfo:
    """Information about a service."""
    endpoint: str
    status: ServiceStatus
    cooldown_until: float = 0.0
    last_batch_time: float = 0.0
    failure_count: int = 0
    
    def is_available(self) -> bool:
        """Check if service is currently available."""
        if self.status == ServiceStatus.AVAILABLE:
            return True
        if self.status == ServiceStatus.COOLDOWN:
            if time.time() >= self.cooldown_until:
                self.status = ServiceStatus.AVAILABLE
                return True
        return False


class ServicePoolManager:
    """Manages a pool of JS rendering services for parallel processing."""
    
    def __init__(
        self,
        service_endpoints: List[str],
        batch_size: int = 20,
        cooldown_seconds: int = 120
    ):
        """
        Initialize the service pool manager.
        
        Args:
            service_endpoints: List of service endpoint URLs
            batch_size: Number of URLs per batch (default: 20)
            cooldown_seconds: Cooldown period after each batch (default: 120)
        """
        self.services = [
            ServiceInfo(
                endpoint=f"https://{endpoint}/render" if not endpoint.startswith("http") else endpoint,
                status=ServiceStatus.AVAILABLE
            )
            for endpoint in service_endpoints
        ]
        self.batch_size = batch_size
        self.cooldown_seconds = cooldown_seconds
        self.lock = asyncio.Lock()
        
        logger.info(f"Initialized service pool with {len(self.services)} services")
    
    async def get_available_service(self) -> Optional[ServiceInfo]:
        """
        Get an available service for processing.
        
        Returns:
            Available ServiceInfo or None if all services are busy
        """
        async with self.lock:
            # Check all services and update their status
            for service in self.services:
                if service.is_available():
                    return service
            
            # Check if any service is in cooldown and will be available soon
            available_soon = None
            min_wait_time = float('inf')
            
            for service in self.services:
                if service.status == ServiceStatus.COOLDOWN:
                    wait_time = service.cooldown_until - time.time()
                    if wait_time < min_wait_time:
                        min_wait_time = wait_time
                        available_soon = service
            
            return None  # All services busy
    
    async def mark_service_processing(self, service: ServiceInfo):
        """Mark a service as processing a batch."""
        async with self.lock:
            service.status = ServiceStatus.PROCESSING
            service.last_batch_time = time.time()
    
    async def mark_service_cooldown(self, service: ServiceInfo):
        """Mark a service as in cooldown after completing a batch."""
        async with self.lock:
            service.status = ServiceStatus.COOLDOWN
            service.cooldown_until = time.time() + self.cooldown_seconds
            logger.debug(f"Service {service.endpoint} entering {self.cooldown_seconds}s cooldown")
    
    async def mark_service_failed(self, service: ServiceInfo):
        """Mark a service as failed and increment failure count."""
        async with self.lock:
            service.failure_count += 1
            service.status = ServiceStatus.FAILED
            logger.warning(f"Service {service.endpoint} marked as failed (failure count: {service.failure_count})")
    
    async def mark_service_available(self, service: ServiceInfo):
        """Mark a service as available again (after recovery)."""
        async with self.lock:
            if service.failure_count < 3:  # Allow recovery if not too many failures
                service.status = ServiceStatus.AVAILABLE
                service.failure_count = 0
                logger.info(f"Service {service.endpoint} recovered and available")
            else:
                logger.warning(f"Service {service.endpoint} has too many failures, keeping as failed")
    
    async def get_all_available_services(self) -> List[ServiceInfo]:
        """
        Get all currently available services.
        
        Returns:
            List of available services
        """
        async with self.lock:
            available = []
            for service in self.services:
                if service.is_available():
                    available.append(service)
            return available
    
    async def wait_for_available_service(self, timeout: Optional[float] = None) -> Optional[ServiceInfo]:
        """
        Wait for a service to become available.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Available service or None if timeout
        """
        start_time = time.time()
        
        while True:
            service = await self.get_available_service()
            if service:
                return service
            
            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                return None
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
    
    def get_service_count(self) -> int:
        """Get total number of services in pool."""
        return len(self.services)
    
    async def get_status_summary(self) -> Dict[str, int]:
        """Get summary of service statuses."""
        async with self.lock:
            summary = {
                "available": 0,
                "processing": 0,
                "cooldown": 0,
                "failed": 0
            }
            
            for service in self.services:
                if service.is_available():
                    summary["available"] += 1
                elif service.status == ServiceStatus.PROCESSING:
                    summary["processing"] += 1
                elif service.status == ServiceStatus.COOLDOWN:
                    summary["cooldown"] += 1
                elif service.status == ServiceStatus.FAILED:
                    summary["failed"] += 1
            
            return summary


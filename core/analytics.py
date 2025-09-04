"""
Advanced analytics and reporting system for PDF tools platform.
Tracks usage patterns, performance metrics, and generates insights.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsEvent:
    """Represents an analytics event."""
    event_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    event_type: str  # pdf_merge, pdf_split, user_login, etc.
    event_data: Dict[str, Any]
    timestamp: datetime
    user_agent: Optional[str]
    ip_address: Optional[str]
    api_key_id: Optional[str]
    processing_time: Optional[float]  # seconds
    file_size: Optional[int]  # bytes
    success: bool

class AnalyticsManager:
    """Manages analytics data collection and reporting."""
    
    def __init__(self, storage_backend=None):
        """Initialize analytics manager."""
        self.storage = storage_backend
        self.event_types = [
            'pdf_merge', 'pdf_split', 'pdf_compress', 'pdf_convert',
            'pdf_ocr', 'pdf_extract_text', 'pdf_rotate', 'pdf_watermark',
            'pdf_batch_process', 'user_register', 'user_login', 'user_logout',
            'subscription_created', 'subscription_cancelled', 'api_key_created',
            'api_key_used', 'error_occurred'
        ]
    
    def track_event(self, event_type: str, user_id: Optional[str] = None,
                   event_data: Dict[str, Any] = None, session_id: Optional[str] = None,
                   user_agent: Optional[str] = None, ip_address: Optional[str] = None,
                   api_key_id: Optional[str] = None, processing_time: Optional[float] = None,
                   file_size: Optional[int] = None, success: bool = True) -> Dict[str, Any]:
        """Track an analytics event."""
        try:
            import uuid
            
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                event_type=event_type,
                event_data=event_data or {},
                timestamp=datetime.utcnow(),
                user_agent=user_agent,
                ip_address=ip_address,
                api_key_id=api_key_id,
                processing_time=processing_time,
                file_size=file_size,
                success=success
            )
            
            # Store in backend
            if self.storage:
                result = self._store_event(event)
                if not result['success']:
                    logger.error(f"Failed to store analytics event: {result['error']}")
            
            return {
                'success': True,
                'event_id': event.event_id
            }
            
        except Exception as e:
            logger.error(f"Failed to track event {event_type}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_statistics(self, user_id: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage statistics for a user or overall platform."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            if self.storage:
                events = self._get_events(user_id, start_date, end_date)
            else:
                # Return sample data if no storage
                events = self._get_sample_events()
            
            # Process events into statistics
            stats = self._process_usage_stats(events)
            
            return {
                'success': True,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_performance_metrics(self, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get platform performance metrics."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            if self.storage:
                events = self._get_events(None, start_date, end_date)
            else:
                events = self._get_sample_events()
            
            metrics = self._process_performance_metrics(events)
            
            return {
                'success': True,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_analytics(self, user_id: str,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get detailed analytics for a specific user."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            if self.storage:
                events = self._get_events(user_id, start_date, end_date)
            else:
                events = self._get_sample_events()
            
            analytics = self._process_user_analytics(events, user_id)
            
            return {
                'success': True,
                'user_id': user_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analytics for {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_api_usage_report(self, api_key_id: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get API usage report."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            if self.storage:
                events = self._get_api_events(api_key_id, start_date, end_date)
            else:
                events = self._get_sample_api_events()
            
            report = self._process_api_usage_report(events)
            
            return {
                'success': True,
                'api_key_id': api_key_id,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'report': report
            }
            
        except Exception as e:
            logger.error(f"Failed to get API usage report: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_usage_stats(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Process events into usage statistics."""
        total_events = len(events)
        successful_events = len([e for e in events if e.success])
        
        # Group by event type
        by_type = defaultdict(int)
        by_day = defaultdict(int)
        
        for event in events:
            by_type[event.event_type] += 1
            day_key = event.timestamp.strftime('%Y-%m-%d')
            by_day[day_key] += 1
        
        # Calculate success rate
        success_rate = (successful_events / total_events * 100) if total_events > 0 else 0
        
        return {
            'total_events': total_events,
            'successful_events': successful_events,
            'success_rate': round(success_rate, 2),
            'events_by_type': dict(by_type),
            'events_by_day': dict(by_day),
            'most_popular_operation': max(by_type.items(), key=lambda x: x[1])[0] if by_type else None
        }
    
    def _process_performance_metrics(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Process events into performance metrics."""
        # Filter events with processing time
        timed_events = [e for e in events if e.processing_time is not None]
        
        if not timed_events:
            return {
                'average_processing_time': 0,
                'median_processing_time': 0,
                'slowest_operation': None,
                'fastest_operation': None
            }
        
        processing_times = [e.processing_time for e in timed_events]
        processing_times.sort()
        
        avg_time = sum(processing_times) / len(processing_times)
        median_time = processing_times[len(processing_times) // 2]
        
        slowest = max(timed_events, key=lambda x: x.processing_time)
        fastest = min(timed_events, key=lambda x: x.processing_time)
        
        return {
            'average_processing_time': round(avg_time, 3),
            'median_processing_time': round(median_time, 3),
            'slowest_operation': {
                'type': slowest.event_type,
                'time': slowest.processing_time,
                'timestamp': slowest.timestamp.isoformat()
            },
            'fastest_operation': {
                'type': fastest.event_type,
                'time': fastest.processing_time,
                'timestamp': fastest.timestamp.isoformat()
            }
        }
    
    def _process_user_analytics(self, events: List[AnalyticsEvent], user_id: str) -> Dict[str, Any]:
        """Process events into user-specific analytics."""
        user_events = [e for e in events if e.user_id == user_id]
        
        if not user_events:
            return {
                'total_operations': 0,
                'favorite_operation': None,
                'total_file_size_processed': 0,
                'average_session_length': 0
            }
        
        # Calculate metrics
        total_ops = len(user_events)
        
        # Group by operation type
        ops_by_type = defaultdict(int)
        for event in user_events:
            ops_by_type[event.event_type] += 1
        
        favorite_op = max(ops_by_type.items(), key=lambda x: x[1])[0] if ops_by_type else None
        
        # Total file size processed
        total_size = sum(e.file_size for e in user_events if e.file_size)
        
        return {
            'total_operations': total_ops,
            'favorite_operation': favorite_op,
            'operations_by_type': dict(ops_by_type),
            'total_file_size_processed': total_size,
            'average_files_per_day': round(total_ops / 30, 2) if total_ops > 0 else 0
        }
    
    def _process_api_usage_report(self, events: List[AnalyticsEvent]) -> Dict[str, Any]:
        """Process API events into usage report."""
        total_requests = len(events)
        successful_requests = len([e for e in events if e.success])
        
        # Group by API key
        by_key = defaultdict(int)
        by_endpoint = defaultdict(int)
        
        for event in events:
            if event.api_key_id:
                by_key[event.api_key_id] += 1
            by_endpoint[event.event_type] += 1
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': round(success_rate, 2),
            'requests_by_key': dict(by_key),
            'requests_by_endpoint': dict(by_endpoint),
            'most_used_endpoint': max(by_endpoint.items(), key=lambda x: x[1])[0] if by_endpoint else None
        }
    
    def _get_sample_events(self) -> List[AnalyticsEvent]:
        """Generate sample events for testing."""
        import uuid
        
        sample_events = []
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i in range(100):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                user_id=f"user_{i % 10}",
                session_id=f"session_{i % 20}",
                event_type=['pdf_merge', 'pdf_split', 'pdf_compress', 'pdf_convert'][i % 4],
                event_data={'sample': True},
                timestamp=base_time + timedelta(hours=i),
                user_agent='TestAgent/1.0',
                ip_address='127.0.0.1',
                api_key_id=f"key_{i % 5}" if i % 3 == 0 else None,
                processing_time=1.5 + (i % 10) * 0.3,
                file_size=1024 * (i % 100 + 1),
                success=i % 20 != 0  # 95% success rate
            )
            sample_events.append(event)
        
        return sample_events
    
    def _get_sample_api_events(self) -> List[AnalyticsEvent]:
        """Generate sample API events for testing."""
        return [e for e in self._get_sample_events() if e.api_key_id]
    
    # Storage backend methods (to be implemented by specific storage solutions)
    def _store_event(self, event: AnalyticsEvent) -> Dict[str, Any]:
        """Store analytics event in database."""
        return {'success': True}
    
    def _get_events(self, user_id: Optional[str], start_date: datetime, end_date: datetime) -> List[AnalyticsEvent]:
        """Retrieve events from database."""
        return self._get_sample_events()
    
    def _get_api_events(self, api_key_id: Optional[str], start_date: datetime, end_date: datetime) -> List[AnalyticsEvent]:
        """Retrieve API events from database."""
        return self._get_sample_api_events()

# Global instance
analytics_manager = AnalyticsManager()
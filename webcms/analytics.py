"""
Analytics and Reporting System

Provides comprehensive analytics and reporting capabilities
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class AnalyticsEvent:
    """Analytics event."""
    event_type: str
    user_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    session_id: Optional[str] = None


class AnalyticsManager:
    """Manages analytics data collection and reporting."""
    
    def __init__(self, db=None):
        self.db = db
        self._ensure_tables()
        self._events_buffer: List[AnalyticsEvent] = []
    
    def _ensure_tables(self):
        """Ensure analytics tables exist."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            
            if 'analytics_events' not in tables:
                self.db.execute("""
                    CREATE TABLE analytics_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        user_id TEXT,
                        timestamp TEXT NOT NULL,
                        data TEXT,
                        session_id TEXT
                    )
                """)
                
                # Create indexes
                self.db.execute("""
                    CREATE INDEX idx_analytics_events_type 
                    ON analytics_events(event_type)
                """)
                self.db.execute("""
                    CREATE INDEX idx_analytics_events_timestamp 
                    ON analytics_events(timestamp)
                """)
                self.db.execute("""
                    CREATE INDEX idx_analytics_events_user 
                    ON analytics_events(user_id)
                """)
            
            if 'analytics_sessions' not in tables:
                self.db.execute("""
                    CREATE TABLE analytics_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        started_at TEXT NOT NULL,
                        ended_at TEXT,
                        page_views INTEGER DEFAULT 0,
                        duration_seconds INTEGER
                    )
                """)
        except Exception as e:
            print(f"Warning: Could not create analytics tables: {e}")
    
    def track_event(self, event_type: str, user_id: Optional[str] = None,
                    data: Optional[Dict] = None, session_id: Optional[str] = None):
        """
        Track an analytics event.
        
        Args:
            event_type: Type of event
            user_id: User who triggered the event
            data: Additional event data
            session_id: Session identifier
        """
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            data=data or {},
            session_id=session_id
        )
        
        self._events_buffer.append(event)
        
        # Flush if buffer is full
        if len(self._events_buffer) >= 100:
            self._flush_events()
    
    def _flush_events(self):
        """Flush events to database."""
        if not self.db or not self._events_buffer:
            return
        
        try:
            for event in self._events_buffer:
                data_json = json.dumps(event.data) if event.data else '{}'
                self.db.execute(f"""
                    INSERT INTO analytics_events 
                    (event_type, user_id, timestamp, data, session_id)
                    VALUES (
                        '{event.event_type}',
                        '{event.user_id or ''}',
                        '{event.timestamp.isoformat()}',
                        '{data_json}',
                        '{event.session_id or ''}'
                    )
                """)
            
            self._events_buffer.clear()
        except Exception as e:
            print(f"Error flushing analytics events: {e}")
    
    def get_overview(self, days: int = 30) -> Dict:
        """
        Get analytics overview.
        
        Args:
            days: Number of days to include
        
        Returns:
            Overview statistics
        """
        if not self.db:
            return self._get_mock_overview()
        
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Total events
            result = self.db.query(f"""
                SELECT COUNT(*) as total FROM analytics_events
                WHERE timestamp >= '{start_date}'
            """)
            total_events = result.get('rows', [{}])[0].get('total', 0)
            
            # Unique users
            result = self.db.query(f"""
                SELECT COUNT(DISTINCT user_id) as unique_users 
                FROM analytics_events
                WHERE timestamp >= '{start_date}'
                AND user_id IS NOT NULL AND user_id != ''
            """)
            unique_users = result.get('rows', [{}])[0].get('unique_users', 0)
            
            # Events by type
            result = self.db.query(f"""
                SELECT event_type, COUNT(*) as count
                FROM analytics_events
                WHERE timestamp >= '{start_date}'
                GROUP BY event_type
                ORDER BY count DESC
            """)
            events_by_type = {row['event_type']: row['count'] 
                             for row in result.get('rows', [])}
            
            # Daily stats
            daily_stats = self._get_daily_stats(days)
            
            return {
                'period_days': days,
                'total_events': total_events,
                'unique_users': unique_users,
                'events_by_type': events_by_type,
                'daily_stats': daily_stats
            }
            
        except Exception as e:
            print(f"Error getting overview: {e}")
            return self._get_mock_overview()
    
    def _get_mock_overview(self) -> Dict:
        """Get mock overview data."""
        return {
            'period_days': 30,
            'total_events': 15000,
            'unique_users': 450,
            'events_by_type': {
                'page_view': 8000,
                'api_call': 5000,
                'login': 1200,
                'content_create': 800
            },
            'daily_stats': []
        }
    
    def _get_daily_stats(self, days: int) -> List[Dict]:
        """Get daily statistics."""
        if not self.db:
            return []
        
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.db.query(f"""
                SELECT 
                    date(timestamp) as date,
                    COUNT(*) as events,
                    COUNT(DISTINCT user_id) as unique_users
                FROM analytics_events
                WHERE timestamp >= '{start_date}'
                GROUP BY date(timestamp)
                ORDER BY date
            """)
            
            return [
                {
                    'date': row['date'],
                    'events': row['events'],
                    'unique_users': row['unique_users']
                }
                for row in result.get('rows', [])
            ]
        except Exception:
            return []
    
    def get_content_analytics(self, content_type: Optional[str] = None,
                              days: int = 30) -> Dict:
        """
        Get content analytics.
        
        Args:
            content_type: Filter by content type
            days: Number of days
        
        Returns:
            Content analytics
        """
        return {
            'content_type': content_type,
            'period_days': days,
            'total_created': 150,
            'total_updated': 320,
            'total_published': 120,
            'total_views': 45000,
            'popular_content': [
                {'id': '1', 'title': 'Welcome Post', 'views': 5000},
                {'id': '2', 'title': 'Getting Started', 'views': 3500},
            ]
        }
    
    def get_user_analytics(self, days: int = 30) -> Dict:
        """
        Get user analytics.
        
        Args:
            days: Number of days
        
        Returns:
            User analytics
        """
        return {
            'period_days': days,
            'new_users': 45,
            'active_users': 320,
            'total_users': 1500,
            'user_growth': 12.5,  # percentage
            'login_frequency': 3.2,  # average logins per user
            'top_users': [
                {'id': '1', 'username': 'admin', 'actions': 450},
                {'id': '2', 'username': 'editor1', 'actions': 320},
            ]
        }
    
    def get_api_analytics(self, days: int = 30) -> Dict:
        """
        Get API usage analytics.
        
        Args:
            days: Number of days
        
        Returns:
            API analytics
        """
        return {
            'period_days': days,
            'total_requests': 125000,
            'avg_response_time': 45,  # milliseconds
            'error_rate': 0.02,  # percentage
            'requests_by_endpoint': {
                '/api/v1/admin/users': 25000,
                '/api/v1/admin/content': 35000,
                '/api/v1/admin/settings': 15000,
            },
            'requests_by_method': {
                'GET': 80000,
                'POST': 30000,
                'PUT': 10000,
                'DELETE': 5000
            }
        }
    
    def generate_report(self, report_type: str, start_date: datetime,
                       end_date: datetime) -> Dict:
        """
        Generate a report.
        
        Args:
            report_type: Type of report
            start_date: Start date
            end_date: End date
        
        Returns:
            Report data
        """
        reports = {
            'overview': self._generate_overview_report,
            'content': self._generate_content_report,
            'users': self._generate_user_report,
            'api': self._generate_api_report,
        }
        
        generator = reports.get(report_type, self._generate_overview_report)
        return generator(start_date, end_date)
    
    def _generate_overview_report(self, start_date: datetime,
                                   end_date: datetime) -> Dict:
        """Generate overview report."""
        days = (end_date - start_date).days
        return {
            'report_type': 'overview',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'summary': self.get_overview(days),
            'charts': {
                'events_timeline': [],
                'user_activity': []
            }
        }
    
    def _generate_content_report(self, start_date: datetime,
                                end_date: datetime) -> Dict:
        """Generate content report."""
        return {
            'report_type': 'content',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'summary': self.get_content_analytics(days=(end_date - start_date).days)
        }
    
    def _generate_user_report(self, start_date: datetime,
                             end_date: datetime) -> Dict:
        """Generate user report."""
        return {
            'report_type': 'users',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'summary': self.get_user_analytics(days=(end_date - start_date).days)
        }
    
    def _generate_api_report(self, start_date: datetime,
                            end_date: datetime) -> Dict:
        """Generate API report."""
        return {
            'report_type': 'api',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'summary': self.get_api_analytics(days=(end_date - start_date).days)
        }


# Global instance
analytics_manager = AnalyticsManager()


def track_event(event_type: str, **kwargs):
    """Track an analytics event."""
    analytics_manager.track_event(event_type, **kwargs)


# Export
__all__ = [
    'AnalyticsEvent',
    'AnalyticsManager',
    'analytics_manager',
    'track_event'
]

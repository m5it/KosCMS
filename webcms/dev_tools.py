"""
Developer Tools

Provides debugging and development utilities
"""

import time
import json
import traceback
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DebugSession:
    """Debug session information."""
    id: str
    started_at: str
    endpoint: str
    method: str
    request_data: Dict
    response_data: Optional[Dict]
    errors: List[str]
    execution_time_ms: float


class DebugManager:
    """Manages debug sessions and logging."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.sessions: Dict[str, DebugSession] = {}
        self.logs: List[Dict] = []
        self.max_logs = 1000
    
    def enable(self):
        """Enable debugging."""
        self.enabled = True
    
    def disable(self):
        """Disable debugging."""
        self.enabled = False
    
    def start_session(self, endpoint: str, method: str, 
                     request_data: Dict) -> str:
        """
        Start a debug session.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            request_data: Request data
        
        Returns:
            Session ID
        """
        if not self.enabled:
            return ""
        
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        self.sessions[session_id] = DebugSession(
            id=session_id,
            started_at=datetime.utcnow().isoformat(),
            endpoint=endpoint,
            method=method,
            request_data=request_data,
            response_data=None,
            errors=[],
            execution_time_ms=0.0
        )
        
        return session_id
    
    def end_session(self, session_id: str, response_data: Dict,
                   execution_time_ms: float):
        """
        End a debug session.
        
        Args:
            session_id: Session ID
            response_data: Response data
            execution_time_ms: Execution time in milliseconds
        """
        if not self.enabled or session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.response_data = response_data
        session.execution_time_ms = execution_time_ms
        
        # Store in logs
        self._add_log({
            'type': 'api_call',
            'session_id': session_id,
            'endpoint': session.endpoint,
            'method': session.method,
            'execution_time_ms': execution_time_ms,
            'timestamp': session.started_at,
            'errors': session.errors
        })
    
    def add_error(self, session_id: str, error: str):
        """Add error to session."""
        if session_id in self.sessions:
            self.sessions[session_id].errors.append(error)
    
    def _add_log(self, log_entry: Dict):
        """Add log entry."""
        self.logs.append(log_entry)
        
        # Trim old logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
    
    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """Get debug session."""
        return self.sessions.get(session_id)
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent logs."""
        return self.logs[-limit:]
    
    def get_slow_queries(self, threshold_ms: float = 1000) -> List[Dict]:
        """Get slow API calls."""
        return [
            log for log in self.logs
            if log.get('execution_time_ms', 0) > threshold_ms
        ]
    
    def get_error_logs(self) -> List[Dict]:
        """Get logs with errors."""
        return [
            log for log in self.logs
            if log.get('errors')
        ]
    
    def clear_logs(self):
        """Clear all logs."""
        self.logs.clear()
        self.sessions.clear()


class APITester:
    """API testing utilities."""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.results: List[Dict] = []
    
    def test_endpoint(self, method: str, endpoint: str,
                     expected_status: int = 200,
                     data: Optional[Dict] = None) -> Dict:
        """
        Test an API endpoint.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            expected_status: Expected status code
            data: Request data
        
        Returns:
            Test result
        """
        import requests
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=10)
            else:
                return {'success': False, 'error': f'Unsupported method: {method}'}
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            success = response.status_code == expected_status
            
            result = {
                'method': method,
                'endpoint': endpoint,
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response_time_ms': round(elapsed_ms, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if not success:
                result['error'] = f"Expected {expected_status}, got {response.status_code}"
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                'method': method,
                'endpoint': endpoint,
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            self.results.append(result)
            return result
    
    def run_test_suite(self) -> Dict:
        """Run comprehensive test suite."""
        tests = [
            ('GET', '/api/v1/admin/dashboard', 200),
            ('GET', '/api/v1/admin/users', 200),
            ('GET', '/api/v1/admin/pages', 200),
            ('GET', '/api/v1/admin/settings', 200),
            ('GET', '/api/v1/admin/cache/stats', 200),
            ('GET', '/health', 200),
        ]
        
        results = []
        for method, endpoint, expected in tests:
            result = self.test_endpoint(method, endpoint, expected)
            results.append(result)
        
        passed = sum(1 for r in results if r['success'])
        failed = len(results) - passed
        
        return {
            'total': len(results),
            'passed': passed,
            'failed': failed,
            'results': results
        }


class CodeGenerator:
    """Generate boilerplate code."""
    
    @staticmethod
    def generate_api_client(endpoint: str, method: str, 
                           params: List[str]) -> str:
        """Generate API client method."""
        method_name = endpoint.replace('/', '_').strip('_')
        
        code = f'''
    def {method_name}(self, {', '.join(params)}):
        """
        {method.upper()} {endpoint}
        
        Args:
            {chr(10).join(f'{p}: Description' for p in params)}
        
        Returns:
            APIResponse
        """
        data = {{{', '.join(f'"{p}": {p}' for p in params)}}}
        return self._request('{method.upper()}', '{endpoint}', data=data)
'''
        return code
    
    @staticmethod
    def generate_test(endpoint: str, method: str) -> str:
        """Generate test case."""
        test_name = f"test_{endpoint.replace('/', '_').strip('_')}"
        
        code = f'''
    def {test_name}(self, api):
        """Test {method.upper()} {endpoint}"""
        response = api._request('{method.upper()}', '{endpoint}')
        assert response.status_code == 200
'''
        return code


# Global instances
debug_manager = DebugManager()
api_tester = APITester()


# Export
__all__ = [
    'DebugSession',
    'DebugManager',
    'debug_manager',
    'APITester',
    'api_tester',
    'CodeGenerator'
]

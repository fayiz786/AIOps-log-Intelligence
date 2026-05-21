#!/usr/bin/env python3
"""
AIOps Log Intelligence System
Ingests log files, classifies errors using LLM, and generates structured alerts
with severity levels and remediation suggestions.
"""

import json
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import random

# Try to import from multiple LLM providers
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class SeverityLevel(Enum):
    """Error severity classification"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    level: str
    service: str
    message: str
    error_code: Optional[str] = None


@dataclass
class AlertSummary:
    """Structured alert with classification and remediation"""
    timestamp: str
    error: str
    severity: SeverityLevel
    suggested_fix: str
    service: str
    error_code: Optional[str] = None


class LogAnalyzer:
    """Analyzes logs and classifies errors using LLM"""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize the analyzer
        
        Args:
            use_llm: Whether to use actual LLM (requires API keys) or fallback to rule-based
        """
        self.use_llm = use_llm and (ANTHROPIC_AVAILABLE or OPENAI_AVAILABLE)
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """Initialize LLM client if available"""
        if not self.use_llm:
            return None
            
        if ANTHROPIC_AVAILABLE:
            return Anthropic()
        elif OPENAI_AVAILABLE:
            return OpenAI()
        return None
    
    def parse_log_file(self, filepath: str) -> List[LogEntry]:
        """
        Parse a log file into structured entries
        Supports common log formats: ISO timestamp | LEVEL | service | message
        """
        entries = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse: timestamp | level | service | message [| error_code]
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4:
                        entries.append(LogEntry(
                            timestamp=parts[0],
                            level=parts[1],
                            service=parts[2],
                            message=parts[3],
                            error_code=parts[4] if len(parts) > 4 else None
                        ))
        except FileNotFoundError:
            print(f"Warning: Log file {filepath} not found")
        
        return entries
    
    def classify_error_with_llm(self, log_entry: LogEntry) -> tuple[SeverityLevel, str]:
        """
        Use LLM to classify error severity and suggest remediation
        Falls back to rule-based classification if LLM unavailable
        """
        if self.use_llm and self.client:
            return self._classify_with_api(log_entry)
        else:
            return self._classify_with_rules(log_entry)
    
    def _classify_with_api(self, log_entry: LogEntry) -> tuple[SeverityLevel, str]:
        """Classify using OpenAI or Anthropic API"""
        prompt = f"""Analyze this error log and provide:
1. Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
2. Brief remediation suggestion

Log entry:
- Service: {log_entry.service}
- Level: {log_entry.level}
- Message: {log_entry.message}
- Error Code: {log_entry.error_code or 'N/A'}

Respond in JSON format:
{{"severity": "<LEVEL>", "fix": "<suggested_fix>"}}
Only respond with valid JSON, no additional text."""

        try:
            if isinstance(self.client, Anthropic):
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200
                )
                response_text = response.choices[0].message.content
            
            # Parse JSON response
            result = json.loads(response_text)
            severity = SeverityLevel[result.get("severity", "MEDIUM")]
            fix = result.get("fix", "Review logs and contact support")
            return severity, fix
            
        except Exception as e:
            print(f"LLM API error: {e}. Falling back to rule-based classification.")
            return self._classify_with_rules(log_entry)
    
    def _classify_with_rules(self, log_entry: LogEntry) -> tuple[SeverityLevel, str]:
        """Rule-based classification (fallback)"""
        message = log_entry.message.lower()
        level = log_entry.level.upper()
        
        # Critical patterns
        critical_patterns = [
            r'database.*connection.*fail',
            r'out of memory',
            r'stack overflow',
            r'fatal error',
            r'panic',
            r'emergency',
            r'system crash',
        ]
        
        # High severity patterns
        high_patterns = [
            r'timeout',
            r'connection refused',
            r'authentication.*fail',
            r'permission denied',
            r'access denied',
            r'unauthorized',
            r'circuit breaker',
        ]
        
        # Medium severity patterns
        medium_patterns = [
            r'retry',
            r'warning',
            r'deprecated',
            r'slow',
            r'latency',
        ]
        
        # Check patterns
        for pattern in critical_patterns:
            if re.search(pattern, message):
                return (SeverityLevel.CRITICAL, 
                       "Immediate attention required. Check system resources and restart services.")
        
        for pattern in high_patterns:
            if re.search(pattern, message):
                return (SeverityLevel.HIGH,
                       "Investigate connection/auth issues. Check service dependencies and credentials.")
        
        for pattern in medium_patterns:
            if re.search(pattern, message):
                return (SeverityLevel.MEDIUM,
                       "Monitor trend. Consider scaling resources or optimizing queries.")
        
        # Level-based fallback
        if level in ['ERROR', 'CRITICAL', 'ALERT', 'EMERGENCY']:
            return (SeverityLevel.HIGH, "Review error logs for root cause analysis.")
        elif level == 'WARNING':
            return (SeverityLevel.MEDIUM, "Monitor situation and gather additional context.")
        else:
            return (SeverityLevel.LOW, "Informational entry. No immediate action required.")
    
    def analyze_logs(self, filepath: str) -> List[AlertSummary]:
        """
        Analyze logs and generate alerts
        """
        entries = self.parse_log_file(filepath)
        alerts = []
        
        for entry in entries:
            severity, fix = self.classify_error_with_llm(entry)
            
            alert = AlertSummary(
                timestamp=entry.timestamp,
                error=entry.message[:80],  # Truncate long messages
                severity=severity,
                suggested_fix=fix[:100],  # Truncate fix suggestions
                service=entry.service,
                error_code=entry.error_code
            )
            alerts.append(alert)
        
        return alerts


def generate_sample_logs(output_file: str = "sample.log", num_entries: int = 15):
    """Generate a sample log file for demonstration"""
    
    base_time = datetime.now() - timedelta(hours=1)
    
    log_templates = [
        # Critical issues
        ("CRITICAL", "database", "Fatal error: Database connection pool exhausted", "DB_001"),
        ("ERROR", "api", "panic: out of memory in request handler", "OOM_001"),
        ("CRITICAL", "auth", "Emergency: Authentication service unreachable - circuit breaker open", "AUTH_001"),
        
        # High severity
        ("ERROR", "cache", "Connection refused: Redis timeout after 30s", "REDIS_001"),
        ("WARNING", "api", "High latency detected: Request timeout (5s threshold exceeded)", "TIMEOUT_001"),
        ("ERROR", "worker", "Authentication failed for service-to-service call", "AUTH_002"),
        
        # Medium severity
        ("WARNING", "scheduler", "Retry attempt 3/5: Job processing failed, will retry", "RETRY_001"),
        ("INFO", "config", "Deprecated: Environment variable API_KEY_OLD still in use", "DEPREC_001"),
        ("WARNING", "database", "Slow query detected: Query took 12.5s (threshold: 5s)", "SLOW_001"),
        
        # Lower severity
        ("INFO", "health", "Graceful degradation: Secondary cache unavailable, using primary", "INFO_001"),
        ("DEBUG", "api", "Request rate limiter: Client approaching threshold (950/1000)", "LIMIT_001"),
        ("INFO", "monitor", "Health check passed for all services", None),
        ("WARNING", "api", "Permission denied: User lacks required scope for resource", "PERMS_001"),
        ("ERROR", "storage", "Connection refused to object storage service", "STORAGE_001"),
        ("INFO", "system", "Memory usage: 76% - consider scaling", None),
    ]
    
    logs = []
    for i, (level, service, message, error_code) in enumerate(log_templates):
        timestamp = (base_time + timedelta(minutes=i*4)).isoformat()
        
        if error_code:
            log_line = f"{timestamp} | {level} | {service} | {message} | {error_code}"
        else:
            log_line = f"{timestamp} | {level} | {service} | {message}"
        
        logs.append(log_line)
    
    with open(output_file, 'w') as f:
        f.write("# AIOps Sample Log File\n")
        f.write("# Format: timestamp | level | service | message | [error_code]\n")
        f.write("# Generated for demonstration\n\n")
        f.write("\n".join(logs))
    
    print(f"✓ Generated sample log file: {output_file}")
    return output_file


def format_alert_table(alerts: List[AlertSummary]) -> str:
    """Format alerts as a formatted ASCII table"""
    
    if not alerts:
        return "No alerts to display"
    
    # Color codes for terminal output
    COLORS = {
        SeverityLevel.CRITICAL: "\033[91m",  # Red
        SeverityLevel.HIGH: "\033[93m",      # Yellow
        SeverityLevel.MEDIUM: "\033[94m",    # Blue
        SeverityLevel.LOW: "\033[92m",       # Green
        SeverityLevel.INFO: "\033[97m",      # White
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Column widths
    col_widths = {
        'timestamp': 25,
        'error': 40,
        'severity': 12,
        'fix': 50,
    }
    
    # Header
    header = (
        f"{BOLD}{'TIMESTAMP':<{col_widths['timestamp']}} | "
        f"{'ERROR':<{col_widths['error']}} | "
        f"{'SEVERITY':<{col_widths['severity']}} | "
        f"{'SUGGESTED FIX':<{col_widths['fix']}}{RESET}"
    )
    
    separator = "-" * (sum(col_widths.values()) + 9)  # +9 for " | " separators
    
    # Rows
    rows = [separator, header, separator]
    
    for alert in alerts:
        # Truncate strings to fit columns
        timestamp = alert.timestamp[:col_widths['timestamp']]
        error = alert.error[:col_widths['error']]
        severity = alert.severity.value
        fix = alert.suggested_fix[:col_widths['fix']]
        
        color = COLORS.get(alert.severity, "")
        row = (
            f"{timestamp:<{col_widths['timestamp']}} | "
            f"{error:<{col_widths['error']}} | "
            f"{color}{severity:<{col_widths['severity']}}{RESET} | "
            f"{fix:<{col_widths['fix']}}"
        )
        rows.append(row)
    
    rows.append(separator)
    
    return "\n".join(rows)


def print_summary_stats(alerts: List[AlertSummary]):
    """Print summary statistics"""
    severity_counts = {}
    for alert in alerts:
        severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
    
    print("\n" + "="*60)
    print("ALERT SUMMARY STATISTICS")
    print("="*60)
    print(f"Total Alerts: {len(alerts)}")
    print("\nBreakdown by Severity:")
    for severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, 
                     SeverityLevel.LOW, SeverityLevel.INFO]:
        count = severity_counts.get(severity.value, 0)
        if count > 0:
            print(f"  {severity.value:<12}: {count:>3} alerts")
    
    print("="*60 + "\n")


def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("AIOps LOG INTELLIGENCE SYSTEM")
    print("="*60 + "\n")
    
    # Generate sample logs
    log_file = generate_sample_logs()
    
    # Initialize analyzer (with LLM if available, fallback to rules)
    use_llm = ANTHROPIC_AVAILABLE or OPENAI_AVAILABLE
    if not use_llm:
        print("⚠ LLM APIs not available. Using rule-based classification.\n")
    else:
        print("✓ Using LLM for intelligent error classification.\n")
    
    analyzer = LogAnalyzer(use_llm=use_llm)
    
    # Analyze logs
    print("Processing logs...")
    alerts = analyzer.analyze_logs(log_file)
    
    # Sort by severity (critical first)
    severity_order = {
        SeverityLevel.CRITICAL: 0,
        SeverityLevel.HIGH: 1,
        SeverityLevel.MEDIUM: 2,
        SeverityLevel.LOW: 3,
        SeverityLevel.INFO: 4,
    }
    alerts.sort(key=lambda x: severity_order[x.severity])
    
    # Display results
    print("\n" + format_alert_table(alerts))
    print_summary_stats(alerts)
    
    # Export to JSON
    json_output = [
        {
            "timestamp": alert.timestamp,
            "service": alert.service,
            "error": alert.error,
            "error_code": alert.error_code,
            "severity": alert.severity.value,
            "suggested_fix": alert.suggested_fix,
        }
        for alert in alerts
    ]
    
    with open("alerts.json", "w") as f:
        json.dump(json_output, f, indent=2)
    
    print(f"✓ Exported {len(alerts)} alerts to alerts.json")


if __name__ == "__main__":
    main()

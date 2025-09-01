from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, computed_field
import json


class LogRecord(BaseModel):
    """
    Log record model compatible with fluent-bit output format.
    
    Supports common log fields and metadata from various log sources.
    """
    
    # Core fields
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the log record")
    timestamp: datetime = Field(..., description="Log timestamp (UTC)")
    message: str = Field(..., min_length=1, description="Log message content")
    
    # Optional standard fields
    severity: Optional[str] = Field(default="info", description="Log level (info, warn, error, debug, etc.)")
    config: Optional[str] = Field(default=None, description="Log service source")
    context: Optional[str] = Field(default=None, description="logical group of configs")
    source: Optional[str] = Field(default=None, description="log file or stdout/stderr")
    hostname: Optional[str] = Field(default=None, description="Host/container name")
    
    # System fields
    ingest_timestamp: Optional[datetime] = Field(default=None, description="When the log was ingested")

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_timestamp(cls, v):
        """Parse various timestamp formats from fluent-bit."""
        if isinstance(v, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(v, tz=timezone.utc)
        elif isinstance(v, str):
            # ISO format string
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing other formats
                from dateutil import parser
                return parser.parse(v).replace(tzinfo=timezone.utc)
        elif isinstance(v, datetime):
            # Ensure timezone aware
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        else:
            raise ValueError(f"Invalid timestamp format: {v}")
    
    @field_validator('level', mode='before')
    @classmethod
    def normalize_level(cls, v):
        """Normalize log level to lowercase."""
        if v is None:
            return "info"
        return str(v).lower()
    
    @field_validator('metadata', mode='before')
    @classmethod
    def ensure_serializable_metadata(cls, v):
        """Ensure metadata contains only JSON-serializable values."""
        if v is None:
            return {}
        
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj
            else:
                return str(obj)
        
        return make_serializable(v)
    
    @computed_field
    @property
    def search_text(self) -> str:
        """Computed field for full-text search indexing."""
        parts = [self.message]
        if self.source:
            parts.append(self.source)
        if self.service:
            parts.append(self.service)
        if self.hostname:
            parts.append(self.hostname)
        if self.tag:
            parts.append(self.tag)
        return " ".join(parts)
    
    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for database insertion."""
        data = self.model_dump(exclude={'id', 'search_text'})
        data['id'] = self.id
        data['metadata'] = json.dumps(data['metadata']) if data['metadata'] else None
        data['labels'] = json.dumps(data['labels']) if data['labels'] else None
        data['ingested_at'] = self.ingested_at or datetime.now(timezone.utc)
        return data
    
    @classmethod
    def from_fluent_bit_record(cls, record: Union[List, Dict]) -> "LogRecord":
        """
        Create LogRecord from fluent-bit format.
        
        Supports both formats:
        - [timestamp, {data}] (default fluent-bit format)
        - {timestamp: ..., message: ...} (JSON format)
        """
        if isinstance(record, list) and len(record) == 2:
            # Format: [timestamp, {data}]
            timestamp_val, data = record
            
            # Extract message from various possible fields
            message = (
                data.get("log") or 
                data.get("message") or 
                data.get("msg") or 
                str(data)
            )
            
            return cls(
                timestamp=timestamp_val,
                message=message,
                level=data.get("level") or data.get("severity"),
                source=data.get("source") or data.get("_source"),
                service=data.get("service") or data.get("service_name"),
                hostname=data.get("hostname") or data.get("host"),
                tag=data.get("tag") or data.get("fluent_tag"),
                container_id=data.get("container_id"),
                container_name=data.get("container_name"),
                labels=data.get("labels", {}),
                metadata={k: v for k, v in data.items() 
                         if k not in ["log", "message", "msg", "level", "severity", 
                                    "source", "_source", "service", "service_name",
                                    "hostname", "host", "tag", "fluent_tag", 
                                    "container_id", "container_name", "labels"]}
            )
        
        elif isinstance(record, dict):
            # Format: {timestamp: ..., message: ...}
            timestamp_val = (
                record.get("@timestamp") or 
                record.get("timestamp") or 
                record.get("time") or
                datetime.now(timezone.utc)
            )
            
            message = (
                record.get("log") or 
                record.get("message") or 
                record.get("msg") or
                str(record)
            )
            
            return cls(
                timestamp=timestamp_val,
                message=message,
                level=record.get("level") or record.get("severity"),
                source=record.get("source") or record.get("_source"),
                service=record.get("service") or record.get("service_name"),
                hostname=record.get("hostname") or record.get("host"),
                tag=record.get("tag") or record.get("fluent_tag"),
                container_id=record.get("container_id"),
                container_name=record.get("container_name"),
                labels=record.get("labels", {}),
                metadata={k: v for k, v in record.items() 
                         if k not in ["@timestamp", "timestamp", "time", "log", 
                                    "message", "msg", "level", "severity", 
                                    "source", "_source", "service", "service_name",
                                    "hostname", "host", "tag", "fluent_tag", 
                                    "container_id", "container_name", "labels"]}
            )
        
        else:
            raise ValueError(f"Invalid fluent-bit record format: {record}")
    
    class Config:
        # Allow extra fields for flexibility
        extra = "forbid"
        # Use enum values for serialization
        use_enum_values = True
        # Validate assignment
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
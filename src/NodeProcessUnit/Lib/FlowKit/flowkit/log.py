from flowkit.node import Node
from flowkit.npu_control import NpuControl
from datetime import datetime
import traceback


class Logger:
    """
    Cloud-based logging system for distributed node execution.
    
    This logger sends log messages to a remote NPU control server rather than
    writing to local stdout/stderr. Designed for distributed cloud environments
    where centralized logging is required.
    
    Features:
    - Remote log aggregation via NPU control
    - Structured log formatting with metadata
    - Multiple log levels (INFO, WARNING, DEBUG, ERROR)
    - Automatic timestamp and node identification
    """
    
    def __init__(self, node: Node):
        """
        Initialize the Logger with a Node instance.
        
        Args:
            node (Node): The Node instance this logger is attached to.
                        Used to extract node metadata (name, ID) and communicate
                        with the NPU control system.
        """
        print(f"[Logger] Initializing cloud logger for node: {node.node_name}")
        
        self.node = node
        
        # Initialize NPU control for remote logging communication
        # This establishes connection to the centralized logging server
        self.npu_control = NpuControl(node)
        
        print(f"[Logger] Cloud logger initialized successfully")
        print(f"[Logger] Node: {node.node_name}, Runner ID: {node.get_id()}")

    def _format_message(self, level: str, message: str) -> str:
        """
        Format log message with metadata for cloud logging system.
        
        Creates a structured log entry containing:
        - Log level (INFO, WARNING, DEBUG, ERROR)
        - Node name for identifying the source
        - Runner ID for tracing execution
        - Timestamp for temporal ordering
        - The actual log message
        
        Args:
            level (str): Log level (INFO, WARNING, DEBUG, ERROR)
            message (str): The log message content
            
        Returns:
            str: Formatted log message ready for transmission
        """
        # Generate ISO-format timestamp for precise log ordering
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format: [LEVEL][NODE_NAME][RUNNER_ID][TIMESTAMP] message
        formatted = (
            f"[{level}]"
            f"[{self.node.node_name}]"
            f"[{self.node.get_id()}]"
            f"[{timestamp}] "
            f"{message}"
        )
        
        return formatted

    async def info(self, message: str):
        """
        Log an informational message to the cloud logging system.
        
        Use for general operational messages, status updates, and
        successful operations that don't indicate problems.
        
        Args:
            message (str): The informational message to log
            
        Example:
            await logger.info("Processing started successfully")
        """
        formatted_msg = self._format_message("INFO", message)
        print(f"[Logger] INFO: {message}")  # Local echo for debugging
        
        try:
            # Send to remote logging server via NPU control
            await self.npu_control.log(formatted_msg)
        except Exception as e:
            # If remote logging fails, log locally as fallback
            print(f"[Logger] WARNING: Failed to send INFO log to server: {e}")
            print(f"[Logger] Original message: {formatted_msg}")

    async def warning(self, message: str):
        """
        Log a warning message to the cloud logging system.
        
        Use for potentially problematic situations that don't prevent
        execution but may require attention.
        
        Args:
            message (str): The warning message to log
            
        Example:
            await logger.warning("Retrying connection after timeout")
        """
        formatted_msg = self._format_message("WARNING", message)
        print(f"[Logger] WARNING: {message}")  # Local echo for debugging
        
        try:
            # Send to remote logging server via NPU control
            await self.npu_control.log(formatted_msg)
        except Exception as e:
            # If remote logging fails, log locally as fallback
            print(f"[Logger] WARNING: Failed to send WARNING log to server: {e}")
            print(f"[Logger] Original message: {formatted_msg}")

    async def debug(self, message: str):
        """
        Log a debug message to the cloud logging system.
        
        Use for detailed diagnostic information useful during development
        and troubleshooting. May be filtered out in production environments.
        
        Args:
            message (str): The debug message to log
            
        Example:
            await logger.debug(f"Variable state: {variable_value}")
        """
        formatted_msg = self._format_message("DEBUG", message)
        print(f"[Logger] DEBUG: {message}")  # Local echo for debugging
        
        try:
            # Send to remote logging server via NPU control
            await self.npu_control.log(formatted_msg)
        except Exception as e:
            # If remote logging fails, log locally as fallback
            print(f"[Logger] WARNING: Failed to send DEBUG log to server: {e}")
            print(f"[Logger] Original message: {formatted_msg}")

    async def error(self, message: str, include_traceback: bool = False):
        """
        Log an error message to the cloud logging system.
        
        Use for error conditions, exceptions, and failures that need
        immediate attention or indicate execution problems.
        
        Args:
            message (str): The error message to log
            include_traceback (bool): If True, append current exception traceback
            
        Example:
            try:
                risky_operation()
            except Exception as e:
                await logger.error(f"Operation failed: {e}", include_traceback=True)
        """
        # Optionally append traceback for better error diagnosis
        if include_traceback:
            tb = traceback.format_exc()
            message = f"{message}\nTraceback:\n{tb}"
        
        formatted_msg = self._format_message("ERROR", message)
        print(f"[Logger] ERROR: {message}")  # Local echo for debugging
        
        try:
            # Send to remote logging server via NPU control
            await self.npu_control.log(formatted_msg)
        except Exception as e:
            # Critical: If error logging fails, ensure local visibility
            print(f"[Logger] CRITICAL: Failed to send ERROR log to server: {e}")
            print(f"[Logger] Original error message: {formatted_msg}")

    async def log_with_context(self, level: str, message: str, context: dict = None):
        """
        Log a message with additional context data.
        
        Useful for including structured data alongside log messages
        for better debugging and analysis in cloud environments.
        
        Args:
            level (str): Log level (INFO, WARNING, DEBUG, ERROR)
            message (str): The log message
            context (dict): Additional context data to include
            
        Example:
            await logger.log_with_context(
                "INFO",
                "User action completed",
                {"user_id": "123", "action": "upload", "duration_ms": 450}
            )
        """
        # Build message with context if provided
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            full_message = f"{message} | Context: {context_str}"
        else:
            full_message = message
        
        formatted_msg = self._format_message(level, full_message)
        print(f"[Logger] {level}: {full_message}")  # Local echo
        
        try:
            # Send to remote logging server via NPU control
            await self.npu_control.log(formatted_msg)
        except Exception as e:
            print(f"[Logger] WARNING: Failed to send {level} log to server: {e}")
            print(f"[Logger] Original message: {formatted_msg}")

    async def flush(self):
        """
        Ensure all pending logs are sent to the cloud logging system.
        
        Call this before node shutdown to guarantee log delivery.
        Useful for ensuring critical logs aren't lost during errors.
        """
        print("[Logger] Flushing logs to cloud logging system...")
        try:
            # Note: Actual flush implementation depends on NpuControl API
            # This is a placeholder for explicit flush functionality
            await self.info("Logger flush completed")
            print("[Logger] Log flush completed successfully")
        except Exception as e:
            print(f"[Logger] ERROR: Failed to flush logs: {e}")
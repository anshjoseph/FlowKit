import sys
import json
from uuid import UUID
import asyncio
import inspect
from flowkit.npu_control import NpuControl


class Node:
    """
    Node class for executing async functions in a distributed workflow system.
    
    This class handles:
    - Loading input data from JSON files
    - Registering and executing async main functions
    - Communicating results back to the NPU control system
    - Error handling and logging
    """
    
    def __init__(self):
        """
        Initialize the Node with command-line arguments and NPU control.
        
        Expected command-line arguments:
            1. input.json - Path to the input data file
            2. runner_id - Unique identifier for this runner (UUID format)
            3. self_addr - Network address of this node
            4. node_name - Human-readable name for this node
        """
        print("[Node] Initializing...")
        
        # Validate command-line arguments
        assert len(sys.argv) >= 5, (
            "Usage: python temp.py input.json runner_id self_addr node_name"
        )
        
        # Parse command-line arguments
        self.input_file = sys.argv[1]
        self.runner_id = UUID(sys.argv[2])
        self.self_addr = sys.argv[3]
        self.node_name = sys.argv[4]
        self.function = None
        
        print(f"[Node] Configuration:")
        print(f"  - Input file: {self.input_file}")
        print(f"  - Runner ID: {self.runner_id}")
        print(f"  - Self address: {self.self_addr}")
        print(f"  - Node name: {self.node_name}")
        
        # Load input data from JSON file
        try:
            with open(self.input_file, "r") as file:
                self.data = json.load(file)
            print(f"[Node] Successfully loaded input data from {self.input_file}")
            print(f"[Node] Input data keys: {list(self.data.keys())}")
        except FileNotFoundError:
            print(f"[Node] ERROR: Input file not found: {self.input_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"[Node] ERROR: Invalid JSON in input file: {e}")
            raise
        
        # Initialize NPU control for communication with the control system
        print("[Node] Initializing NPU control...")
        self.npu_control = NpuControl(self)
        print("[Node] NPU control initialized successfully")

    def get_inputs(self):
        """
        Get the input data loaded from the JSON file.
        
        Returns:
            dict: The input data dictionary
        """
        print("[Node] Returning input data")
        return self.data

    def get_id(self):
        """
        Get the unique runner ID for this node.
        
        Returns:
            UUID: The runner's unique identifier
        """
        return self.runner_id

    def register_main(self, function):
        """
        Register an async main function to be executed by this node.
        
        Args:
            function: An async function to execute. Must be a coroutine function.
        
        Raises:
            AssertionError: If the provided function is not async
        """
        print(f"[Node] Registering main function: {function.__name__}")
        
        # Ensure only async functions are registered
        assert inspect.iscoroutinefunction(function), (
            "Only async functions are allowed as entry points. "
            f"Function '{function.__name__}' is not async."
        )
        
        self.function = function
        print(f"[Node] Function '{function.__name__}' registered successfully")

    async def run_func(self):
        """
        Execute the registered async function and handle results/errors.
        
        The main function must return a tuple of (nodes, outputs, message):
            - nodes: List of downstream nodes to execute
            - outputs: Dictionary of output data
            - message: Status or result message
        """
        print("[Node] Starting function execution...")
        
        try:
            # Execute the registered async main function
            print(f"[Node] Calling function: {self.function.__name__}")
            result = await self.function()
            print(f"[Node] Function {self.function.__name__} completed successfully")
            
            # Validate the return format
            if not isinstance(result, tuple) or len(result) != 3:
                error_msg = (
                    "Main function must return a tuple: (nodes, outputs, message). "
                    f"Got: {type(result)}"
                )
                print(f"[Node] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            # Unpack the result
            nodes, outputs, message = result
            print(f"[Node] Result unpacked:")
            print(f"  - Nodes: {nodes}")
            print(f"  - Outputs keys: {list(outputs.keys()) if isinstance(outputs, dict) else 'N/A'}")
            print(f"  - Message: {message}")
            
            # Send successful result back to NPU control
            print("[Node] Sending DONE status to NPU control...")
            await self.npu_control.result(
                nodes,
                outputs,
                message,
                NpuControl.DONE
            )
            print("[Node] Result sent successfully with DONE status")
            
        except Exception as e:
            # Log the error with full details
            print(f"[Node] ERROR during execution: {type(e).__name__}")
            print(f"[Node] ERROR message: {str(e)}")
            print(f"[Node] Sending ERROR status to NPU control...")
            
            # Send error result back to NPU control
            try:
                await self.npu_control.result(
                    [],      # No downstream nodes on error
                    {},      # No outputs on error
                    str(e),  # Error message
                    NpuControl.ERROR
                )
                print("[Node] Error result sent successfully")
            except Exception as send_error:
                print(f"[Node] CRITICAL: Failed to send error result: {send_error}")
                raise

    def run(self):
        """
        Start the node execution by running the registered async function.
        
        This is the main entry point that should be called after registering
        a main function with register_main().
        
        Raises:
            AssertionError: If no function has been registered
        """
        print("[Node] Starting node execution...")
        
        # Ensure a function has been registered
        assert self.function is not None, (
            "No async function registered to run. "
            "Call register_main() before run()."
        )
        
        print(f"[Node] Executing registered function: {self.function.__name__}")
        
        # Run the async function using asyncio
        try:
            asyncio.run(self.run_func())
            print("[Node] Execution completed")
        except KeyboardInterrupt:
            print("[Node] Execution interrupted by user")
            raise
        except Exception as e:
            print(f"[Node] CRITICAL: Execution failed with error: {e}")
            raise
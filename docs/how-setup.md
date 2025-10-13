# FlowKit - Distributed Node Processing System

A distributed system for managing and executing node-based workflows with built-in monitoring, security, and process isolation.

## 🏗️ Architecture

FlowKit consists of five core components:

- **FlowKitControlUnit** - Central control and orchestration
- **FlowTraceMonitor** - Real-time monitoring and tracing
- **NodeProcessUnit** - Isolated code execution environment
- **SecretManager** - Secure credential and secret management
- **NodeRunner** - Node execution and workflow management

## 📋 Prerequisites

- Python 3.8+
- pip (Python package installer)
- Virtual environment support

## 🚀 Installation

### 1. Create the Shared Virtual Environment

All servers share a common base environment. Create it using:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r req.txt
```

### 2. Special Setup for NodeProcessUnit

NodeProcessUnit requires **two separate environments** for security and isolation:

#### Environment 1: Server Environment
This is covered by the shared environment created in step 1.

#### Environment 2: Code Execution Environment

Create a system-level isolated environment for executing user code:

```bash
# Create the execution environment
python -m venv node_execution_env
source node_execution_env/bin/activate  # On Windows: node_execution_env\Scripts\activate

# Install execution environment dependencies
pip install -r src/NodeProcessUnit/v-req.txt

# Install FlowKit library for server communication
cd src/NodeProcessUnit/Lib/FlowKit
pip install -e .
cd ../../../..
```

This dual-environment approach ensures:
- ✅ Server communication and control
- ✅ Isolated code execution
- ✅ Security through process separation
- ✅ Code execution moderation

## ⚙️ Configuration

### Environment Variables

Each server requires its own `.env` file. Configure the following:

#### FlowKitControlUnit
```env
# Add your FlowKitControlUnit environment variables
```

#### FlowTraceMonitor
```env
# Add your FlowTraceMonitor environment variables
```

#### NodeProcessUnit
```env
# Add your NodeProcessUnit environment variables
EXECUTION_ENV_PATH=path/to/node_execution_env
```

#### SecretManager
```env
# Add your SecretManager environment variables
```

#### NodeRunner
```env
# Add your NodeRunner environment variables
```

## 🎯 Running the Servers

### Start Individual Servers

```bash
# Activate the shared environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start FlowKitControlUnit
python src/FlowKitControlUnit/main.py

# Start FlowTraceMonitor
python src/FlowTraceMonitor/main.py

# Start NodeProcessUnit
python src/NodeProcessUnit/main.py

# Start SecretManager
python src/SecretManager/main.py

# Start NodeRunner
python src/NodeRunner/main.py
```

"use client"
import { useState, useEffect } from 'react';
import { Zap, Network, GitBranch, Cpu, ArrowRight, Activity, Box } from 'lucide-react';
import Link from 'next/link';

export default function Hero() {
  const [activeNode, setActiveNode] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsAnimating(true);
      setActiveNode((prev) => (prev + 1) % 4);
      setTimeout(() => setIsAnimating(false), 500);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-white text-black overflow-hidden">
      {/* Subtle animated background */}
      <div className="absolute inset-0 opacity-[0.015]">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,1)_1px,transparent_1px)] bg-[size:64px_64px]" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-12 sm:px-8">
        {/* Minimal Header */}
        <nav className="flex items-center justify-between mb-24 py-4">
          <div className="flex items-center gap-2">
            <Box className="w-5 h-5" strokeWidth={2} />
            <span className="text-lg font-medium tracking-tight">FlowKit</span>
          </div>
          <div className="flex gap-3 items-center">
            <button className="px-5 py-2 text-sm bg-black text-white rounded-full hover:bg-gray-800 transition-colors font-medium">
              <Link href={"/dashboard"}>Get started</Link>
            </button>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="grid lg:grid-cols-[1.2fr_1fr] gap-20 items-center mb-32">
          {/* Left Column - Text */}
          <div className="space-y-8 max-w-xl">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-black/10 text-xs font-medium">
              <Zap className="w-3 h-3" strokeWidth={2.5} />
              <span>Distributed Computing</span>
            </div>

            <h1 className="text-6xl sm:text-7xl font-light leading-[0.95] tracking-tight">
              Run AI
              <br />
              <span className="font-semibold">At Scale</span>
            </h1>

            <p className="text-lg text-gray-600 leading-relaxed font-light">
              Execute complex AI workloads across distributed nodes. Write Python code using our simple Node API, define workflows as DAGs, and let FlowKit handle parallel execution.
            </p>

            <div className="flex gap-3 pt-4">
              <button className="group px-6 py-3 rounded-full bg-black text-white text-sm font-medium hover:bg-gray-800 transition-all flex items-center gap-2">
                <Link href={"/dashboard"}>Get started</Link>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" strokeWidth={2} />
              </button>
            </div>
          </div>

          {/* Right Column - Minimal Visual */}
          <div className="relative lg:ml-auto">
            <div className="relative w-80 h-80 mx-auto">
              {/* Central Node */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className={`w-16 h-16 rounded-full bg-black flex items-center justify-center transition-all duration-300 ${isAnimating ? 'scale-105' : 'scale-100'}`}>
                  <Activity className="w-7 h-7 text-white" strokeWidth={2} />
                </div>
              </div>

              {/* Worker Nodes - Clean circles */}
              {[0, 1, 2, 3].map((i) => {
                const angle = (i * Math.PI * 2) / 4 - Math.PI / 2;
                const radius = 110;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                const isActive = activeNode === i;

                return (
                  <div
                    key={i}
                    className="absolute top-1/2 left-1/2"
                    style={{
                      transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`
                    }}
                  >
                    {/* Connection Line */}
                    <svg
                      className="absolute top-1/2 left-1/2 pointer-events-none"
                      style={{
                        width: Math.abs(x) * 2,
                        height: Math.abs(y) * 2,
                        transform: `translate(-50%, -50%) rotate(${angle}rad)`
                      }}
                    >
                      <line
                        x1="0"
                        y1="50%"
                        x2="100%"
                        y2="50%"
                        stroke={isActive ? '#000000' : '#e5e7eb'}
                        strokeWidth="1.5"
                        className="transition-all duration-500"
                      />
                      {isActive && (
                        <line
                          x1="0"
                          y1="50%"
                          x2="100%"
                          y2="50%"
                          stroke="#000000"
                          strokeWidth="1.5"
                          strokeDasharray="4 4"
                          className="animate-pulse"
                        />
                      )}
                    </svg>

                    {/* Node */}
                    <div className={`transition-all duration-300 ${isActive ? 'scale-110' : 'scale-100'}`}>
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                        isActive 
                          ? 'bg-black' 
                          : 'bg-white border border-gray-200'
                      }`}>
                        <Cpu className={`w-5 h-5 transition-colors ${isActive ? 'text-white' : 'text-gray-400'}`} strokeWidth={2} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Features - Minimal Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-black/5 border border-black/5 rounded-2xl overflow-hidden">
          <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
            <Network className="w-5 h-5 mb-4" strokeWidth={2} />
            <div className="font-medium text-sm mb-1">Distributed</div>
            <div className="text-xs text-gray-500 leading-relaxed">Parallel execution across worker nodes</div>
          </div>
          <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
            <GitBranch className="w-5 h-5 mb-4" strokeWidth={2} />
            <div className="font-medium text-sm mb-1">DAG Workflows</div>
            <div className="text-xs text-gray-500 leading-relaxed">Define complex task pipelines</div>
          </div>
          <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
            <Zap className="w-5 h-5 mb-4" strokeWidth={2} />
            <div className="font-medium text-sm mb-1">Simple API</div>
            <div className="text-xs text-gray-500 leading-relaxed">Write Python code with Node API</div>
          </div>
          <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
            <Activity className="w-5 h-5 mb-4" strokeWidth={2} />
            <div className="font-medium text-sm mb-1">Real-time</div>
            <div className="text-xs text-gray-500 leading-relaxed">Monitor execution live</div>
          </div>
        </div>

        {/* Code Example Section */}
        <div className="mt-32 max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-light mb-3">Simple to use</h2>
            <p className="text-gray-600">Run any Python code — LLMs, RAG, document processing, or custom workflows</p>
          </div>
          
          <div className="bg-black rounded-2xl p-8 overflow-hidden">
            <div className="flex items-center gap-2 mb-6">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-gray-700"></div>
                <div className="w-3 h-3 rounded-full bg-gray-700"></div>
                <div className="w-3 h-3 rounded-full bg-gray-700"></div>
              </div>
              <span className="text-gray-500 text-xs ml-2">node.py</span>
            </div>
            
            <pre className="text-sm leading-relaxed overflow-x-auto">
              <code className="text-gray-300 font-mono">
{`from flowkit.node import Node
from flowkit.log import Logger

node = Node()
logger = Logger(node)

key = "{{{secret::OPENAI_KEY}}}"  # load from secret manager

async def main():
    inputs = node.get_inputs()
    ret = inputs["a"] + inputs["b"]
    
    for i in range(10):
        await logger.info("Processing...")
    
    await logger.info(key)
    return [], {"out": ret, "key": key}, "run successfully"

node.register_main(main)
node.run()`}
              </code>
            </pre>
          </div>
        </div>

        {/* Architecture Section */}
        <div className="mt-32 max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-light mb-3">Built for reliability</h2>
            <p className="text-gray-600">Distributed architecture with automatic recovery and atomic execution</p>
          </div>

          <div className="space-y-6">
            {/* FlowKit Control Unit */}
            <div className="border border-black/10 rounded-2xl p-8 hover:border-black/20 transition-colors">
              <div className="flex items-start gap-6">
                <div className="w-12 h-12 rounded-xl bg-black flex items-center justify-center flex-shrink-0">
                  <GitBranch className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-lg mb-2">FlowKit Control Unit</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-4">
                    Executes DAG workflows and manages the FlowControlBlock containing code, results, and execution state. 
                    Integrates with trace server for comprehensive input/output logging.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">DAG Execution</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">State Management</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Trace Logging</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Pause/Resume</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Node Runner */}
            <div className="border border-black/10 rounded-2xl p-8 hover:border-black/20 transition-colors">
              <div className="flex items-start gap-6">
                <div className="w-12 h-12 rounded-xl bg-black flex items-center justify-center flex-shrink-0">
                  <Activity className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-lg mb-2">Node Runner</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-4">
                    Orchestrates task scheduling across NPUs, monitors worker health, tracks node execution, 
                    and resolves secrets from the secret manager for secure operations.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Task Scheduling</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">NPU Monitoring</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Secret Management</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Task Tracking</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Node Processing Units */}
            <div className="border border-black/10 rounded-2xl p-8 hover:border-black/20 transition-colors">
              <div className="flex items-start gap-6">
                <div className="w-12 h-12 rounded-xl bg-black flex items-center justify-center flex-shrink-0">
                  <Cpu className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-lg mb-2">Node Processing Units (NPUs)</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-4">
                    Isolated worker nodes that execute your Python code. Each node runs atomically with guaranteed 
                    execution and automatic state persistence for failure recovery.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Isolated Execution</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Atomic Operations</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">Auto Recovery</span>
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">State Persistence</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Key Features Banner */}
          <div className="mt-12 grid sm:grid-cols-3 gap-6">
            <div className="text-center p-6">
              <div className="text-2xl font-light mb-2">🔄</div>
              <div className="font-medium text-sm mb-1">Auto Recovery</div>
              <div className="text-xs text-gray-500">Resume from any failure point</div>
            </div>
            <div className="text-center p-6">
              <div className="text-2xl font-light mb-2">⚛️</div>
              <div className="font-medium text-sm mb-1">Atomic Nodes</div>
              <div className="text-xs text-gray-500">Guaranteed execution integrity</div>
            </div>
            <div className="text-center p-6">
              <div className="text-2xl font-light mb-2">⏸️</div>
              <div className="font-medium text-sm mb-1">Pause & Resume</div>
              <div className="text-xs text-gray-500">Control execution flow anytime</div>
            </div>
          </div>
        </div>

        {/* Stats - Ultra minimal */}
        <div className="flex justify-center gap-16 mt-20 pt-12 border-t border-black/5">
          <div className="text-center">
            <div className="text-3xl font-light mb-1">99.9%</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider">Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-light mb-1">10x</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider">Faster</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-light mb-1">∞</div>
            <div className="text-xs text-gray-500 uppercase tracking-wider">Scale</div>
          </div>
        </div>
      </div>
    </div>
  );
}
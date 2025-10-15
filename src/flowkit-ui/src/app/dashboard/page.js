"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, Plus, Trash2, Play, Search, Eye, AlertCircle, CheckCircle, Copy, Check, Code, Settings, Maximize2, X, GitBranch, Zap } from "lucide-react";

export default function Dashboard() {
    const pathname = usePathname();
    const [activeTab, setActiveTab] = useState("builder");
    const [nodes, setNodes] = useState([
        { id: "start", name: "start", code: "", flowLevel: 1, x: 400, y: 100 }
    ]);
    const [connections, setConnections] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [currentInput, setCurrentInput] = useState("{}");
    const [flowId, setFlowId] = useState("");
    const [flowData, setFlowData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [copied, setCopied] = useState(false);
    const [draggingNode, setDraggingNode] = useState(null);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
    const [connecting, setConnecting] = useState(null);
    const [codeEditorOpen, setCodeEditorOpen] = useState(false);
    const canvasRef = useRef(null);

    const addNode = () => {
        const newId = `node${nodes.length}`;
        const newNode = {
            id: newId,
            name: newId,
            code: "",
            flowLevel: nodes.length + 1,
            x: 300 + (nodes.length * 50),
            y: 250 + (nodes.length * 30)
        };
        setNodes([...nodes, newNode]);
        setSelectedNode(newNode);
    };

    const removeNode = (id) => {
        if (id === "start") return;
        setNodes(nodes.filter(node => node.id !== id));
        setConnections(connections.filter(conn => conn.from !== id && conn.to !== id));
        if (selectedNode?.id === id) setSelectedNode(null);
    };

    const updateNode = (id, field, value) => {
        setNodes(nodes.map(node => 
            node.id === id ? { ...node, [field]: value } : node
        ));
        if (selectedNode?.id === id) {
            setSelectedNode({ ...selectedNode, [field]: value });
        }
    };

    const handleMouseDown = (e, node) => {
        if (e.target.closest('.node-action')) return;
        setDraggingNode(node.id);
        setSelectedNode(node);
        const rect = e.currentTarget.getBoundingClientRect();
        setDragOffset({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        });
    };

    const handleMouseMove = useCallback((e) => {
        if (!draggingNode || !canvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left - dragOffset.x;
        const y = e.clientY - rect.top - dragOffset.y;
        
        setNodes(prev => prev.map(node => 
            node.id === draggingNode ? { ...node, x, y } : node
        ));
    }, [draggingNode, dragOffset]);

    const handleMouseUp = useCallback(() => {
        setDraggingNode(null);
    }, []);

    const startConnection = (nodeId) => {
        setConnecting(nodeId);
    };

    const endConnection = (targetId) => {
        if (connecting && connecting !== targetId) {
            const exists = connections.find(c => c.from === connecting && c.to === targetId);
            if (!exists) {
                setConnections([...connections, { from: connecting, to: targetId }]);
            }
        }
        setConnecting(null);
    };

    const removeConnection = (from, to) => {
        setConnections(connections.filter(c => !(c.from === from && c.to === to)));
    };

    const encodeToBase64 = (str) => {
        return btoa(unescape(encodeURIComponent(str)));
    };

    const createPayload = () => {
        const nodesObj = {};
        nodes.forEach(node => {
            nodesObj[node.id] = {
                name: node.name,
                code: encodeToBase64(node.code),
                flow_lvl: node.flowLevel
            };
        });

        let parsedInput = {};
        try {
            parsedInput = JSON.parse(currentInput);
        } catch (e) {
            setError("Invalid JSON in Current Input");
            return null;
        }

        return {
            nodes: nodesObj,
            curr_inp: parsedInput,
            curr_node: {
                name: nodes[0].name,
                code: encodeToBase64(nodes[0].code),
                flow_lvl: nodes[0].flowLevel
            }
        };
    };

    const handleAddFlow = async () => {
        setError("");
        setSuccess("");
        setLoading(true);
        
        const payload = createPayload();
        if (!payload) {
            setLoading(false);
            return;
        }

        try {
            const res = await fetch("/api/fcb/add", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const data = await res.json();
            
            if (data.flow_id) {
                setFlowId(data.flow_id);
                setSuccess("Flow created successfully!");
                setTimeout(() => setActiveTab("tracker"), 800);
            } else {
                setError(data.message || "Failed to create flow");
            }
        } catch (err) {
            setError("Network error: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleGetFlowData = async () => {
        if (!flowId.trim()) {
            setError("Please enter a Flow ID");
            return;
        }

        setError("");
        setSuccess("");
        setLoading(true);
        
        try {
            const res = await fetch(`/api/flow/${flowId}`);
            const data = await res.json();
            setFlowData(data);
            setSuccess("Flow data retrieved successfully!");
        } catch (err) {
            setError("Failed to fetch flow data: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="min-h-screen bg-neutral-50" onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
            <nav className="bg-black text-white">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex justify-between h-14">
                        <div className="flex items-center space-x-8">
                            <div className="flex items-center gap-2">
                                <Box className="w-5 h-5" strokeWidth={2} />
                                <span className="text-lg font-semibold">FlowKit</span>
                            </div>
                            <div className="hidden md:flex items-center space-x-1">
                                <NavLink href="/kv" currentPath={pathname} label="Secret Key" />
                                <NavLink href="/resource" currentPath={pathname} label="Resource Monitor" />
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto py-6 px-6">
                <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
                    <div className="flex border-b border-neutral-200">
                        <TabButton active={activeTab === "builder"} onClick={() => setActiveTab("builder")} label="Builder" />
                        <TabButton active={activeTab === "tracker"} onClick={() => setActiveTab("tracker")} label="Tracker" />
                    </div>

                    {success && (
                        <div className="mx-6 mt-4 p-3 bg-black text-white rounded-lg flex items-center gap-2 text-sm">
                            <CheckCircle className="w-4 h-4" />
                            <span>{success}</span>
                        </div>
                    )}

                    {error && (
                        <div className="mx-6 mt-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center gap-2 text-sm">
                            <AlertCircle className="w-4 h-4" />
                            <span>{error}</span>
                        </div>
                    )}

                    {activeTab === "builder" && (
                        <div className="flex h-[calc(100vh-200px)]">
                            {/* Canvas */}
                            <div className="flex-1 relative bg-neutral-50 overflow-hidden" ref={canvasRef}>
                                <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
                                    {connections.map((conn, i) => {
                                        const fromNode = nodes.find(n => n.id === conn.from);
                                        const toNode = nodes.find(n => n.id === conn.to);
                                        if (!fromNode || !toNode) return null;
                                        
                                        const x1 = fromNode.x + 100;
                                        const y1 = fromNode.y + 40;
                                        const x2 = toNode.x;
                                        const y2 = toNode.y + 40;
                                        const midX = (x1 + x2) / 2;
                                        
                                        return (
                                            <g key={i}>
                                                <path
                                                    d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                                                    stroke="#000"
                                                    strokeWidth="2"
                                                    fill="none"
                                                />
                                                <circle
                                                    cx={(x1 + x2) / 2}
                                                    cy={(y1 + y2) / 2}
                                                    r="8"
                                                    fill="white"
                                                    stroke="#000"
                                                    strokeWidth="2"
                                                    className="cursor-pointer pointer-events-auto"
                                                    onClick={() => removeConnection(conn.from, conn.to)}
                                                />
                                                <line
                                                    x1={(x1 + x2) / 2 - 3}
                                                    y1={(y1 + y2) / 2}
                                                    x2={(x1 + x2) / 2 + 3}
                                                    y2={(y1 + y2) / 2}
                                                    stroke="#000"
                                                    strokeWidth="2"
                                                    className="pointer-events-none"
                                                />
                                            </g>
                                        );
                                    })}
                                    {connecting && (
                                        <line
                                            x1={nodes.find(n => n.id === connecting)?.x + 100}
                                            y1={nodes.find(n => n.id === connecting)?.y + 40}
                                            x2={nodes.find(n => n.id === connecting)?.x + 150}
                                            y2={nodes.find(n => n.id === connecting)?.y + 40}
                                            stroke="#000"
                                            strokeWidth="2"
                                            strokeDasharray="5,5"
                                        />
                                    )}
                                </svg>

                                {/* Grid Pattern */}
                                <div className="absolute inset-0 opacity-20" style={{
                                    backgroundImage: 'radial-gradient(circle, #000 1px, transparent 1px)',
                                    backgroundSize: '20px 20px'
                                }} />

                                {/* Nodes */}
                                {nodes.map(node => (
                                    <div
                                        key={node.id}
                                        className={`absolute bg-white rounded-lg shadow-lg border-2 transition-all cursor-move ${
                                            selectedNode?.id === node.id ? 'border-black ring-2 ring-black ring-offset-2' : 'border-neutral-300 hover:border-neutral-400'
                                        }`}
                                        style={{
                                            left: node.x,
                                            top: node.y,
                                            width: '200px',
                                            zIndex: selectedNode?.id === node.id ? 10 : 2
                                        }}
                                        onMouseDown={(e) => handleMouseDown(e, node)}
                                    >
                                        <div className="p-3 bg-gradient-to-r from-black to-neutral-800 text-white rounded-t-md">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <Zap className="w-4 h-4" />
                                                    <span className="font-semibold text-sm truncate">{node.name}</span>
                                                </div>
                                                {node.id !== "start" && (
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); removeNode(node.id); }}
                                                        className="node-action p-1 hover:bg-white/20 rounded"
                                                    >
                                                        <Trash2 className="w-3 h-3" />
                                                    </button>
                                                )}
                                            </div>
                                            <div className="text-xs text-neutral-300 mt-1">Level {node.flowLevel}</div>
                                        </div>
                                        <div className="p-3">
                                            <div className="text-xs text-neutral-600 mb-2">
                                                {node.code ? `${node.code.split('\n').length} lines of code` : 'No code'}
                                            </div>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setSelectedNode(node); setCodeEditorOpen(true); }}
                                                className="node-action w-full flex items-center justify-center gap-1.5 px-2 py-1.5 bg-black text-white rounded text-xs hover:bg-neutral-800"
                                            >
                                                <Code className="w-3 h-3" />
                                                Edit Code
                                            </button>
                                        </div>

                                        {/* Connection Points */}
                                        <div
                                            className="node-action absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-black border-2 border-white rounded-full cursor-pointer hover:scale-125 transition-transform"
                                            onClick={(e) => { e.stopPropagation(); endConnection(node.id); }}
                                        />
                                        <div
                                            className="node-action absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-black border-2 border-white rounded-full cursor-pointer hover:scale-125 transition-transform"
                                            onClick={(e) => { e.stopPropagation(); startConnection(node.id); }}
                                        />
                                    </div>
                                ))}

                                {/* Toolbar */}
                                <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg border border-neutral-200 p-2 flex gap-2">
                                    <button
                                        onClick={addNode}
                                        className="flex items-center gap-1.5 px-3 py-2 bg-black text-white rounded hover:bg-neutral-800 text-sm"
                                    >
                                        <Plus className="w-4 h-4" />
                                        Add Node
                                    </button>
                                </div>

                                {/* Stats */}
                                <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg border border-neutral-200 p-3 space-y-2">
                                    <div className="flex items-center gap-2 text-sm">
                                        <GitBranch className="w-4 h-4" />
                                        <span className="font-semibold">{nodes.length}</span>
                                        <span className="text-neutral-600">Nodes</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                        <Box className="w-4 h-4" />
                                        <span className="font-semibold">{connections.length}</span>
                                        <span className="text-neutral-600">Connections</span>
                                    </div>
                                </div>
                            </div>

                            {/* Side Panel */}
                            {selectedNode && !codeEditorOpen && (
                                <div className="w-80 border-l border-neutral-200 bg-white p-4 overflow-y-auto">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="font-semibold flex items-center gap-2">
                                            <Settings className="w-4 h-4" />
                                            Node Settings
                                        </h3>
                                        <button onClick={() => setSelectedNode(null)} className="p-1 hover:bg-neutral-100 rounded">
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>

                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-xs font-medium mb-1.5 text-neutral-700">Node Name</label>
                                            <input
                                                type="text"
                                                value={selectedNode.name}
                                                onChange={(e) => updateNode(selectedNode.id, "name", e.target.value)}
                                                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-black focus:border-black text-sm placeholder:text-neutral-500"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-xs font-medium mb-1.5 text-neutral-700">Flow Level</label>
                                            <input
                                                type="number"
                                                value={selectedNode.flowLevel}
                                                onChange={(e) => updateNode(selectedNode.id, "flowLevel", parseInt(e.target.value))}
                                                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-black focus:border-black text-sm"
                                                min="1"
                                            />
                                        </div>

                                        <button
                                            onClick={() => setCodeEditorOpen(true)}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-black text-white rounded-lg hover:bg-neutral-800 text-sm"
                                        >
                                            <Code className="w-4 h-4" />
                                            Open Code Editor
                                        </button>
                                    </div>

                                    <div className="mt-6 pt-6 border-t border-neutral-200">
                                        <label className="block text-xs font-medium mb-2 text-neutral-700">Current Input (JSON)</label>
                                        <textarea
                                            value={currentInput}
                                            onChange={(e) => setCurrentInput(e.target.value)}
                                            className="w-full h-32 px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-black focus:border-black font-mono text-xs resize-none placeholder:text-neutral-500"
                                            placeholder='{"key": "value"}'
                                        />
                                    </div>

                                    <button
                                        onClick={handleAddFlow}
                                        disabled={loading}
                                        className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 bg-black text-white rounded-lg hover:bg-neutral-800 disabled:bg-neutral-400 text-sm font-medium"
                                    >
                                        {loading ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                                Processing...
                                            </>
                                        ) : (
                                            <>
                                                <Play className="w-4 h-4" />
                                                Execute Flow
                                            </>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "tracker" && (
                        <div className="p-6">
                            <div className="mb-6">
                                <h2 className="text-xl font-semibold mb-1">Track Flow</h2>
                                <p className="text-sm text-neutral-600">Monitor your flow execution</p>
                            </div>

                            <div className="mb-6">
                                <label className="block text-sm font-medium mb-2">Flow ID</label>
                                <div className="flex gap-2">
                                    <div className="flex-1 relative">
                                        <input
                                            type="text"
                                            value={flowId}
                                            onChange={(e) => setFlowId(e.target.value)}
                                            className="w-full px-3 py-2 pr-10 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-black focus:border-black font-mono text-sm placeholder:text-neutral-500"
                                            placeholder="d51e109a-3dc2-43b3-aa2e-421772c62ea7"
                                        />
                                        {flowId && (
                                            <button
                                                onClick={() => copyToClipboard(flowId)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-neutral-100 rounded"
                                            >
                                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                            </button>
                                        )}
                                    </div>
                                    <button
                                        onClick={handleGetFlowData}
                                        disabled={loading}
                                        className="flex items-center gap-1.5 px-4 py-2 bg-black text-white rounded-lg hover:bg-neutral-800 disabled:bg-neutral-400 text-sm font-medium"
                                    >
                                        {loading ? (
                                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                        ) : (
                                            <>
                                                <Search className="w-4 h-4" />
                                                Track
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {flowData && <FlowDataDisplay data={flowData} />}

                            {!flowData && !loading && (
                                <div className="text-center py-16 bg-neutral-50 rounded-lg">
                                    <Eye className="w-10 h-10 text-neutral-400 mx-auto mb-3" />
                                    <p className="text-sm text-neutral-600">Enter a Flow ID to view data</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Code Editor Modal */}
            {codeEditorOpen && selectedNode && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-6">
                    <div className="bg-neutral-900 rounded-xl shadow-2xl w-full max-w-7xl h-[95vh] flex flex-col">
                        <div className="flex items-center justify-between p-5 border-b border-neutral-700">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-neutral-800 rounded-lg">
                                    <Code className="w-6 h-6 text-green-400" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-white text-lg">Python Code Editor</h3>
                                    <p className="text-sm text-neutral-400">{selectedNode.name}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setCodeEditorOpen(false)}
                                className="p-2 hover:bg-neutral-800 rounded-lg text-neutral-400 hover:text-white transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        
                        <div className="flex-1 p-6 overflow-hidden">
                            <div className="relative h-full bg-neutral-950 rounded-lg border border-neutral-800 overflow-hidden">
                                {/* Line Numbers */}
                                <div className="absolute left-0 top-0 bottom-0 w-16 bg-neutral-900 border-r border-neutral-800 py-4 text-right pr-3 text-sm text-neutral-500 font-mono select-none overflow-hidden">
                                    {selectedNode.code.split('\n').map((_, i) => (
                                        <div key={i} className="leading-7">{i + 1}</div>
                                    ))}
                                    {!selectedNode.code && <div className="leading-7">1</div>}
                                </div>
                                
                                {/* Code Area */}
                                <textarea
                                    value={selectedNode.code}
                                    onChange={(e) => updateNode(selectedNode.id, "code", e.target.value)}
                                    className="w-full h-full pl-20 pr-6 py-4 bg-transparent text-green-400 font-mono text-base resize-none placeholder:text-neutral-600 focus:outline-none leading-7"
                                    placeholder="# Write your Python code here&#x0a;# Example:&#x0a;def process(input_data):&#x0a;    result = input_data.get('value', 0) * 2&#x0a;    return {'result': result}"
                                    spellCheck="false"
                                    style={{ tabSize: 4 }}
                                />
                            </div>
                        </div>
                        
                        <div className="p-5 border-t border-neutral-700 flex justify-between items-center bg-neutral-900">
                            <div className="flex items-center gap-6 text-sm text-neutral-400">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                    <span>Python</span>
                                </div>
                                <div>
                                    {selectedNode.code.split('\n').length} lines
                                </div>
                                <div>
                                    {selectedNode.code.length} characters
                                </div>
                            </div>
                            <button
                                onClick={() => setCodeEditorOpen(false)}
                                className="px-6 py-2.5 bg-green-500 text-black font-medium rounded-lg hover:bg-green-400 transition-colors text-sm"
                            >
                                Save & Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function FlowDataDisplay({ data }) {
    const [copied, setCopied] = useState(false);

    const copyData = () => {
        navigator.clipboard.writeText(JSON.stringify(data, null, 2));
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="border border-neutral-200 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between p-3 bg-neutral-50">
                <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <h3 className="text-sm font-semibold">Flow Data</h3>
                </div>
                <button
                    onClick={copyData}
                    className="flex items-center gap-1.5 px-2 py-1 bg-black text-white rounded text-xs hover:bg-neutral-800"
                >
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied ? "Copied" : "Copy"}
                </button>
            </div>
            <div className="p-3">
                <pre className="bg-neutral-900 text-green-400 p-4 rounded overflow-auto max-h-96 text-xs font-mono">
{JSON.stringify(data, null, 2)}
                </pre>
            </div>
        </div>
    );
}

function NavLink({ href, currentPath, label }) {
    const isActive = currentPath === href;
    return (
        <Link
            href={href}
            className={`px-3 py-2 text-sm font-medium rounded transition-colors ${
                isActive ? "text-white bg-neutral-800" : "text-neutral-400 hover:text-white"
            }`}
        >
            {label}
        </Link>
    );
}

function TabButton({ active, onClick, label }) {
    return (
        <button
            onClick={onClick}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                active
                    ? "text-black bg-white border-b-2 border-black"
                    : "text-neutral-600 hover:text-black"
            }`}
        >
            {label}
        </button>
    );
}
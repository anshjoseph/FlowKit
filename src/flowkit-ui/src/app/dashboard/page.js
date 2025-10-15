"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, Plus, Trash2, Play, Search, Eye, ChevronDown, ChevronRight, AlertCircle, CheckCircle, Copy, Check } from "lucide-react";

export default function Dashboard() {
    const pathname = usePathname();
    const [activeTab, setActiveTab] = useState("builder");
    const [nodes, setNodes] = useState([
        { id: "start", name: "start", code: "", flowLevel: 1 }
    ]);
    const [currentInput, setCurrentInput] = useState("{}");
    const [flowId, setFlowId] = useState("");
    const [flowData, setFlowData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [copied, setCopied] = useState(false);

    const addNode = () => {
        const newId = `node${nodes.length}`;
        setNodes([...nodes, {
            id: newId,
            name: newId,
            code: "",
            flowLevel: nodes.length + 1
        }]);
    };

    const removeNode = (id) => {
        if (id === "start") return;
        setNodes(nodes.filter(node => node.id !== id));
    };

    const updateNode = (id, field, value) => {
        setNodes(nodes.map(node => 
            node.id === id ? { ...node, [field]: value } : node
        ));
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
        <div className="min-h-screen bg-white">
            {/* Navigation */}
            <nav className="bg-black text-white">
                <div className="max-w-6xl mx-auto px-6">
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

            {/* Main Content */}
            <div className="max-w-6xl mx-auto py-8 px-6">
                {/* Tab Navigation */}
                <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden mb-6">
                    <div className="flex border-b border-neutral-200">
                        <TabButton
                            active={activeTab === "builder"}
                            onClick={() => setActiveTab("builder")}
                            label="Builder"
                        />
                        <TabButton
                            active={activeTab === "tracker"}
                            onClick={() => setActiveTab("tracker")}
                            label="Tracker"
                        />
                    </div>

                    {/* Notifications */}
                    {success && (
                        <div className="mx-6 mt-6 p-3 bg-black text-white rounded-lg flex items-center gap-2 text-sm">
                            <CheckCircle className="w-4 h-4" />
                            <span>{success}</span>
                        </div>
                    )}

                    {error && (
                        <div className="mx-6 mt-6 p-3 bg-neutral-900 text-white rounded-lg flex items-center gap-2 text-sm">
                            <AlertCircle className="w-4 h-4" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Builder Tab */}
                    {activeTab === "builder" && (
                        <div className="p-6">
                            <div className="mb-6">
                                <h2 className="text-xl font-semibold mb-1 text-neutral-900">Create Flow</h2>
                                <p className="text-sm text-neutral-600">Define nodes and execute your flow</p>
                            </div>

                            {/* Stats */}
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="bg-black text-white p-4 rounded-lg">
                                    <div className="text-2xl font-semibold">{nodes.length}</div>
                                    <div className="text-xs text-neutral-300">Nodes</div>
                                </div>
                                <div className="bg-black text-white p-4 rounded-lg">
                                    <div className="text-2xl font-semibold">{Math.max(...nodes.map(n => n.flowLevel))}</div>
                                    <div className="text-xs text-neutral-300">Levels</div>
                                </div>
                                <div className="bg-black text-white p-4 rounded-lg">
                                    <div className="text-2xl font-semibold">Ready</div>
                                    <div className="text-xs text-neutral-300">Status</div>
                                </div>
                            </div>

                            {/* Nodes */}
                            <div className="mb-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-sm font-semibold text-neutral-900">Nodes</h3>
                                    <button
                                        onClick={addNode}
                                        className="flex items-center gap-1.5 px-3 py-1.5 bg-black text-white rounded-lg hover:bg-neutral-800 transition-colors text-sm"
                                    >
                                        <Plus className="w-4 h-4" />
                                        Add
                                    </button>
                                </div>

                                <div className="space-y-3">
                                    {nodes.map((node, index) => (
                                        <NodeCard
                                            key={node.id}
                                            node={node}
                                            index={index}
                                            onUpdate={updateNode}
                                            onRemove={removeNode}
                                            canRemove={node.id !== "start"}
                                        />
                                    ))}
                                </div>
                            </div>

                            {/* Input */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium mb-2 text-neutral-900">Current Input (JSON)</label>
                                <textarea
                                    value={currentInput}
                                    onChange={(e) => setCurrentInput(e.target.value)}
                                    className="w-full h-24 px-3 py-2 border border-neutral-300 rounded-lg focus:ring-1 focus:ring-black focus:border-black transition-colors font-mono text-sm resize-none text-neutral-900 bg-white placeholder:text-neutral-400"
                                    placeholder='{"key": "value"}'
                                />
                            </div>

                            {/* Submit */}
                            <button
                                onClick={handleAddFlow}
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-black text-white rounded-lg hover:bg-neutral-800 transition-colors disabled:bg-neutral-400 text-sm font-medium"
                            >
                                {loading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        <Play className="w-4 h-4" />
                                        Create & Execute Flow
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Tracker Tab */}
                    {activeTab === "tracker" && (
                        <div className="p-6">
                            <div className="mb-6">
                                <h2 className="text-xl font-semibold mb-1 text-neutral-900">Track Flow</h2>
                                <p className="text-sm text-neutral-600">Monitor your flow execution</p>
                            </div>

                            {/* Flow ID Input */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium mb-2 text-neutral-900">Flow ID</label>
                                <div className="flex gap-2">
                                    <div className="flex-1 relative">
                                        <input
                                            type="text"
                                            value={flowId}
                                            onChange={(e) => setFlowId(e.target.value)}
                                            className="w-full px-3 py-2 pr-10 border border-neutral-300 rounded-lg focus:ring-1 focus:ring-black focus:border-black transition-colors font-mono text-sm text-neutral-900 bg-white placeholder:text-neutral-400"
                                            placeholder="d51e109a-3dc2-43b3-aa2e-421772c62ea7"
                                        />
                                        {flowId && (
                                            <button
                                                onClick={() => copyToClipboard(flowId)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-neutral-100 rounded transition-colors"
                                            >
                                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                            </button>
                                        )}
                                    </div>
                                    <button
                                        onClick={handleGetFlowData}
                                        disabled={loading}
                                        className="flex items-center gap-1.5 px-4 py-2 bg-black text-white rounded-lg hover:bg-neutral-800 transition-colors disabled:bg-neutral-400 text-sm font-medium"
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

                            {/* Flow Data */}
                            {flowData && <FlowDataDisplay data={flowData} />}

                            {!flowData && !loading && (
                                <div className="text-center py-12 bg-neutral-50 rounded-lg">
                                    <Eye className="w-8 h-8 text-neutral-400 mx-auto mb-2" />
                                    <p className="text-sm text-neutral-600">Enter a Flow ID to view data</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function NodeCard({ node, index, onUpdate, onRemove, canRemove }) {
    const [expanded, setExpanded] = useState(true);

    return (
        <div className="border border-neutral-200 rounded-lg overflow-hidden hover:border-neutral-400 transition-colors">
            <div className="flex items-center justify-between p-3 bg-neutral-50">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="p-1 hover:bg-neutral-200 rounded transition-colors"
                    >
                        {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                    <div className="w-6 h-6 bg-black text-white rounded flex items-center justify-center text-xs font-semibold">
                        {index + 1}
                    </div>
                    <span className="text-sm font-medium">{node.name}</span>
                    <span className="text-xs text-neutral-500">Level {node.flowLevel}</span>
                </div>
                {canRemove && (
                    <button
                        onClick={() => onRemove(node.id)}
                        className="p-1 text-neutral-400 hover:text-black transition-colors"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                )}
            </div>

            {expanded && (
                <div className="p-3 space-y-3 bg-white">
                    <div>
                        <label className="block text-xs font-medium mb-1 text-neutral-900">Node Name</label>
                        <input
                            type="text"
                            value={node.name}
                            onChange={(e) => onUpdate(node.id, "name", e.target.value)}
                            className="w-full px-2 py-1.5 border border-neutral-300 rounded focus:ring-1 focus:ring-black focus:border-black transition-colors text-sm text-neutral-900 bg-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium mb-1 text-neutral-900">Flow Level</label>
                        <input
                            type="number"
                            value={node.flowLevel}
                            onChange={(e) => onUpdate(node.id, "flowLevel", parseInt(e.target.value))}
                            className="w-full px-2 py-1.5 border border-neutral-300 rounded focus:ring-1 focus:ring-black focus:border-black transition-colors text-sm text-neutral-900 bg-white"
                            min="1"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium mb-1 text-neutral-900">Python Code</label>
                        <textarea
                            value={node.code}
                            onChange={(e) => onUpdate(node.id, "code", e.target.value)}
                            className="w-full h-32 px-2 py-1.5 border border-neutral-300 rounded focus:ring-1 focus:ring-black focus:border-black transition-colors font-mono text-sm resize-none text-neutral-900 bg-white placeholder:text-neutral-400"
                            placeholder="# Enter Python code"
                        />
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
                    className="flex items-center gap-1.5 px-2 py-1 bg-black text-white rounded text-xs hover:bg-neutral-800 transition-colors"
                >
                    {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copied ? "Copied" : "Copy"}
                </button>
            </div>
            <div className="p-3">
                <pre className="bg-neutral-900 text-green-400 p-3 rounded overflow-auto max-h-80 text-xs font-mono">
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
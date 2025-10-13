"use client";
import React, { useEffect, useState } from "react";
import { Box, Key, Plus, RefreshCw, Trash2, Eye, Search, Shield, Lock, Copy } from "lucide-react";

export default function SecretManager() {
  const [keys, setKeys] = useState([]);
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedKey, setSelectedKey] = useState(null);

  const showNotification = (message) => {
    setNotification(message);
    setTimeout(() => setNotification(""), 3000);
  };

  const fetchKeys = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/kv");
      if (!res.ok) throw new Error("Failed to fetch keys");
      const data = await res.json();
      setKeys(Array.isArray(data) ? data : data.keys || []);
    } catch (err) {
      showNotification("Failed to load keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchKeys(); }, []);

  const handleSet = async () => {
    if (!key.trim() || !value.trim()) {
      showNotification("Please enter both key and value");
      return;
    }

    try {
      setLoading(true);
      const res = await fetch("/api/kv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: key.trim(), value: value.trim() }),
      });

      if (!res.ok) throw new Error("Failed to set value");
      
      setKey("");
      setValue("");
      showNotification("Secret saved successfully!");
      fetchKeys();
    } catch (err) {
      showNotification(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGet = async (k) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/kv?key=${encodeURIComponent(k)}`);
      if (!res.ok) throw new Error("Failed to get value");
      const data = await res.json();
      setOutput(data);
      setSelectedKey(k);
      showNotification(`Retrieved value for ${k}`);
    } catch (err) {
      showNotification("Failed to get value");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (k) => {
    if (!confirm(`Are you sure you want to delete "${k}"?`)) return;
    
    try {
      setLoading(true);
      const res = await fetch(`/api/kv?key=${encodeURIComponent(k)}`, {
        method: "DELETE"
      });
      if (!res.ok) throw new Error("Failed to delete key");
      showNotification(`"${k}" deleted successfully`);
      setSelectedKey(null);
      setOutput(null);
      fetchKeys();
    } catch (err) {
      showNotification("Failed to delete key");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && key && value) handleSet();
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    showNotification("Copied to clipboard!");
  };

  const filteredKeys = keys.filter(k => 
    k.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800">Secret Vault</h1>
              <p className="text-sm text-slate-600">Secure key management</p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-slate-200">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search keys..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-slate-900"
            />
          </div>
        </div>

        {/* Keys List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                Keys ({filteredKeys.length})
              </h2>
              <button
                onClick={fetchKeys}
                disabled={loading}
                className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>

            {loading && keys.length === 0 ? (
              <div className="text-center py-8">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-slate-400" />
                <p className="text-sm text-slate-600">Loading secrets...</p>
              </div>
            ) : filteredKeys.length === 0 ? (
              <div className="text-center py-8">
                <Key className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm text-slate-600">No secrets found</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredKeys.map((k) => (
                  <div
                    key={k}
                    className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                      selectedKey === k 
                        ? "bg-blue-50 border border-blue-200" 
                        : "hover:bg-slate-50 border border-transparent"
                    }`}
                    onClick={() => handleGet(k)}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <Lock className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="font-mono text-sm text-slate-800 truncate">
                        {k}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(k);
                      }}
                      className="p-1 text-slate-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0 ml-2"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white border-b border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-800">
                {selectedKey ? `Key: ${selectedKey}` : "Secret Manager"}
              </h2>
              <p className="text-slate-600">
                {selectedKey ? "View and manage this secret" : "Add and manage your secrets securely"}
              </p>
            </div>
            {selectedKey && (
              <button
                onClick={() => handleDelete(selectedKey)}
                disabled={loading}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete Key
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Add Secret Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Plus className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">Add New Secret</h3>
                  <p className="text-sm text-slate-600">Create a new key-value pair</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Key Name
                  </label>
                  <input
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-slate-900"
                    placeholder="Enter unique key name"
                    value={key}
                    onChange={(e) => setKey(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Secret Value
                  </label>
                  <textarea
                    rows={4}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-slate-900 resize-none"
                    placeholder="Enter secret value"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <button
                  onClick={handleSet}
                  disabled={loading || !key.trim() || !value.trim()}
                  className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  {loading ? "Saving..." : "Add Secret"}
                </button>
              </div>
            </div>

            {/* Output Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Eye className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800">Secret Details</h3>
                    <p className="text-sm text-slate-600">
                      {selectedKey ? `Viewing: ${selectedKey}` : "Select a key to view details"}
                    </p>
                  </div>
                </div>
                {output && (
                  <button
                    onClick={() => handleDelete(selectedKey)}
                    disabled={loading}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white font-medium rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                )}
              </div>

              {output ? (
                <div className="space-y-4">
                  <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-slate-700">Key-Value Pair:</span>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(output, null, 2))}
                        className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    <pre className="text-sm text-slate-800 font-mono overflow-x-auto bg-white p-3 rounded border">
                      {JSON.stringify(output, null, 2)}
                    </pre>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => copyToClipboard(output.value)}
                      className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
                    >
                      <Copy className="w-4 h-4" />
                      Copy Value
                    </button>
                    <button
                      onClick={() => {
                        setOutput(null);
                        setSelectedKey(null);
                      }}
                      className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                  <Eye className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-slate-600">No secret selected</p>
                  <p className="text-sm text-slate-500 mt-1">Choose a key from the sidebar to view its value</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <div className="fixed top-4 right-4 bg-slate-800 text-white px-6 py-3 rounded-lg shadow-lg transform animate-in slide-in-from-right-4">
          {notification}
        </div>
      )}
    </div>
  );
}
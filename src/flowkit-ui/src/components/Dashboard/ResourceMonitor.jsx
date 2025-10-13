"use client";
import React, { useEffect, useState, useCallback } from "react";

function ResourceMonitor() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  const fetchResources = useCallback(async () => {
    try {
      const res = await fetch("/api/resource");
      const data = await res.json();
      setResources(data.npus || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Error fetching resources:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResources();

    if (autoRefresh) {
      const interval = setInterval(fetchResources, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchResources]);

  const handleRefresh = () => {
    setLoading(true);
    fetchResources();
  };

  const formatUptime = (seconds) => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(0)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "idle":
        return "bg-black text-white border-black";
      case "active":
        return "bg-white text-black border-2 border-black";
      case "error":
        return "bg-gray-900 text-white border-gray-900";
      default:
        return "bg-gray-100 text-black border-gray-200";
    }
  };

  const getHealthColor = (failedTasks) => {
    if (failedTasks === 0) return "bg-green-500";
    if (failedTasks < 5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getHealthText = (failedTasks) => {
    if (failedTasks === 0) return "Excellent";
    if (failedTasks < 5) return "Good";
    return "Needs Attention";
  };

  return (
    <div className="min-h-screen bg-white text-black">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-3 h-8 bg-black rounded-sm"></div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Resource Monitor</h1>
                {lastUpdated && (
                  <p className="text-sm text-gray-600 mt-1">
                    Last updated: {lastUpdated.toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
            
            {/* Controls */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">Auto-refresh</label>
                <div className="relative inline-block w-12 h-6">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`block w-12 h-6 rounded-full transition-colors ${
                    autoRefresh ? 'bg-black' : 'bg-gray-300'
                  }`}></div>
                  <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${
                    autoRefresh ? 'transform translate-x-6' : ''
                  }`}></div>
                </div>
              </div>
              
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!autoRefresh}
              >
                <option value={2000}>2 seconds</option>
                <option value={5000}>5 seconds</option>
                <option value={10000}>10 seconds</option>
                <option value={30000}>30 seconds</option>
              </select>
              
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="bg-black text-white px-4 py-2 rounded-lg hover:bg-gray-800 active:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors flex items-center gap-2 min-w-[120px] justify-center"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Refreshing...
                  </>
                ) : (
                  "Refresh Now"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Loading State */}
        {loading && resources.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-black border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-lg font-medium">Loading resources...</p>
            <p className="text-gray-600 mt-2">Fetching NPU node information</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && resources.length === 0 && (
          <div className="text-center py-20 border-2 border-dashed border-gray-300 rounded-2xl bg-gray-50">
            <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No NPU nodes available</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              NPU resources will appear here when they become available. Check your configuration and try refreshing.
            </p>
          </div>
        )}

        {/* Resources Grid */}
        {!loading && resources.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {resources.map((npu) => (
              <div
                key={npu.id}
                className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all duration-300 group hover:border-gray-300"
              >
                {/* Card Header */}
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="font-bold text-lg text-gray-900 group-hover:text-black">NPU Node</h3>
                    <p className="text-sm text-gray-600 font-mono mt-1 bg-gray-50 px-2 py-1 rounded border">
                      {npu.id}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold capitalize border ${getStatusColor(
                      npu.status
                    )}`}
                  >
                    {npu.status}
                  </span>
                </div>

                {/* Address */}
                <div className="mb-6">
                  <p className="text-sm font-medium text-gray-700 mb-2">Address</p>
                  <p className="font-mono text-sm bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 break-all">
                    {npu.address}
                  </p>
                </div>

                {/* Metrics Grid */}
                <div className="border-t border-gray-200 pt-6">
                  <h4 className="font-bold text-gray-900 mb-4">Performance Metrics</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-4 border border-gray-200 rounded-lg bg-white">
                      <p className="text-2xl font-bold text-gray-900">{formatUptime(npu.metrics.uptime)}</p>
                      <p className="text-gray-600 text-xs font-medium mt-1">Uptime</p>
                    </div>
                    <div className="text-center p-4 border border-gray-200 rounded-lg bg-white">
                      <p className="text-2xl font-bold text-gray-900">{npu.metrics.queued_tasks}</p>
                      <p className="text-gray-600 text-xs font-medium mt-1">Queued</p>
                    </div>
                    <div className="text-center p-4 border border-gray-200 rounded-lg bg-white">
                      <p className="text-2xl font-bold text-green-600">{npu.metrics.successful_tasks}</p>
                      <p className="text-gray-600 text-xs font-medium mt-1">Success</p>
                    </div>
                    <div className="text-center p-4 border border-gray-200 rounded-lg bg-white">
                      <p className="text-2xl font-bold text-red-600">{npu.metrics.failed_tasks}</p>
                      <p className="text-gray-600 text-xs font-medium mt-1">Failed</p>
                    </div>
                  </div>
                </div>

                {/* Health Indicator */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Health Status</span>
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-3 h-3 rounded-full ${getHealthColor(npu.metrics.failed_tasks)}`}
                      ></div>
                      <span className="text-sm font-medium text-gray-900">
                        {getHealthText(npu.metrics.failed_tasks)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer Info */}
        {!loading && resources.length > 0 && (
          <div className="mt-12 text-center">
            <div className="inline-flex items-center gap-4 px-6 py-3 bg-gray-50 border border-gray-200 rounded-2xl">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <p className="text-sm text-gray-700">
                Monitoring <span className="font-semibold text-black">{resources.length}</span> NPU 
                node{resources.length !== 1 ? 's' : ''} in real-time
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ResourceMonitor;
/**
 * pages/SystemHealthPage.jsx — Phase 1/16 — operational dashboard
 */
import React, { useEffect, useState } from 'react'
import { Activity, Database, Cpu, Server, CheckCircle2, XCircle, Loader2, RefreshCw } from 'lucide-react'
import { healthAPI } from '../api/services'
import apiClient from '../api/client'
import { useTitle } from '../hooks/index'

export default function SystemHealthPage() {
  useTitle('System Health')
  const [health, setHealth] = useState(null)
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const [h, o] = await Promise.all([
      healthAPI.check().catch(e => e.response),
      apiClient.get('/api/admin/system-overview').catch(() => null),
    ])
    setHealth(h?.data)
    setOverview(o?.data?.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const ServiceCard = ({ name, icon: Icon, status }) => {
    const isHealthy = status?.status === 'healthy'
    return (
      <div className="card p-5">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Icon className="w-4 h-4 text-primary-500" />
            <span className="font-medium text-sm text-gray-900 dark:text-white capitalize">{name}</span>
          </div>
          {isHealthy ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
        </div>
        <span className={isHealthy ? 'badge-success' : 'badge-danger'}>{status?.status || 'unknown'}</span>
        {status?.error && <p className="text-2xs text-red-500 mt-2">{status.error}</p>}
        {status?.available_models && (
          <p className="text-2xs text-gray-400 mt-2">Models: {status.available_models.join(', ') || 'none pulled'}</p>
        )}
        {status?.total_documents != null && <p className="text-2xs text-gray-400 mt-2">{status.total_documents} vectors stored</p>}
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">System Health</h1>
          <p className="page-subtitle">Live status of all platform services</p>
        </div>
        <button onClick={load} className="btn-secondary btn-sm"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <ServiceCard name="MongoDB" icon={Database} status={health?.services?.mongodb} />
            <ServiceCard name="ChromaDB" icon={Server} status={health?.services?.chromadb} />
            <ServiceCard name={`AI (${health?.services?.llm?.provider || 'LLM'})`} icon={Cpu} status={health?.services?.llm} />
          </div>

          {overview?.mongodb_collections && (
            <div className="card p-5">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary-500" /> Collection Sizes
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(overview.mongodb_collections).map(([name, count]) => (
                  <div key={name} className="bg-gray-50 dark:bg-dark-700 rounded-lg p-3">
                    <p className="text-xs text-gray-400 capitalize">{name}</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">{count}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

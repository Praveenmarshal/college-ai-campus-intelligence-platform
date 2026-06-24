/**
 * pages/ChatHistoryPage.jsx — Phase 3
 */
import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Trash2, Bot, Loader2 } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { useTitle } from '../hooks/index'
import { timeAgo } from '../utils/helpers'

export default function ChatHistoryPage() {
  useTitle('Chat History')
  const { sessions, loadSessions, loadSession, deleteSession } = useChat()
  const navigate = useNavigate()
  const [loading, setLoading] = React.useState(true)

  useEffect(() => {
    loadSessions().finally(() => setLoading(false))
  }, [])

  const openSession = async (id) => {
    await loadSession(id)
    navigate('/chat')
  }

  return (
    <div className="page-container max-w-3xl">
      <div className="page-header">
        <h1 className="page-title">Chat History</h1>
        <p className="page-subtitle">Your previous conversations with the AI assistant</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading…
        </div>
      ) : sessions.length === 0 ? (
        <div className="card p-12 flex flex-col items-center text-center gap-3">
          <MessageSquare className="w-10 h-10 text-gray-300" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">No conversations yet</p>
          <button onClick={() => navigate('/chat')} className="btn-primary btn-sm mt-2">Start chatting</button>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map(s => (
            <div key={s.id} onClick={() => openSession(s.id)}
              className="card-hover p-4 flex items-center gap-3 cursor-pointer">
              <div className="w-9 h-9 rounded-lg bg-primary-100 dark:bg-primary-900 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{s.title}</p>
                <p className="text-xs text-gray-400 truncate mt-0.5">{s.last_message}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-gray-400">{timeAgo(s.updated_at)}</p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); deleteSession(s.id) }}
                className="btn-ghost p-1.5 hover:text-red-500 shrink-0">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

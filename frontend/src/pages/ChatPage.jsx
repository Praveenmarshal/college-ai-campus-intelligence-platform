/**
 * pages/ChatPage.jsx — Phase 3 full implementation
 * RAG-powered conversational AI chat interface.
 */
import React, { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Send, Loader2, FileText, Sparkles, Plus, Bot, User as UserIcon } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChat } from '../context/ChatContext'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/index'
import { timeAgo } from '../utils/helpers'

const SUGGESTIONS = [
  'What is the attendance policy?',
  'Summarize the placement brochure',
  "What's in the latest exam syllabus?",
  'How many companies visited last year?',
]

export default function ChatPage() {
  useTitle('AI Chat')
  const { messages, isLoading, sendMessage, newChat } = useChat()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const [input, setInput] = useState(searchParams.get('q') || '')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    const q = searchParams.get('q')
    if (q) handleSend(q)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSend = async (overrideText) => {
    const text = (overrideText ?? input).trim()
    if (!text || isLoading) return
    setInput('')
    await sendMessage(text)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-100 dark:border-dark-600 bg-white dark:bg-dark-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-sm">Campus AI Assistant</span>
          <span className="badge-neutral text-2xs">Qwen 3 · Local</span>
        </div>
        <button onClick={newChat} className="btn-ghost btn-sm">
          <Plus className="w-3.5 h-3.5" /> New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-100 to-accent-100 dark:from-primary-950 dark:to-accent-950 flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-primary-500" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              Hi {user?.name?.split(' ')[0]}, ask me anything
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              I can answer questions about uploaded documents, attendance, placements, and more.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => handleSend(s)}
                  className="text-left text-sm px-4 py-3 rounded-xl border border-gray-100 dark:border-dark-600 hover:border-primary-300 dark:hover:border-primary-700 hover:bg-primary-50/50 dark:hover:bg-primary-950/30 transition-colors text-gray-600 dark:text-gray-300">
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map((m, i) => (
              <MessageBubble key={i} message={m} userName={user?.name} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 mr-auto">
                <div className="w-7 h-7 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="chat-bubble-ai flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span className="text-xs text-gray-400">Thinking…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 dark:border-dark-600 bg-white dark:bg-dark-800 px-4 sm:px-8 py-4">
        <div className="max-w-3xl mx-auto flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about documents, attendance, placements…"
            rows={1}
            className="input resize-none flex-1 py-2.5"
            style={{ maxHeight: '120px' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="btn-primary p-2.5 rounded-xl shrink-0"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-2xs text-gray-400 text-center mt-2">
          AI responses are generated by a local model and may be inaccurate. Verify important information.
        </p>
      </div>
    </div>
  )
}

function MessageBubble({ message, userName }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${isUser ? 'bg-gradient-to-br from-primary-400 to-accent-500' : 'bg-primary-100 dark:bg-primary-900'}`}>
        {isUser
          ? <span className="text-2xs font-bold text-white">{userName?.charAt(0)?.toUpperCase()}</span>
          : <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />}
      </div>
      <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-ai'}>
        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-pre:my-2">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>
        {message.sources?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100 dark:border-dark-600 flex flex-wrap gap-1.5">
            {message.sources.map((s, idx) => (
              <span key={idx} className="inline-flex items-center gap-1 text-2xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-dark-600 text-gray-600 dark:text-gray-300">
                <FileText className="w-2.5 h-2.5" /> {s.filename}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

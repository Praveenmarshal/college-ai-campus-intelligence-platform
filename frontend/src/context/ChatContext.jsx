/**
 * context/ChatContext.jsx
 * Manages active chat session, message history, and streaming state.
 */

import React, { createContext, useContext, useState, useCallback } from 'react'
import { chatAPI } from '../api/services'
import toast from 'react-hot-toast'

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [sessions, setSessions]         = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages]         = useState([])
  const [isLoading, setIsLoading]       = useState(false)
  const [isStreaming, setIsStreaming]   = useState(false)

  // Send a message and append response
  const sendMessage = useCallback(async (content, sessionId = null) => {
    const userMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const { data } = await chatAPI.sendMessage({
        message: content,
        session_id: sessionId || activeSession?.id,
      })

      const aiMessage = {
        role: 'assistant',
        content: data.data.response,
        sources: data.data.sources || [],
        agent_used: data.data.agent_used,
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, aiMessage])

      // Update active session ID if new
      if (data.data.session_id && !activeSession) {
        setActiveSession({ id: data.data.session_id })
      }

      return aiMessage
    } catch (err) {
      const errMsg = err?.response?.data?.error || 'Failed to get response'
      toast.error(errMsg)
      setMessages((prev) => prev.slice(0, -1)) // Remove optimistic user msg
    } finally {
      setIsLoading(false)
    }
  }, [activeSession])

  const loadSession = useCallback(async (sessionId) => {
    try {
      const { data } = await chatAPI.getSession(sessionId)
      setActiveSession(data.data)
      setMessages(data.data.messages || [])
    } catch (err) {
      toast.error('Failed to load chat session')
    }
  }, [])

  const newChat = useCallback(() => {
    setActiveSession(null)
    setMessages([])
  }, [])

  const loadSessions = useCallback(async () => {
    try {
      const { data } = await chatAPI.getSessions()
      setSessions(data.data || [])
    } catch { /* silent */ }
  }, [])

  const deleteSession = useCallback(async (sessionId) => {
    try {
      await chatAPI.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (activeSession?.id === sessionId) newChat()
      toast.success('Chat deleted')
    } catch {
      toast.error('Failed to delete chat')
    }
  }, [activeSession, newChat])

  return (
    <ChatContext.Provider
      value={{
        sessions,
        activeSession,
        messages,
        isLoading,
        isStreaming,
        sendMessage,
        loadSession,
        loadSessions,
        newChat,
        deleteSession,
        setMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}

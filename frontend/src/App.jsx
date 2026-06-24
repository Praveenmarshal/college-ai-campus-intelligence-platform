import React, { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { ChatProvider } from './context/ChatContext'
import ProtectedRoute from './routes/ProtectedRoute'
import RoleRoute from './routes/RoleRoute'
import AppLayout from './components/layout/AppLayout'

// Pages — lazy loaded for performance
import {
  LoginPage,
  RegisterPage,
  DashboardPage,
  ChatPage,
  ChatHistoryPage,
  ProfilePage,
  SettingsPage,
  StudentPage,
  FacultyPage,
  AdminPage,
  UploadPDFPage,
  UploadExcelPage,
  UploadCSVPage,
  DocumentsPage,
  UsersPage,
  AnalyticsPage,
  ReportsPage,
  NotificationsPage,
  SystemHealthPage,
  ResumeAnalyzerPage,
  QuestionPaperPage,
  AttendancePage,
  PlacementsPage,
  AcademicAnalyticsPage,
  TimetablePage,
  CalendarPage,
  LibraryPage,
  HostelPage,
  EventsPage,
  NotFoundPage,
} from './pages'

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ChatProvider>
          <AppRoutes />
        </ChatProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected routes — require login */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>

          {/* Common */}
          <Route path="/dashboard"      element={<DashboardPage />} />
          <Route path="/chat"           element={<ChatPage />} />
          <Route path="/chat-history"   element={<ChatHistoryPage />} />
          <Route path="/profile"        element={<ProfilePage />} />
          <Route path="/settings"       element={<SettingsPage />} />
          <Route path="/notifications"  element={<NotificationsPage />} />

          {/* Features */}
          <Route path="/resume-analyzer"        element={<ResumeAnalyzerPage />} />
          <Route path="/question-paper-analyzer" element={<QuestionPaperPage />} />
          <Route path="/attendance"             element={<AttendancePage />} />
          <Route path="/placements"             element={<PlacementsPage />} />
          <Route path="/academic-analytics"     element={<AcademicAnalyticsPage />} />
          <Route path="/timetable"              element={<TimetablePage />} />
          <Route path="/calendar"               element={<CalendarPage />} />
          <Route path="/library"                element={<LibraryPage />} />
          <Route path="/hostel"                 element={<HostelPage />} />
          <Route path="/events"                 element={<EventsPage />} />

          {/* Role-specific */}
          <Route element={<RoleRoute allowedRoles={['student']} />}>
            <Route path="/student" element={<StudentPage />} />
          </Route>

          <Route element={<RoleRoute allowedRoles={['faculty', 'admin']} />}>
            <Route path="/faculty" element={<FacultyPage />} />
          </Route>

          {/* Admin only */}
          <Route element={<RoleRoute allowedRoles={['admin']} />}>
            <Route path="/admin"                   element={<AdminPage />} />
            <Route path="/admin/upload-pdf"        element={<UploadPDFPage />} />
            <Route path="/admin/upload-excel"      element={<UploadExcelPage />} />
            <Route path="/admin/upload-csv"        element={<UploadCSVPage />} />
            <Route path="/admin/documents"         element={<DocumentsPage />} />
            <Route path="/admin/users"             element={<UsersPage />} />
            <Route path="/admin/analytics"         element={<AnalyticsPage />} />
            <Route path="/admin/reports"           element={<ReportsPage />} />
            <Route path="/admin/notifications"     element={<NotificationsPage />} />
            <Route path="/admin/system-health"     element={<SystemHealthPage />} />
          </Route>
        </Route>
      </Route>

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import DashboardLayout from '../components/layout/DashboardLayout';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import ModulePlaceholder from '../pages/ModulePlaceholder';
import KnowledgeBase from '../pages/KnowledgeBase';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Officer Login & Info Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/info" element={<KnowledgeBase />} />

      {/* Dashboard Layout Routes */}
      <Route element={<DashboardLayout />}>
        {/* /dashboard is Public - accessible with or without authentication */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* Operational Modules - Protected (Redirects unauthenticated users to /login) */}
        <Route
          path="/alerts"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/risk-map"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/cases"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/evidence"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teams"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/intelligence"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit-logs"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <ModulePlaceholder />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Root & Catch-all Navigation */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default AppRoutes;

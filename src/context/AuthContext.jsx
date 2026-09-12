import React, { useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { AuthContext } from './authContextBase';

export function AuthProvider({ children }) {
  const [officer, setOfficer] = useState(() => authService.getCurrentOfficer());
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('cyber-sentinals-theme');
    return saved === 'quantum-light' ? 'quantum-light' : 'cyber-blue';
  });

  // Apply theme to html root element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('cyber-sentinals-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'cyber-blue' ? 'quantum-light' : 'cyber-blue'));
  };

  const login = async (officerId, password) => {
    setLoading(true);
    try {
      const session = await authService.login(officerId, password);
      setOfficer(session);
      return session;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setOfficer(null);
  };

  const value = {
    officer,
    isAuthenticated: !!officer,
    loading,
    login,
    logout,
    theme,
    setTheme,
    toggleTheme
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthProvider;

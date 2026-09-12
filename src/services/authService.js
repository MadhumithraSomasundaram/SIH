/**
 * Authentication Service for CYBERGUARD LEA (Prototype)
 * 
 * Manages officer session storage and mock authentication for Phase 1.
 * Ready to integrate with backend authentication endpoints in future phases.
 */

const STORAGE_KEY = 'cyber_officer_session';

export const authService = {
  /**
   * Prototype officer login
   * @param {string} officerId 
   * @param {string} password 
   * @returns {Promise<{officerId: string, loggedInAt: string}>}
   */
  async login(officerId, password) {
    // Artificial slight network delay for realistic UX
    await new Promise((resolve) => setTimeout(resolve, 400));

    const trimmedId = officerId ? officerId.trim() : '';
    const trimmedPassword = password ? password.trim() : '';

    if (!trimmedId || !trimmedPassword) {
      throw new Error('Please enter both Officer ID and Password.');
    }

    // Prototype credential check: requires non-empty credentials
    // Disallows blank or invalid input patterns
    if (trimmedPassword.length < 4) {
      throw new Error('Invalid credentials. Password must be at least 4 characters.');
    }

    const sessionData = {
      officerId: trimmedId,
      status: 'ACTIVE',
      role: 'LEA Officer',
      accessLevel: 'STANDARD',
      loggedInAt: new Date().toISOString()
    };

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
    } catch (e) {
      console.error('Failed to save session to localStorage:', e);
    }

    return sessionData;
  },

  /**
   * Clears the active officer session
   */
  logout() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.error('Failed to clear session from localStorage:', e);
    }
  },

  /**
   * Gets the currently authenticated officer from session
   * @returns {{officerId: string, loggedInAt: string} | null}
   */
  getCurrentOfficer() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      console.error('Failed to parse session:', e);
      return null;
    }
  },

  /**
   * Checks if an officer is authenticated
   * @returns {boolean}
   */
  isAuthenticated() {
    return this.getCurrentOfficer() !== null;
  }
};

export default authService;

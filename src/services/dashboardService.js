/**
 * Dashboard Service for CYBERGUARD LEA
 * 
 * Provides dashboard statistics and empty state datasets for Phase 1.
 * Ready for future integration with Flask backend API: GET /api/dashboard
 */

export const dashboardService = {
  /**
   * Retrieves dashboard state (0 values & empty arrays for Phase 1)
   * @returns {Promise<{
   *   stats: { totalAlerts: number, activeCases: number, highRiskZones: number, activeTeams: number },
   *   activeAlerts: Array<any>,
   *   riskIntelligence: Array<any>,
   *   recentActivity: Array<any>,
   *   notifications: Array<any>
   * }>}
   */
  async getDashboardData() {
    // Artificial slight network latency simulation for smooth UI rendering
    await new Promise((resolve) => setTimeout(resolve, 250));

    return {
      stats: {
        totalAlerts: 0,
        activeCases: 0,
        highRiskZones: 0,
        activeTeams: 0
      },
      activeAlerts: [],
      riskIntelligence: [],
      recentActivity: [],
      announcements: [],
      notifications: []
    };
  }
};

export default dashboardService;

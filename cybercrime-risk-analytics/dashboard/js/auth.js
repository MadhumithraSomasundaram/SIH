/**
 * Dashboard API Authentication Interceptor
 * Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
 *
 * Automatically attaches the prototype X-API-Key header to all API requests
 * originating from the dashboard, ensuring seamless communication with guarded
 * backend endpoints (/gis/*, /alerts/*, /predict, /explain).
 */
'use strict';

const DASHBOARD_API_KEY = 'sih26184-dashboard-prototype-key-2026';

(function () {
  const originalFetch = window.fetch;
  window.fetch = function (resource, init) {
    init = init || {};
    let url = typeof resource === 'string' ? resource : (resource && resource.url ? resource.url : '');

    // Check if the request is to our protected API endpoints
    const isInternalApi =
      url.startsWith('/gis') || url.includes('/gis/') ||
      url.startsWith('/alerts') || url.includes('/alerts/') ||
      url.startsWith('/predict') || url.includes('/predict') ||
      url.startsWith('/explain') || url.includes('/explain') ||
      url.startsWith('/model') || url.includes('/model/') ||
      url.startsWith('/database') || url.includes('/database/') ||
      url.startsWith('/health') || url.includes('/health');

    if (isInternalApi) {
      if (!init.headers) {
        init.headers = {};
      }
      if (init.headers instanceof Headers) {
        if (!init.headers.has('X-API-Key')) {
          init.headers.set('X-API-Key', DASHBOARD_API_KEY);
        }
      } else if (Array.isArray(init.headers)) {
        const hasKey = init.headers.some(([k]) => k.toLowerCase() === 'x-api-key');
        if (!hasKey) {
          init.headers.push(['X-API-Key', DASHBOARD_API_KEY]);
        }
      } else {
        if (!init.headers['X-API-Key'] && !init.headers['x-api-key']) {
          init.headers['X-API-Key'] = DASHBOARD_API_KEY;
        }
      }
    }
    return originalFetch.call(this, resource, init);
  };
})();

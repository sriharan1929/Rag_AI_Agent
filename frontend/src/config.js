/**
 * config.js — Central frontend configuration.
 * Reads from frontend/.env (REACT_APP_API_URL).
 */
const API_URL = process.env.REACT_APP_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

export { API_URL };

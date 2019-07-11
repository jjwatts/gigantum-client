import history from 'JS/history';
import auth0 from 'auth0-js';
import RemoveUserIdentityMutation from 'Mutations/RemoveUserIdentityMutation';
// queries
import SessionCheck from 'JS/Auth/sessionCheck';
// store
import { setLogout, setLoginError } from 'JS/redux/actions/login';
// variables
import { AUTH_CONFIG } from './auth0-variables';

export default class Auth {
  auth0 = new auth0.WebAuth({
    domain: AUTH_CONFIG.domain,
    clientID: AUTH_CONFIG.clientId,
    redirectUri: AUTH_CONFIG.callbackUrl,
    audience: AUTH_CONFIG.audience,
    responseType: 'token id_token',
    scope: 'openid profile email user_metadata',
  });

  constructor() {
    this.login = this.login.bind(this);
    this.logout = this.logout.bind(this);
    this.handleAuthentication = this.handleAuthentication.bind(this);
    this.isAuthenticated = this.isAuthenticated.bind(this);
    this.renewToken = this.renewToken.bind(this);
  }

  /**
   * Renews auth token if possible, otherwise prompt login
  */
  renewToken(showModal, showModalCallback, successCallback, forceHistory, failureCallback) {
    this.auth0.checkSession({}, (err, result) => {
      if (err) {
        if (showModal) {
          showModalCallback();
        } else {
          failureCallback();
        }
      } else {
        this.setSession(result, true, forceHistory);
        if (successCallback) {
          successCallback();
        }
      }
    });
  }

  login() {
    setLogout(false);
    this.auth0.authorize();
  }

  handleAuthentication() {
    this.auth0.parseHash((err, authResult) => {
      if (authResult && authResult.accessToken && authResult.idToken) {
        this.setSession(authResult);
        window.sessionStorage.removeItem('LOGIN_ERROR_DESCRIPTION');
        window.sessionStorage.removeItem('LOGIN_ERROR_TYPE');
      } else if (err) {
        history.replace('/login');
        setLoginError(err);
        window.sessionStorage.setItem('LOGIN_ERROR_TYPE', err.error);
        window.sessionStorage.setItem('LOGIN_ERROR_DESCRIPTION', err.errorDescription);
        //  alert(`Error: ${err.error}. Check the console for further details.`); TODO make this a modal or redirect to login failure page
      }
    });
  }

  setSession(authResult, silent, forceHistory) {
    // Set the time that the access token will expire at
    const expiresAt = JSON.stringify((authResult.expiresIn * 1000) + new Date().getTime());
    localStorage.setItem('access_token', authResult.accessToken);
    localStorage.setItem('id_token', authResult.idToken);
    localStorage.setItem('expires_at', expiresAt);
    localStorage.setItem('family_name', authResult.idTokenPayload.family_name);
    localStorage.setItem('given_name', authResult.idTokenPayload.given_name);
    localStorage.setItem('email', authResult.idTokenPayload.email);
    localStorage.setItem('username', authResult.idTokenPayload.nickname);
    // redirect to labbooks when user logs in
    let route = window.sessionStorage.getItem('CALLBACK_ROUTE')
      ? window.sessionStorage.getItem('CALLBACK_ROUTE')
      : '/projects';

    route = route === ''
      ? '/projects'
      : route;

    if (!silent || forceHistory) {
      history.replace(route);
    }
  }

  logout() {
    setLogout(true);
    RemoveUserIdentityMutation(() => {
      // redirect to root when user logs out

      localStorage.removeItem('access_token');
      localStorage.removeItem('id_token');
      localStorage.removeItem('expires_at');
      localStorage.removeItem('family_name');
      localStorage.removeItem('given_name');
      localStorage.removeItem('email');
      localStorage.removeItem('username');
      window.sessionStorage.removeItem('CALLBACK_ROUTE');

      history.replace('/');
    });
  }

  isAuthenticated() {
    // Check whether the current time is past the
    // access token's expiry time

    return SessionCheck.getUserIdentity().then(response => response && response.data && response.data.userIdentity && response.data.userIdentity.isSessionValid);
  }
}

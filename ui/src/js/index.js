import React from 'react';
import { render } from 'react-dom';
import UserIdentity from 'JS/Auth/UserIdentity';
import Auth from 'JS/Auth/Auth';
import { Provider } from 'react-redux';
import { detect } from 'detect-browser';
// store
import store from 'JS/redux/store';
// components
import Routes from 'Components/Routes';
import BrowserSupport from 'Components/browserSupport/BrowserSupport';
// service worker
import { unregister } from './registerServiceWorker';
// assets
import '../css/critical.scss';

const auth = new Auth();
let routes;

UserIdentity.getUserIdentity().then((response) => {
  const expiresAt = JSON.stringify((new Date().getTime() * 1000) + new Date().getTime());
  let forceLoginScreen = true;
  let loadingRenew = false;

  if (response.data) {
    if (response.data.userIdentity && ((response.data.userIdentity.isSessionValid && navigator.onLine) || !navigator.onLine)) {
      localStorage.setItem('family_name', response.data.userIdentity.familyName);
      localStorage.setItem('given_name', response.data.userIdentity.givenName);
      localStorage.setItem('email', response.data.userIdentity.email);
      localStorage.setItem('username', response.data.userIdentity.username);
      localStorage.setItem('expires_at', expiresAt);
      forceLoginScreen = false;
    } else if (response.data.userIdentity && localStorage.getItem('access_token')) {
      loadingRenew = true;
      auth.renewToken(null, null, () => {
        setTimeout(() => {
          routes.setState({ loadingRenew: false });
        }, 2000);
      }, true, () => {
        routes.setState({ forceLoginScreen: true, loadingRenew: false });
      });
    } else if (!response.data.userIdentity && !localStorage.getItem('access_token')) {
      localStorage.removeItem('family_name');
      localStorage.removeItem('given_name');
      localStorage.removeItem('email');
      localStorage.removeItem('username');
      localStorage.removeItem('expires_at');
      localStorage.removeItem('access_token');
      localStorage.removeItem('id_token');
      forceLoginScreen = true;
    }
  }
  const browser = detect();
  if ((browser.name === 'chrome') || (browser.name === 'firefox')) {
    render(
      <Provider store={store}>
        <Routes
          ref={el => routes = el}
          auth={auth}
          forceLoginScreen={forceLoginScreen}
          loadingRenew={loadingRenew}
        />
      </Provider>,
      document.getElementById('root') || document.createElement('div'),
    );
  } else {
    render(
      <BrowserSupport />,
      document.getElementById('root') || document.createElement('div'),
    );
  }
});

unregister();

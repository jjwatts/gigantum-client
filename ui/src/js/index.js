import React from 'react';
import { render } from 'react-dom';
import { unregister } from './registerServiceWorker';
import './../css/critical.scss';
import UserIdentity from 'JS/Auth/UserIdentity';
import Auth from 'JS/Auth/Auth';
import { Provider } from 'react-redux';
// components
import Routes from './components/Routes';
// store
import store from 'JS/redux/store';

const auth = new Auth();
let routes;

UserIdentity.getUserIdentity().then((response) => {
  const expiresAt = JSON.stringify((new Date().getTime() * 1000) + new Date().getTime());
  let forceLoginScreen = true;
  let loadingRenew = false;
  let validSession = false;

  if (response.data) {
    if (response.data.userIdentity && ((response.data.userIdentity.isSessionValid && navigator.onLine) || !navigator.onLine)) {
      localStorage.setItem('family_name', response.data.userIdentity.familyName);
      localStorage.setItem('given_name', response.data.userIdentity.givenName);
      localStorage.setItem('email', response.data.userIdentity.email);
      localStorage.setItem('username', response.data.userIdentity.username);
      localStorage.setItem('expires_at', expiresAt);
      validSession = true;
      forceLoginScreen = false;
    } else if (response.data.userIdentity && localStorage.getItem('access_token')) {
      loadingRenew = true;
      auth.renewToken(null, null, () => {
        setTimeout(() => {
          routes.setState({ loadingRenew: false });
        }, 2000);
        validSession = true;
      }, true, () => {
        routes.setState({ forceLoginScreen: true, loadingRenew: false });
      });
    } else if (!localStorage.getItem('access_token')) {
      localStorage.removeItem('family_name');
      localStorage.removeItem('given_name');
      localStorage.removeItem('email');
      localStorage.removeItem('username');
      localStorage.removeItem('expires_at');
      localStorage.removeItem('access_token');
      localStorage.removeItem('id_token');
      forceLoginScreen = true;
    }
  } else {

  }

  render(
    <Provider store={store}>
      <Routes
        ref={el => routes = el}
        auth={auth}
        forceLoginScreen={forceLoginScreen}
        loadingRenew={loadingRenew}
        validSession={validSession}
      />
    </Provider>
    , document.getElementById('root') || document.createElement('div'),

  );
});

unregister();

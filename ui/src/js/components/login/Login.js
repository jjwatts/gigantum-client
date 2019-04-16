// vendor
import React, { Component } from 'react';
import store from 'JS/redux/store';
import Loader from 'Components/common/Loader';
// config
import config from 'JS/config';
// assets
import './Login.scss';

// import CreatePage from './components/CreatePage';
export default class Login extends Component {
  constructor(props) {
    super(props);
    this.state = store.getState().login;
  }

  /**
    @param {}
    login through Auth0
  */
  login() {
    const { props } = this;
    props.auth.login();
  }

  /**
    @param {}
    logout through Auth0
  */
  logout() {
    const { props } = this;
    props.auth.logout();
  }

  render() {
    const { props } = this;
    const errorType = sessionStorage.getItem('LOGIN_ERROR_TYPE');
    const errorDescription = sessionStorage.getItem('LOGIN_ERROR_DESCRIPTION');
    return (
      <div className="Login">
        { props.userIdentityReturned
          && (
            <div className="Login__panel">
              { (window.location.hostname === config.demoHostName)
                && (
                  <div className="demo-header">
                    Login or create an account to try out Gigantum.
                    <a
                      href="https://docs.gigantum.com/docs/frequently-asked-questions#section-why-do-i-need-to-log-in"
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                        Why?
                    </a>
                  </div>
                )
              }
              { errorType
                && (
                  <div className="LoginError">
                    <div className="Login__error">
                      <div className="Login__error-type">
                        <div className="Login__error-exclamation" />
                        <div>{errorType}</div>
                      </div>
                      <div className="Login__error-description">
                        {errorDescription}
                      </div>
                    </div>
                  </div>
                )
               }

              <div className="Login__logo" />

              { props.loadingRenew
                ? (
                  <button
                    type="button"
                    disabled
                    className="Login__button--loading"
                  >
                    Logging In
                    <div className="Code__loading" />
                  </button>
                )
                : (
                  <button
                    type="button"
                    className="Login__button"
                    onClick={this.login.bind(this)}
                  >
                    Log In
                  </button>
                )
              }
            </div>
          )
        }
        {
          props.userIdentityReturned && <Loader />
        }
      </div>
    );
  }
}

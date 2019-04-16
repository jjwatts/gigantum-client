// vendor
import React, { Component } from 'react';
// components
import Dashboard from 'Components/dashboard/Dashboard';
import Login from 'Components/login/Login';
// assets
import './Home.scss';

export default class Home extends Component {
  // login for Auth0 function
  constructor(props) {
    super(props);
    this.state = {
      authenticated: null,
    };
    this.footerWorkerCallback = this.footerWorkerCallback.bind(this);
  }

  /*
    sets authentication response to the state
  */
  componentDidMount() {
    const { props, state } = this;
    props.auth.isAuthenticated().then((response) => {
      let isAuthenticated = response;
      if (isAuthenticated === null) {
        isAuthenticated = false;
      }
      if (isAuthenticated !== state.authenticated) {
        this.setState({ authenticated: isAuthenticated });
      }
    });
  }

  login() {
    const { props } = this;
    props.auth.login();
  }

  footerWorkerCallback(worker, filepath) {
    const { props } = this;
    props.footerWorkerCallback(worker, filepath);
  }

  render() {
    const { props, state } = this;
    const { loadingRenew } = props;
    return (
      <div className="Home">
        {
          state.authenticated && (
            <Dashboard
              auth={props.auth}
              diskLow={props.diskLow}
              footerWorkerCallback={this.footerWorkerCallback}
              section={props.match}
              match={props.match}
              history={props.history}
            />
          )
        }

        {
          !state.authenticated && state.authenticated !== null && (
          <Login
            auth={props.auth}
            loadingRenew={loadingRenew}
            userIdentityReturned={props.userIdentityReturned}
            diskLow={props.diskLow}
          />
          )
        }

      </div>
    );
  }
}

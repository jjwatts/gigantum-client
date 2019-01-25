import React, { Component } from 'react';
import Dashboard from 'Components/dashboard/Dashboard';
import Login from 'Components/login/Login';

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
    this.props.auth.isAuthenticated().then((response) => {
      let isAuthenticated = response;
      if (isAuthenticated === null) {
        isAuthenticated = false;
      }
      if (isAuthenticated !== this.state.authenticated) {
        this.setState({ authenticated: isAuthenticated });
      }
    });
  }
  login() {
    this.props.auth.login();
  }

  footerWorkerCallback(worker, filepath) {
    this.props.footerWorkerCallback(worker, filepath);
  }
  render() {
    const { loadingRenew } = this.props;
    return (
      <div className="Home">
        {
          this.state.authenticated && (
            <Dashboard
              auth={this.props.auth}
              footerWorkerCallback={this.footerWorkerCallback}
              section={this.props.match}
              match={this.props.match}
              history={this.props.history}
            />
          )
        }

        {
          !this.state.authenticated && this.state.authenticated !== null && (
          <Login
            auth={this.props.auth}
            loadingRenew={loadingRenew}
          />
            )
        }

      </div>
    );
  }
}

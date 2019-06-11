// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import YouTube from 'react-youtube';
import Loadable from 'react-loadable';
import Auth from 'JS/Auth/Auth';
import { boundMethod } from 'autobind-decorator';
import {
  BrowserRouter as Router,
  Route,
  Switch,
  Redirect,
} from 'react-router-dom'; // keep browser router, reloads page with Router in labbook view
// history
import history from 'JS/history';
// components
import SideBar from 'Components/common/SideBar';
import Footer from 'Components/common/footer/Footer';
import Prompt from 'Components/common/Prompt';
import DiskHeader from 'Components/common/DiskHeader';
import Helper from 'Components/common/Helper';
import Loader from 'Components/common/Loader';
// config
import config from 'JS/config';
// auth
import UserIdentity from 'JS/Auth/UserIdentity';
// assets
import './Routes.scss';

const Loading = () => <div />;
const auth = new Auth();

const Home = Loadable({
  loader: () => import('Components/home/Home'),
  loading: Loading,
});

const LabbookQueryContainer = Loadable({
  loader: () => import('Components/labbook/LabbookQueryContainer'),
  loading: Loading,
});

const DatasetQueryContainer = Loadable({
  loader: () => import('Components/dataset/DatasetQueryContainer'),
  loading: Loading,
});


class Routes extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      forceLoginScreen: null,
      loadingRenew: true,
      userIdentityReturned: false,
      showYT: false,
      showDefaultMessage: true,
      diskLow: false,
      available: 0,
    };

    this._setForceLoginScreen = this._setForceLoginScreen.bind(this);
    this._flipDemoHeaderText = this._flipDemoHeaderText.bind(this);
  }

  /**
    @param {}
    calls flip header text function
  */
  componentDidMount() {
    const self = this;

    this._checkSysinfo();
    this._flipDemoHeaderText();

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
              self.setState({ loadingRenew: false });
            }, 2000);
          }, true, () => {
            self.setState({ forceLoginScreen: true, loadingRenew: false });
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

      this.setState({
        forceLoginScreen,
        loadingRenew,
        userIdentityReturned: true,
      });
    });
  }

  /**
    @param {Error, Object} error, info
    shows error message when runtime error occurs
  */
  componentDidCatch(error, info) {
    this.setState({ hasError: true });
  }

  /**
    @param {}
    changes text of demo header message
  */
  _flipDemoHeaderText() {
    const { state } = this;
    const self = this;
    setTimeout(() => {
      self.setState({ showDefaultMessage: !state.showDefaultMessage });
      self._flipDemoHeaderText();
    }, 15000);
  }

  /**
    @param{}
    logs user out in using auth0
  */
  login() {
    const { props } = this;
    auth.login();
  }

  /**
    @param{}
    logs user out using auth0
  */
  logout() {
    const { props } = this;
    auth.logout();
  }

  /**
    @param {boolean} forceLoginScreen
    sets state of forceloginscreen
  */
  _setForceLoginScreen(forceLoginScreen) {
    const { state } = this;
    if (forceLoginScreen !== state.forceLoginScreen) {
      this.setState({ forceLoginScreen });
    }
  }

  /**
    hides disk warning
  */
  @boundMethod
  _hideDiskWarning() {
    window.sessionStorage.setItem('hideDiskWarning', true);
    this.forceUpdate();
  }

  /**
    shows sysinfo header if available size is too small
  */
  _checkSysinfo() {
    const apiHost = process.env.NODE_ENV === 'development' ? 'localhost:10000' : window.location.host;
    const self = this;
    const url = `${window.location.protocol}//${apiHost}${process.env.SYSINFO_API}`;
    setTimeout(self._checkSysinfo.bind(this), 60 * 1000);
    return fetch(url, {
      method: 'GET',
      headers: {
          'Content-Type': 'application/json',
          accept: '*/*',
      },
    }).then((response) => {
      if (response.status === 200 && (response.headers.get('content-type') === 'application/json')) {
        response.json().then((res) => {
          const { available, lowDiskWarning } = res.disk;
          self.setState({ diskLow: lowDiskWarning, available });
        });
      }
    }).catch(() => false);
  }

  render() {
    const { props, state } = this;
    const showDiskLow = state.diskLow && !window.sessionStorage.getItem('hideDiskWarning');
    if (!state.hasError) {
      // declare variables
      const demoText = "You're using the Gigantum web demo. Data is wiped hourly. To continue using Gigantum ";
      // declare css
      const headerCSS = classNames({
        HeaderBar: true,
        'is-demo': (window.location.hostname === config.demoHostName) || showDiskLow,
      });
      const routesCSS = classNames({
        Routes__main: true,
      });

      if (state.forceLoginScreen === null) {
        return <Loader />;
      }

      return (

        <Router>

          <Switch>

            <Route
              path=""
              render={() => (
                <div className="Routes">
                  {
                    window.location.hostname === config.demoHostName
                    && (state.showDefaultMessage
                      ? (
                        <div
                          id="demo-header"
                          className="demo-header"
                        >
                          {demoText}
                          <a
                            href="http://gigantum.com/download"
                            rel="noopener noreferrer"
                            target="_blank"
                          >
                        download the Gigantum client.
                          </a>
                        </div>
                      )
                      : (
                        <div
                          id="demo-header"
                          className="demo-header"
                        >
                      Curious what can Gigantum do for you? &nbsp;
                          <a onClick={() => this.setState({ showYT: true })}>
                         Watch this overview video.
                          </a>
                        </div>
                      ))
                  }
                  {
                    showDiskLow
                    && (
                    <DiskHeader
                      available={state.available}
                      hideDiskWarning={this._hideDiskWarning}
                    />)
                  }
                  {
                    state.showYT
                      && (
                      <div
                        id="yt-lightbox"
                        className="yt-lightbox"
                        onClick={() => this.setState({ showYT: false })}
                      >
                        <YouTube
                          opts={{ height: '576', width: '1024' }}
                          className="yt-frame"
                          videoId="S4oW2CtN500"
                        />
                      </div>
                      )
                  }
                  <div className={headerCSS} />
                  <SideBar
                    auth={auth}
                    history={history}
                    diskLow={showDiskLow}
                  />
                  <div className={routesCSS}>

                    <Route
                      exact
                      path="/"
                      render={parentProps => (
                        <Home
                          loadingRenew={state.loadingRenew}
                          userIdentityReturned={state.userIdentityReturned}
                          history={history}
                          auth={auth}
                          diskLow={showDiskLow}
                          {...parentProps}
                        />
                      )
                    }
                    />

                    <Route
                      exact
                      path="/login"
                      render={parentProps => (
                        <Home
                          userIdentityReturned={state.userIdentityReturned}
                          loadingRenew={state.loadingRenew}
                          history={history}
                          auth={auth}
                          diskLow={showDiskLow}
                          {...parentProps}
                        />
                      )
                      }
                    />
                    <Route
                      exact
                      path="/:id"
                      render={() => <Redirect to="/projects/local" />}
                    />

                    <Route
                      exact
                      path="/labbooks/:section"
                      render={() => <Redirect to="/projects/local" />}
                    />


                    <Route
                      exact
                      path="/datasets/:labbookSection"
                      render={parentProps => (
                        <Home
                          userIdentityReturned={state.userIdentityReturned}
                          loadingRenew={state.loadingRenew}
                          history={history}
                          auth={auth}
                          diskLow={showDiskLow}
                          {...parentProps}
                        />
                      )
                      }
                    />


                    <Route
                      exact
                      path="/projects/:labbookSection"
                      render={parentProps => (
                        <Home
                          userIdentityReturned={state.userIdentityReturned}
                          loadingRenew={state.loadingRenew}
                          history={history}
                          auth={auth}
                          diskLow={showDiskLow}
                          {...parentProps}
                        />
                      )
                      }
                    />

                    <Route
                      path="/datasets/:owner/:datasetName"
                      auth={auth}
                      render={(parentProps) => {
                        if (state.forceLoginScreen) {
                          return <Redirect to="/login" />;
                        }

                        return (
                          <DatasetQueryContainer
                            datasetName={parentProps.match.params.datasetName}
                            owner={parentProps.match.params.owner}
                            auth={auth}
                            history={history}
                            diskLow={showDiskLow}
                            {...props}
                            {...parentProps}
                          />
                        );
                      }

                      }
                    />

                    <Route
                      path="/projects/:owner/:labbookName"
                      auth={auth}
                      render={(parentProps) => {
                        if (state.forceLoginScreen) {
                          return <Redirect to="/login" />;
                        }

                        return (
                          <LabbookQueryContainer
                            labbookName={parentProps.match.params.labbookName}
                            owner={parentProps.match.params.owner}
                            auth={auth}
                            history={history}
                            diskLow={showDiskLow}
                            {...props}
                            {...parentProps}
                          />
                        );
                      }

                      }
                    />

                    <Helper auth={auth} />

                    <Prompt ref="prompt" />

                    <Footer
                      ref="footer"
                      history={history}
                    />

                  </div>
                </div>
              )}
            />
          </Switch>
        </Router>
      );
    }
    return (
      <div className="Routes__error">

        <p>An error has occured. Please try refreshing the page.</p>
      </div>
    );
  }
}


export default Routes;

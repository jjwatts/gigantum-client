// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import YouTube from 'react-youtube';
import Loadable from 'react-loadable';
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
import Helper from 'Components/common/Helper';
// config
import config from 'JS/config';
// assets
import './Routes.scss';

const Loading = () => <div />;

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
      forceLoginScreen: this.props.forceLoginScreen,
      loadingRenew: this.props.loadingRenew,
      showYT: false,
      showDefaultMessage: true,
      diskLow: false,
    };

    this._setForceLoginScreen = this._setForceLoginScreen.bind(this);
    this._flipDemoHeaderText = this._flipDemoHeaderText.bind(this);
  }

  /**
    @param {}
    calls flip header text function
  */
  componentDidMount() {
    this._checkSysinfo()
    this._flipDemoHeaderText();
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
    const self = this;
    setTimeout(() => {
      self.setState({ showDefaultMessage: !this.state.showDefaultMessage });
      self._flipDemoHeaderText();
    }, 15000);
  }

  /**
    @param{}
    logs user out in using auth0
  */
  login() {
    this.props.auth.login();
  }

  /**
    @param{}
    logs user out using auth0
  */
  logout() {
    this.props.auth.logout();
  }

  /**
    @param {boolean} forceLoginScreen
    sets state of forceloginscreen
  */
  _setForceLoginScreen(forceLoginScreen) {
    if (forceLoginScreen !== this.state.forceLoginScreen) {
      this.setState({ forceLoginScreen });
    }
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
    }).then((response) => {
      if (response.status === 200 && (response.headers.get('content-type') === 'application/json')) {
        response.json().then((res) => {
          const { available } = res.disk;
          const size = available.slice(0, available.length - 1);
          const sizeType = available.slice(-1);
          if ((sizeType === 'T') || ((sizeType === 'G') && (Number(size) > 5))) {
            self.setState({ diskLow: false });
          } else {
            self.setState({ diskLow: true });
          }
        });
      }
    }).catch(() => false);
  }

  render() {
    const { state, props } = this;
    if (!state.hasError) {
      const headerCSS = classNames({
        HeaderBar: true,
        'is-demo': (window.location.hostname === config.demoHostName) || state.diskLow,
      });
      const routesCSS = classNames({
        Routes__main: true,
      });

      const demoText = "You're using the Gigantum web demo. Data is wiped hourly. To continue using Gigantum ";

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
                    state.diskLow &&
                    (
                      <div className="disk-header">
                        Gigantum is running low on storage.
                        {' '}
                        <a
                          href="https://docs.gigantum.com/docs/"
                          rel="noopener noreferrer"
                          target="_blank"
                        >
                          Click here
                        </a>
                        {' '}
                        to learn how to allocate more space to Docker, or free up existing storage in Gigantum.
                      </div>
                    )
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
                    auth={props.auth}
                    history={history}
                    diskLow={state.diskLow}
                  />
                  <div className={routesCSS}>

                    <Route
                      exact
                      path="/"
                      render={renderProps => (
                        <Home
                          loadingRenew={state.loadingRenew}
                          history={history}
                          diskLow={state.diskLow}
                          auth={props.auth}
                          {...renderProps}
                        />
                      )
                    }
                    />

                    <Route
                      exact
                      path="/login"
                      render={renderProps => (
                        <Home
                          loadingRenew={state.loadingRenew}
                          history={history}
                          diskLow={state.diskLow}
                          auth={props.auth}
                          {...renderProps}
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
                      render={renderProps => (
                        <Home
                          loadingRenew={state.loadingRenew}
                          history={history}
                          auth={props.auth}
                          diskLow={state.diskLow}
                          {...renderProps}
                        />
                      )
                      }
                    />


                    <Route
                      exact
                      path="/projects/:labbookSection"
                      render={renderProps => (
                        <Home
                          loadingRenew={state.loadingRenew}
                          history={history}
                          auth={props.auth}
                          diskLow={state.diskLow}
                          {...renderProps}
                        />
                      )
                      }
                    />

                    <Route
                      path="/datasets/:owner/:datasetName"
                      auth={props.auth}
                      render={(parentProps) => {
                        if (state.forceLoginScreen) {
                          return <Redirect to="/login" />;
                        }

                        return (
                          <DatasetQueryContainer
                            datasetName={parentProps.match.params.datasetName}
                            owner={parentProps.match.params.owner}
                            auth={props.auth}
                            history={history}
                            diskLow={state.diskLow}
                            {...props}
                            {...parentProps}
                          />);
                      }

                      }
                    />

                    <Route
                      path="/projects/:owner/:labbookName"
                      auth={props.auth}
                      render={(parentProps) => {
                        if (state.forceLoginScreen) {
                          return <Redirect to="/login" />;
                        }

                        return (
                          <LabbookQueryContainer
                            labbookName={parentProps.match.params.labbookName}
                            owner={parentProps.match.params.owner}
                            auth={props.auth}
                            history={history}
                            diskLow={state.diskLow}
                            {...props}
                            {...parentProps}
                          />);
                      }

                      }
                    />

                    <Helper
                      auth={props.auth}
                    />

                    <Prompt
                      ref="prompt"
                    />

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

// vendor
import React, { Component } from 'react';
import { Route, Switch } from 'react-router-dom';
import {
  createFragmentContainer,
  graphql,
} from 'react-relay';
import { DragDropContext } from 'react-dnd';
import HTML5Backend from 'react-dnd-html5-backend';
import classNames from 'classnames';
import { connect } from 'react-redux';
import Loadable from 'react-loadable';
// store
import store from 'JS/redux/store';
import { setContainerMenuWarningMessage } from 'JS/redux/reducers/labbook/environment/environment';
import { setMergeMode, setBuildingState, setStickyDate } from 'JS/redux/reducers/labbook/labbook';
import { setCallbackRoute } from 'JS/redux/reducers/routes';
import { setLatestPackages } from 'JS/redux/reducers/labbook/environment/packageDependencies';
// utils
import { getFilesFromDragEvent } from 'JS/utils/html-dir-content';
import FetchContainerStatus from './fetchContainerStatus';
// config
import Config from 'JS/config';
// components
import Login from 'Components/login/Login';
import Loader from 'Components/common/Loader';
import ErrorBoundary from 'Components/common/ErrorBoundary';
import Header from '../shared/header/Header';
// import Activity from './activity/LabbookActivityContainer';
// assets
import './Labbook.scss';


const Loading = () => <Loader />;

/*
 * Code splitting imports intended to boost initial load speed
*/

const Overview = Loadable({
  loader: () => import('./overview/LabbookOverviewContainer'),
  loading: Loading,
});
const Activity = Loadable({
  loader: () => import('./activity/LabbookActivityContainer'),
  loading: Loading,
});
const Code = Loadable({
  loader: () => import('./code/Code'),
  loading: Loading,
});
const InputData = Loadable({
  loader: () => import('./inputData/Input'),
  loading: Loading,
});
const OutputData = Loadable({
  loader: () => import('./outputData/Output'),
  loading: Loading,
});
const Environment = Loadable({
  loader: () => import('./environment/Environment'),
  loading: Loading,
});

class Labbook extends Component {
  constructor(props) {
  	super(props);
    localStorage.setItem('owner', store.getState().routes.owner);
    // bind functions here
    this._setBuildingState = this._setBuildingState.bind(this);
    this._toggleBranchesView = this._toggleBranchesView.bind(this);
    this._branchViewClickedOff = this._branchViewClickedOff.bind(this);
    setCallbackRoute(props.location.pathname);
  }

  state = {
    containerStatus: this.props.labbook.environment.containerStatus,
    imageStatus: this.props.labbook.environment.imageStatus,
    isBuilding: false,
    isLocked: (this.props.labbook.environment.containerStatus !== 'NOT_RUNNING'),
  }

  UNSAFE_componentWillMount() {
    const { labbookName, owner } = store.getState().routes;
    document.title = `${owner}/${labbookName}`;
  }

  UNSAFE_componentWillReceiveProps(nextProps) {
    setCallbackRoute(nextProps.location.pathname);
  }

  /**
    @param {}
    subscribe to store to update state
    set unsubcribe for store
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
    this._setStickHeader();
    this._fetchStatus();

    window.addEventListener('scroll', this._setStickHeader);
    window.addEventListener('click', this._branchViewClickedOff);
  }

  /**
    @param {}
    removes event listeners
  */
  componentWillUnmount() {
    setLatestPackages({});

    window.removeEventListener('scroll', this._setStickHeader);

    window.removeEventListener('click', this._branchViewClickedOff);
  }

  /**
  *  @param {}
  *  fetches status of labbook container and image
  *  sets state of labbook using redux and containerStatus using setState
  *  @return {}
  */
  _fetchStatus() {
    const { props, state } = this,
          { owner, name } = props.labbook,
          self = this,
          { isBuilding } = props;

      FetchContainerStatus.getContainerStatus(owner, name).then((response, error) => {
        if (response && response.labbook) {
          const { environment } = response.labbook;
          // reset build flags
          if ((environment.imageStatus !== 'BUILD_IN_PROGRESS') && isBuilding) {
            self.setState({
              isBuilding: false,
            });

            setBuildingState(false);
          }
          // only updates state if container or imageStatus has changed
          if ((state.containerStatus !== environment.containerStatus) || (state.imageStatus !== environment.imageStatus)) {
            const isLocked = (environment.containerStatus !== 'NOT_RUNNING');
            self.setState({
              imageStatus: environment.imageStatus,
              containerStatus: environment.containerStatus,
              isLocked,
            });
          }
        }
        // refetches status after a 3 second timeout
        setTimeout(() => {
          self._fetchStatus();
        }, 3 * 1000);
      });
  }

  /**
    @param {event}
    updates state of labbook when prompted ot by the store
    updates history prop
  */
  _branchViewClickedOff(evt) {
    if (evt.target.className.indexOf('Labbook__veil') > -1) {
      this._toggleBranchesView(false, false);
    }
  }

  /**
    @param {}
    dispatches sticky state to redux to update state
  */
  _setStickHeader() {
    this.offsetDistance = window.pageYOffset;
    const sticky = 50;
    const isSticky = window.pageYOffset >= sticky;
    if (store.getState().labbook.isSticky !== isSticky) {
      setStickyDate(isSticky);
    }

    if (isSticky) {
      setMergeMode(false, false);
    }
  }

  /**
    @param {boolean} isBuilding
    updates container status state
    updates labbook state
  */
  _setBuildingState = (isBuilding) => {
    const { props } = this;
    this.refs.ContainerStatus && this.refs.ContainerStatus.setState({ isBuilding });

    if (props.isBuilding !== isBuilding) {
      setBuildingState(isBuilding);
    }
  }

  /**
    @param {boolean, boolean}
    updates branchOpen state
  */
  _toggleBranchesView(branchesOpen, mergeFilter) {
    if (store.getState().containerStatus.status !== 'Running') {
      setMergeMode(branchesOpen, mergeFilter);
    } else {
      setContainerMenuWarningMessage('Stop Project before switching branches. \n Be sure to save your changes.');
    }
  }

  /**
    scrolls to top of window
  */
  _scrollToTop() {
    window.scrollTo(0, 0);
  }

  render() {
    const { props, state } = this;
    const isLockedBrowser = {
      locked: (props.isPublishing || props.isSyncing || props.isExporting),
      isPublishing: props.isPublishing,
      isExporting: props.isExporting,
      isSyncing: props.isSyncing,
    };
    const isLocked = props.isBuilding || props.isSyncing || props.isPublishing || state.isLocked;
    if (props.labbook) {
      const { labbook, branchesOpen } = props;
      const branchName = props.labbook.activeBranchName;

      const labbookCSS = classNames({
        Labbook: true,
        'Labbook--detail-mode': props.detailMode,
        'Labbook--branch-mode': branchesOpen,
        'Labbook--demo-mode': window.location.hostname === Config.demoHostName,
      });

      return (
        <div className={labbookCSS}>

          <div className="Labbook__spacer flex flex--column">

            <Header
              {...props}
              description={labbook.description}
              setBuildingState={this._setBuildingState}
              toggleBranchesView={this._toggleBranchesView}
              branchName={branchName}
              sectionType={'labbook'}
              containerStatus={state.containerStatus}
              imageStatus={state.imageStatus}
              isLocked={isLocked}
            />

            <div className="Labbook__routes flex flex-1-0-auto">

              <Switch>
                <Route
                  exact
                  path={`${props.match.path}`}
                  render={() => (
                    <ErrorBoundary type="labbookSectionError">
                      <Overview
                        key={`${props.labbookName}_overview`}
                        labbook={labbook}
                        labbookId={labbook.id}
                        setBuildingState={this._setBuildingState}
                        isSyncing={props.isSyncing}
                        isPublishing={props.isPublishing}
                        scrollToTop={this._scrollToTop}
                        sectionType="labbook"
                        history={this.props.history}
                      />
                    </ErrorBoundary>
                        )}
                />

                <Route path={`${props.match.path}/:labbookMenu`}>

                  <Switch>

                    <Route
                      path={`${props.match.path}/overview`}
                      render={() => (

                        <ErrorBoundary
                          type="labbookSectionError"
                          key="overview">
                          <Overview
                               key={`${props.labbookName}_overview`}
                               labbook={labbook}
                               description={labbook.description}
                               labbookId={labbook.id}
                               setBuildingState={this._setBuildingState}
                               isSyncing={props.isSyncing}
                               isPublishing={props.isPublishing}
                               scrollToTop={this._scrollToTop}
                               sectionType="labbook"
                                history={this.props.history}
                             />
                        </ErrorBoundary>
                            )}
                    />

                    <Route
                      path={`${props.match.path}/activity`}
                      render={() => (
                        <ErrorBoundary
                          type="labbookSectionError"
                          key="activity">
                          <Activity
                               key={`${props.labbookName}_activity`}
                               labbook={labbook}
                               activityRecords={props.activityRecords}
                               labbookId={labbook.id}
                               branchName={branchName}
                               description={labbook.description}
                               activeBranch={labbook.activeBranchName}
                               isMainWorkspace={branchName === 'workspace'}
                               setBuildingState={this._setBuildingState}
                               sectionType={'labbook'}
                               isLocked={isLocked}
                               {...props}
                             />
                        </ErrorBoundary>
                          )}
                    />

                    <Route
                      path={`${props.match.url}/environment`}
                      render={() => (
                        <ErrorBoundary
                          type="labbookSectionError"
                          key="environment">
                          <Environment
                               key={`${props.labbookName}_environment`}
                               labbook={labbook}
                               labbookId={labbook.id}
                               setBuildingState={this._setBuildingState}
                               containerStatus={this.refs.ContainerStatus}
                               overview={labbook.overview}
                               isLocked={isLocked}
                               {...props}
                             />
                        </ErrorBoundary>)}
                    />

                    <Route
                      path={`${props.match.url}/code`}
                      render={() => (
                        <ErrorBoundary
                          type="labbookSectionError"
                          key="code">
                          <Code
                               labbook={labbook}
                               labbookId={labbook.id}
                               setContainerState={this._setContainerState}
                               isLocked={isLockedBrowser}
                               section={'code'}
                             />

                        </ErrorBoundary>)}
                    />

                    <Route
                      path={`${props.match.url}/inputData`}
                      render={() => (
                        <ErrorBoundary
                          type="labbookSectionError"
                          key="input">
                          <InputData
                               labbook={labbook}
                               labbookId={labbook.id}
                               isLocked={isLockedBrowser}
                               section={'input'}
                             />
                        </ErrorBoundary>)}
                    />

                    <Route
                      path={`${props.match.url}/outputData`}
                      render={() => (
                        <ErrorBoundary
                          type="labbookSectionError"
                          key="output">
                          <OutputData
                               labbook={labbook}
                               labbookId={labbook.id}
                               isLocked={isLockedBrowser}
                               section={'output'}
                             />
                        </ErrorBoundary>)}
                    />

                  </Switch>

                </Route>

              </Switch>

            </div>

          </div>
          <div className="Labbook__veil" />

        </div>);
    }

    if (state.authenticated) {
      return (<Loader />);
    }

    return (<Login auth={props.auth} />);
  }
}

const mapStateToProps = (state, ownProps) => state.labbook;

const mapDispatchToProps = dispatch => ({
});

const LabbookContainer = connect(mapStateToProps, mapDispatchToProps)(Labbook);


const LabbookFragmentContainer = createFragmentContainer(
  LabbookContainer,
  {
    labbook: graphql`
      fragment Labbook_labbook on Labbook{
          id
          description
          defaultRemote
          owner
          name
          creationDateUtc
          visibility

          environment{
            containerStatus
            imageStatus
            base{
              developmentTools
            }
          }

          overview{
            remoteUrl
            numAptPackages
            numConda2Packages
            numConda3Packages
            numPipPackages
          }

         branches {
           owner
           name
           branchName
           isActive
           isLocal
           isRemote
           isMergeable
           commitsBehind
           commitsAhead
         }

          ...Environment_labbook
          ...LabbookOverviewContainer_labbook
          ...LabbookActivityContainer_labbook
          ...Code_labbook
          ...Input_labbook
          ...Output_labbook

      }`,
  },

);

/** *
  * @param {Object} manager
  * data object for reactDND
*/

const backend = (manager) => {
  const backend = HTML5Backend(manager),
    orgTopDropCapture = backend.handleTopDropCapture;

  backend.handleTopDropCapture = (e) => {
    if (backend.currentNativeSource) {
      orgTopDropCapture.call(backend, e);
      backend.currentNativeSource.item.dirContent = getFilesFromDragEvent(e, { recursive: true }); // returns a promise
    }
  };

  return backend;
};

export default DragDropContext(backend)(LabbookFragmentContainer);

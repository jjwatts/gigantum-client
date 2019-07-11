// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
import { boundMethod } from 'autobind-decorator';
// store
import store from 'JS/redux/store';
import { setContainerState } from 'JS/redux/actions/labbook/overview/overview';
import { setContainerStatus, setContainerMenuVisibility } from 'JS/redux/actions/labbook/containerStatus';
import { setContainerMenuWarningMessage, setCloseEnvironmentMenus } from 'JS/redux/actions/labbook/environment/environment';
import { setPackageMenuVisible } from 'JS/redux/actions/labbook/environment/packageDependencies';
import { setBuildingState, setMergeMode, updateTransitionState } from 'JS/redux/actions/labbook/labbook';
import { setErrorMessage, setInfoMessage } from 'JS/redux/actions/footer';
// components
import Tooltip from 'Components/common/Tooltip';
// assets
import './ContainerStatus.scss';

class ContainerStatus extends Component {
  constructor(props) {
    super(props);

    this.state = {
      status: '',
      isMouseOver: false,
      showDevList: false,
      attemptingRebuild: false,
    };

    this._getContainerStatusText = this._getContainerStatusText.bind(this);
    this._containerAction = this._containerAction.bind(this);
    this._closePopupMenus = this._closePopupMenus.bind(this);
    this._rebuildContainer = this._rebuildContainer.bind(this);
  }

  static getDerivedStateFromProps(nextProps, state) {
    const displayTransitionState = nextProps.transitionState[nextProps.labbookName] && nextProps.transitionState[nextProps.labbookName].length;
    return ({
      ...state,
      status: displayTransitionState ? nextProps.transitionState[nextProps.labbookName] : state.status,
    });
  }

  /**
  *  @param {}
  *  clear interval to stop polling and clean up garbage
  */
  componentWillUnmount() {
    // memory clean up
    window.removeEventListener('click', this._closePopupMenus);
  }

  /**
  *  @param {}
  *  set fetch interval
  *  @return {string}
  */
  componentDidMount() {
    const { props } = this;
    const status = this._getContainerStatusText({
      containerStatus: props.containerStatus,
      imageStatus: props.imageStatus,
    });
    const hasLabbookId = store.getState().overview.containerStates[props.labbookId];

    if (hasLabbookId) {
      const storeStatus = store.getState().overview.containerStates[props.labbookId];

      if (storeStatus !== status) {
        props.setContainerState(props.labbookId, status);
      }
    }

    window.addEventListener('click', this._closePopupMenus);
  }


  /**
   *  @param {event} evt
   *  closes menu box when menu is open and the menu has not been clicked on
   *
  */
  _closePopupMenus(evt) {
    const { props, state } = this;
    // TODO fix this implementation, this is not sustainable.
    const containerMenuClicked = evt.target.getAttribute('data-container-popup') === 'true';

    if (!containerMenuClicked
    && props.containerMenuOpen) {
      props.setContainerMenuVisibility(false);
    }

    const pluginsMenuClicked = (evt.target.className.indexOf('ContainerStatus__plugins') > -1);
    if (!pluginsMenuClicked && state.pluginsMenu) {
      this.setState({
        pluginsMenu: false,
      });
    }

    if (state.showDevList && evt.target.className.indexOf('ContainerStatus__expand-tools') === -1) {
      this.setState({ showDevList: false });
    }
  }

  /**
    @param {}
    set containerStatus secondsElapsed state by iterating
    @return {string}
  */
  _checkJupyterStatus = (devTool) => {
    // update this when juphyter can accept cors

    setTimeout(() => {
      window.open('http://localhost:8888', '_blank');
    }, 5000);
  }

  /**
    @param {string, string} containerStatus,imageStatus -
    get status by mixing containrSatus imagesStatus and state.status
    @return {string}
  */
  _getContainerStatusText = ({ containerStatus, imageStatus }) => {
    const { props, state } = this;
    const labbookCreationDate = Date.parse(`${props.creationDateUtc}Z`);
    const timeNow = Date.parse(new Date());
    const timeDifferenceMS = timeNow - labbookCreationDate;

    let status = (containerStatus === 'RUNNING') ? 'Running' : containerStatus;
    status = (containerStatus === 'NOT_RUNNING') ? 'Stopped' : status;
    status = (imageStatus === 'BUILD_IN_PROGRESS' || imageStatus === 'BUILD_QUEUED') ? 'Building' : status;
    status = (imageStatus === 'BUILD_FAILED') ? 'Rebuild' : status;
    status = (imageStatus === 'DOES_NOT_EXIST') ? 'Rebuild' : status;
    status = ((imageStatus === 'DOES_NOT_EXIST') || props.isBuilding || (imageStatus === 'BUILD_IN_PROGRESS')) && (timeDifferenceMS < 15000) ? 'Building' : status;

    status = ((status === 'Stopped') && (state.status === 'Starting')) ? 'Starting' : status;
    status = ((status === 'Running') && (state.status === 'Stopping')) ? 'Stopping' : status;

    if (store.getState().containerStatus.status !== status) {
      props.setContainerStatus(status);
    }

    if ((status === 'Stopped') && state.attemptingRebuild) {
      this.setState({ attemptingRebuild: false });
      this._startContainerMutation(false);
    } else if (status === 'Rebuild' && state.attemptingRebuild) {
      this.setState({ attemptingRebuild: false });
    }

    if ((status) && (status !== 'Stopped') && (status !== 'Rebuild')) {
      props.setCloseEnvironmentMenus();
      setPackageMenuVisible(false);
    }
    let cssClass = status;
    const constainerStatus = (status === 'Rebuild') ? 'Stopped' : status;
    cssClass = ((cssClass === 'Building') && (state.status === 'Canceling')) ? 'Canceling' : cssClass;

    return { constainerStatus, cssClass };
  }

  /**
    @param {}
    triggers stop container mutation
  */
  _stopContainerMutation() {
    const { props } = this;
    const self = this;

    props.setContainerMenuVisibility(false);

    props.containerMutations.stopContainer(
      {},
      (response, error) => {
        self.setState({
          imageStatus: 'EXISTS',
          containerStatus: 'NOT_RUNNING',
        });

        if (error) {
          props.setErrorMessage(`There was a problem stopping ${self.state.labbookName} container`, error);
        }
      },
    );
  }

  /**
    @param {}
    triggers stop build mutation
  */
  @boundMethod
  _cancelBuildMutation() {
    const { props } = this;
    const self = this;

    props.setContainerMenuVisibility(false);
    props.containerMutations.cancelBuild(
      () => {
        setTimeout(() => {
          self.setState({
            status: '',
            contanerMenuRunning: false,
          });
        }, 3000);
      },
    );
  }

  /**
    @param {}
    triggers start container mutation
  */
  _startContainerMutation(launchDevTool) {
    const { state, props } = this;
    const self = this;
    const data = launchDevTool ? { devTool: state.selectedDevTool } : {};

    props.setCloseEnvironmentMenus();
    setPackageMenuVisible(false);
    props.setContainerMenuVisibility(false);

    props.containerMutations.startContainer(
      data,
      (response, error) => {
        self.setState({
          imageStatus: 'EXISTS',
          containerStatus: 'RUNNING',
        });

        if (error) {
          props.setErrorMessage(`There was a problem starting ${this.state.labbookName} container`, error);
          if (error[0].message.indexOf('404 Client Error') > -1) {
            self._rebuildContainer();
          }
        } else {
          props.setCloseEnvironmentMenus();
          setPackageMenuVisible(false);
        }
      },
    );
  }


  /**
    @param {string} status
    trigger mutatuion to stop or start container depdending on the state
    @return {string} newStatus
   */
  _containerAction(status, cssStatus, evt) {
    const { props } = this;

    if (!store.getState().labbook.isBuilding && !props.isLookingUpPackages) {
      if (status === 'Stop') {
        updateTransitionState(props.labbookName, 'Stopping');
        this.setState({ contanerMenuRunning: false });
        this._stopContainerMutation();
      } else if ((status === 'Start') && (cssStatus !== 'Rebuild')) {
        updateTransitionState(props.labbookName, 'Starting');
        this.setState({ contanerMenuRunning: false });
        props.setMergeMode(false, false);
        this._startContainerMutation();
      } else if ((status === 'Start') || (status === 'Rebuild')) {
        this.setState({
          status: 'Building',
          contanerMenuRunning: false,
        });
        this._rebuildContainer(evt, status);
      }
    } else {
      props.setContainerMenuWarningMessage('Can\'t start container when environment is being edited');
    }

    if ((status === 'Cancel')) {
      this.setState({
        status: 'Canceling',
        contanerMenuRunning: false,
      });
      this._cancelBuildMutation();
    }
  }

  /**
    @param {} value
    shows message plugin menu
  */
  _openPluginMenu() {
    this.setState((state) => {
      const pluginsMenu = !state.pluginsMenu;
      return {
        pluginsMenu,
      };
    });
  }

  /**
    @param {boolean} value
    trigger mutatuion to stop or start container depdending on the state
  */
  _setMouseOverState(value) {
    this.setState({ isMouseOver: value });
  }

  /**
    @param {string} status
    trigger mutatuion to stop or start container depdending on the state
    @return {string} newStatus
  */
  _getStatusText(status) {
    const { props, state } = this;
    let newStatus = status;

    newStatus = state.isMouseOver && (status === 'Running') ? 'Stop' : newStatus;
    newStatus = state.isMouseOver && ((status === 'Stopped')
      && !props.isLookingUpPackages) ? 'Start' : newStatus;
    newStatus = state.isMouseOver && (status === 'Rebuild') ? 'Rebuild' : newStatus;
    newStatus = state.isMouseOver && (status === 'Rebuild') ? 'Rebuild' : newStatus;

    newStatus = props.isBuilding
      ? 'Building' : props.isSyncing
      ? 'Syncing' : props.isPublishing
      ? 'Publishing' : newStatus;
    newStatus = (state.isMouseOver && (props.isBuilding || status === 'Building'))
      ? 'Cancel' : newStatus;
    newStatus = ((newStatus === 'Building' || newStatus === 'Cancel') && (state.status === 'Canceling'))
      ? 'Canceling' : newStatus;

    return newStatus;
  }

  /**
    @param {}
    triggers build image mutations with force === true
    @return {}
  */
  _rebuildContainer() {
    const { props } = this;
    const data = { noCache: true };

    props.setContainerMenuVisibility(false);

    this.setState({ imageStatus: 'BUILD_IN_PROGRESS', attemptingRebuild: true });

    props.containerMutations.buildImage(
      data,
      (response, error) => {
        if (error) {
          console.log(error);
        }
      },
    );
  }

  render() {
    const { props, state } = this;
    const { constainerStatus, cssClass } = this._getContainerStatusText(props);
    const key = 'setStatus';
    const excludeStatuses = ['Stopping', 'Starting', 'Publishing', 'Syncing'];
    const notExcluded = (excludeStatuses.indexOf(constainerStatus) === -1);
    const status = this._getStatusText(constainerStatus);

    const containerStatusCss = classNames({
      'ContainerStatus__container-state--menu-open': props.containerMenuOpen,
      'ContainerStatus__container-state': !props.containerMenuOpen,
      [cssClass]: !props.isBuilding && !props.isSyncing && !props.isPublishing,
      'Tooltip-data': (cssClass === 'Rebuild'),
      Building: (props.isBuilding || props.imageStatus === 'BUILD_IN_PROGRESS' || props.imageStatus === 'BUILD_QUEUED') && state.status !== 'Canceling',
      Canceling: state.status === 'Canceling' && ((props.isBuilding || props.imageStatus === 'BUILD_IN_PROGRESS' || props.imageStatus === 'BUILD_QUEUED')),
      Syncing: props.isSyncing,
      Publishing: props.isPublishing,
      LookingUp: props.isLookingUpPackages,
      'ContainerStatus__container-state--expanded': state.isMouseOver && notExcluded && !props.isBuilding && !(state.imageStatus === 'BUILD_IN_PROGRESS'),
      'ContainerStatus__container-remove-pointer': !notExcluded || props.isSyncing || props.isPublishing,
    });

    return (
      <div className="ContainerStatus flex flex--row">

        <div
          data-tooltip="Rebuild Required, container will attempt to rebuild before starting."
          onClick={evt => this._containerAction(status, cssClass, key)}
          key={key}
          className={containerStatusCss}
          onMouseOver={() => { this._setMouseOverState(true); }}
          onMouseOut={() => { this._setMouseOverState(false); }}
        >

          <div className="ContainerStatus__text">{ status }</div>
          <div className="ContainerStatus__toggle">
            <div className="ContainerStatus__toggle-btn" />
          </div>
        </div>

        { props.containerMenuOpen
          && <div className="ContainerStatus__menu-pointer" />
        }

        { props.containerMenuOpen
          && (
          <div className="ContainerStatus__button-menu" data-container-popup="true">
            { store.getState().environment.containerMenuWarning }
          </div>
          )
        }

        <Tooltip
          section="containerStatus"
        />
      </div>);
  }
}

const mapStateToProps = (state, ownProps) => ({
  containerMenuOpen: state.containerStatus.containerMenuOpen,
  isLookingUpPackages: state.containerStatus.isLookingUpPackages,
});

const mapDispatchToProps = dispatch => ({
  setContainerState,
  setContainerStatus,
  setContainerMenuVisibility,
  setBuildingState,
  setErrorMessage,
  setCloseEnvironmentMenus,
  setInfoMessage,
  setMergeMode,
  setContainerMenuWarningMessage,
});

export default connect(mapStateToProps, mapDispatchToProps)(ContainerStatus);

// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
import { boundMethod } from 'autobind-decorator';
// store
import store from 'JS/redux/store';
import { setContainerState } from 'JS/redux/reducers/labbook/overview/overview';
import { setContainerStatus, setContainerMenuVisibility } from 'JS/redux/reducers/labbook/containerStatus';
import { setContainerMenuWarningMessage, setCloseEnvironmentMenus } from 'JS/redux/reducers/labbook/environment/environment';
import { setPackageMenuVisible } from 'JS/redux/reducers/labbook/environment/packageDependencies';
import { setBuildingState, setMergeMode } from 'JS/redux/reducers/labbook/labbook';
import { setErrorMessage, setInfoMessage, setWarningMessage } from 'JS/redux/reducers/footer';
// components
import ToolTip from 'Components/common/ToolTip';
// assets
import './ContainerStatus.scss';


function Bounce(w) {
  window.blur();
  w.focus();
}

class ContainerStatus extends Component {
  constructor(props) {
    super(props);

    this.state = {
      status: '',
      secondsElapsed: 0,
      isMouseOver: false,
      rebuildAttempts: 0,
      showDevList: false,
      showInitialMessage: false,
      previousContainerStatus: props.containerStatus,
    };

    this._getContainerStatusText = this._getContainerStatusText.bind(this);
    this._containerAction = this._containerAction.bind(this);
    this._closePopupMenus = this._closePopupMenus.bind(this);
    this._rebuildContainer = this._rebuildContainer.bind(this);
  }

  static getDerivedStateFromProps(nextProps, state) {
    // const status = (state.previousContainerStatus === nextProps.containerStatus) ? nextProps.status : '';
    return ({
      ...state,
      status: nextProps.stateStatus,
      previousContainerStatus: nextProps.containerStatus,
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
    props.auth.isAuthenticated().then((response) => {
      const containerMessageShown = localStorage.getItem('containerMessageShown');
      if (!containerMessageShown && response) {
        this.setState({ showInitialMessage: true });
        localStorage.setItem('containerMessageShown', true);
      }
    });

    const status = this._getContainerStatusText({
      containerStatus: this.props.containerStatus,
      imageStatus: this.props.imageStatus,
    });

    const hasLabbookId = store.getState().overview.containerStates[this.props.labbookId];

    if (hasLabbookId) {
      const storeStatus = store.getState().overview.containerStates[this.props.labbookId];

      if (storeStatus !== status) {
        this.props.setContainerState(this.props.labbookId, status);
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
    // TODO fix this implementation, this is not sustainable.
    const containerMenuClicked = evt.target.getAttribute('data-container-popup') === 'true';

    if (!containerMenuClicked &&
    this.props.containerMenuOpen) {
      this.props.setContainerMenuVisibility(false);
    }
    if (this.state.showInitialMessage) {
      this.setState({ showInitialMessage: false });
    }

    const pluginsMenuClicked = (evt.target.className.indexOf('ContainerStatus__plugins') > -1);
    if (!pluginsMenuClicked && this.state.pluginsMenu) {
      this.setState({
        pluginsMenu: false,
      });
    }

    if (this.state.showDevList && evt.target.className.indexOf('ContainerStatus__expand-tools') === -1) {
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
    const labbookCreationDate = Date.parse(`${this.props.creationDateUtc}Z`);
    const timeNow = Date.parse(new Date());

    const timeDifferenceMS = timeNow - labbookCreationDate;

    let status = (containerStatus === 'RUNNING') ? 'Running' : containerStatus;
    status = (containerStatus === 'NOT_RUNNING') ? 'Stopped' : status;
    status = (imageStatus === 'BUILD_IN_PROGRESS') ? 'Building' : status;
    status = (imageStatus === 'BUILD_FAILED') ? 'Rebuild' : status;
    status = (imageStatus === 'DOES_NOT_EXIST') ? 'Rebuild' : status;
    status = ((imageStatus === 'DOES_NOT_EXIST') || (imageStatus === 'BUILD_IN_PROGRESS')) && (timeDifferenceMS < 15000) ? 'Building' : status;

    status = ((status === 'Stopped') && (state.status === 'Starting')) ? 'Starting' : status;
    status = ((status === 'Running') && (state.status === 'Stopping')) ? 'Stopping' : status;

    if (store.getState().containerStatus.status !== status) {
      this.props.setContainerStatus(status);
    }

    if ((status) && (status !== 'Stopped') && (status !== 'Rebuild')) {
      this.props.setCloseEnvironmentMenus();
      setPackageMenuVisible(false);
    }

    return status;
  }

  /**
    @param {}
    triggers stop container mutation
  */
  _stopContainerMutation() {
    const { props, state } = this;

    props.setContainerMenuVisibility(false);

    const self = this;

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
    triggers start container mutation
  */
  _startContainerMutation(launchDevTool) {
    const { state, props } = this,
          self = this,
          data = launchDevTool ? { devTool: state.selectedDevTool } : {};

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
          this.props.setErrorMessage(`There was a problem starting ${this.state.labbookName} container`, error);
          if (error[0].message.indexOf('404 Client Error') > -1) {
            self._rebuildContainer();
          }
        } else {
          this.props.setCloseEnvironmentMenus();
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
  _containerAction(status, evt) {
    const { props, state } = this;
    if (!store.getState().labbook.isBuilding && !props.isLookingUpPackages) {
      if (status === 'Stop') {
        props.updateStatus('Stopping');

        this.setState({ contanerMenuRunning: false });
        this._stopContainerMutation();
      } else if (status === 'Run') {
        props.updateStatus('Starting');

        this.setState({ contanerMenuRunning: false });

        props.setMergeMode(false, false);
        this._startContainerMutation();
      } else if ((status === 'Rebuild') || (status === 'Rebuild')) {
        this.setState({
          status: 'Building',
          contanerMenuRunning: false,
        });

        this._rebuildContainer(evt, status);
      }
    } else {
      props.setContainerMenuWarningMessage('Can\'t start container when environment is being edited');
    }
  }

  /**
    @param {} value
    shows message plugin menu
  */
  _openPluginMenu() {
    const { state } = this;
    this.setState({
      pluginsMenu: !state.pluginsMenu,
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
    newStatus = state.isMouseOver && ((status === 'Stopped') && !props.isLookingUpPackages) ? 'Run' : newStatus;
    newStatus = state.isMouseOver && (status === 'Rebuild') ? 'Rebuild' : newStatus;
    newStatus = state.isMouseOver && (status === 'Rebuild') ? 'Rebuild' : newStatus;

    newStatus = props.isBuilding ? 'Building' : props.isSyncing ? 'Syncing' : props.isPublishing ? 'Publishing' : newStatus;

    return newStatus;
  }
  /**
    @param {}
    triggers build image mutations with force === true
    @return {}
  */
  _rebuildContainer() {
    const { props, state } = this,
          { labbookName, owner } = state,
          self = this,
          data = { noCache: true };

    props.setContainerMenuVisibility(false);

    this.setState({ imageStatus: 'BUILD_IN_PROGRESS' });

    props.containerMutations.buildImage(
      data,
      (response, error) => {
        if (error) {
          console.log(error);
        }

        self.setState({ rebuildAttempts: state.rebuildAttempts + 1 });

        if ((state.status === 'Starting') && (state.rebuildAttempts < 1)) {
          self._startContainerMutation();
        } else {
          self.setState({
            rebuildAttempts: 0,
            status: '',
          });
        }
      },
    );
  }

  render() {
    const { props, state } = this,
          status = this._getContainerStatusText(props),
          key = 'setStatus',
          excludeStatuses = ['Stopping', 'Starting', 'Building', 'Publishing', 'Syncing'],
          notExcluded = excludeStatuses.indexOf(status) === -1,
          textStatus = this._getStatusText(status);

    const containerStatusCss = classNames({
      'ContainerStatus__container-state--menu-open': props.containerMenuOpen,
      'ContainerStatus__container-state': !props.containerMenuOpen,
      [status]: !props.isBuilding && !props.isSyncing && !props.isPublishing,
      Building: props.isBuilding || state.imageStatus === 'BUILD_IN_PROGRESS',
      Syncing: props.isSyncing,
      Publishing: props.isPublishing,
      LookingUp: props.isLookingUpPackages,
      'ContainerStatus__container-state--expanded': state.isMouseOver && notExcluded && !props.isBuilding && !(state.imageStatus === 'BUILD_IN_PROGRESS'),
      'ContainerStatus__container-remove-pointer': !notExcluded || props.isBuilding || (props.imageStatus === 'BUILD_IN_PROGRESS') || props.isSyncing || props.isPublishing,
    });

    return (
      <div className="ContainerStatus flex flex--row">

        <div
          onClick={evt => this._containerAction(textStatus, key)}
          key={key}
          className={containerStatusCss}
          onMouseOver={() => { this._setMouseOverState(true); }}
          onMouseOut={() => { this._setMouseOverState(false); }}>

          {this._getStatusText(textStatus)}

        </div>

        { state.showInitialMessage
          && <Fragment>
            <div className="ContainerStatus__initial-pointer" />
            <div className="ContainerStatus__initial-menu">
              This shows the current status of your project. To start a Project click on the status indicator or select the development tool that you wish to launch.
            </div>
          </Fragment>
        }

        { props.containerMenuOpen
          && <div className="ContainerStatus__menu-pointer" />
        }

        { props.containerMenuOpen
          && <div className="ContainerStatus__button-menu" data-container-popup="true">
            { store.getState().environment.containerMenuWarning }
          </div>
        }

        <ToolTip
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

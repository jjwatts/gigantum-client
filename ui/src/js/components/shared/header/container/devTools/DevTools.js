// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { boundMethod } from 'autobind-decorator';
// store
import store from 'JS/redux/store';
import { setContainerState } from 'JS/redux/reducers/labbook/overview/overview';
import { setContainerStatus, setContainerMenuVisibility } from 'JS/redux/reducers/labbook/containerStatus';
import { setContainerMenuWarningMessage, setCloseEnvironmentMenus } from 'JS/redux/reducers/labbook/environment/environment';
import { setPackageMenuVisible } from 'JS/redux/reducers/labbook/environment/packageDependencies';
import { setBuildingState, setMergeMode } from 'JS/redux/reducers/labbook/labbook';
import { setErrorMessage, setInfoMessage, setWarningMessage } from 'JS/redux/reducers/footer';
// assets
import './DevTools.scss';

class DevTools extends Component {

  state = {
    isMouseOver: false,
    selectedDevTool: 'jupyterlab',
    showDevList: false,
  }

  componentDidMount() {
    window.addEventListener('click', this._closeDevtoolMenu);
  }

  componentWillUnmount() {
    window.removeEventListener('click', this._closeDevtoolMenu);
  }

  /**
  *  @param {Object} evt
  *  closes dev tool
  *  @return {}
  */
  @boundMethod
  _closeDevtoolMenu(evt) {
    if (evt.target.className.indexOf('DevTool') < 0) {
       this.setState({ showDevList: false });
    }
  }

  /**
  *  @param {Object} evt
  *  upodates state if the conditions are met
  *  @return {}
  */
  @boundMethod
  _toggleDevtoolMenu(evt) {
    const { state } = this;
    this.setState({ showDevList: !state.showDevList });
  }

  /**
  *  @param {string} developmentTool
  *  @param {string} developmentTool
  *  mutation to trigger opening of development tool
  *  @return {}
  */
  @boundMethod
  _openDevToolMuation(developmentTool) {
    const { props, state } = this,
          { containerStatus, imageStatus } = props,
          { owner, name } = props.labbook,
          tabName = `${developmentTool}-${owner}-${name}`;

    const labbookCreationDate = Date.parse(`${this.props.creationDateUtc}Z`);
    const timeNow = Date.parse(new Date());

    const timeDifferenceMS = timeNow - labbookCreationDate;

    let status = (containerStatus === 'RUNNING') ? 'Running' : containerStatus;
    status = (containerStatus === 'NOT_RUNNING') ? 'Stopped' : status;
    status = (imageStatus === 'BUILD_IN_PROGRESS') ? 'Building' : status;
    status = (imageStatus === 'BUILD_FAILED') ? 'Rebuild' : status;
    status = (imageStatus === 'DOES_NOT_EXIST') ? 'Rebuild' : status;
    status = ((imageStatus === 'DOES_NOT_EXIST') || (imageStatus === 'BUILD_IN_PROGRESS')) && (timeDifferenceMS < 15000) ? 'Building' : status;

    if ((status !== 'Stopped') && (status !== 'Running')) {
      setWarningMessage('Could not launch development environment as the project is not ready.');
    } else if (status === 'Stopped') {
      setInfoMessage('Starting Project container. When done working, click Stop to shutdown the container.');
      this.setState({
        status: 'Starting',
        contanerMenuRunning: false,
      });
      setMergeMode(false, false);
      props.updateStatus('Starting');
      props.containerMutations.startContainer({ devTool: developmentTool }, (response, error) => {
        if (error) {
          setErrorMessage('Error Starting Dev tool', error);
        }

        if (response.startDevTool) {
          const tabName = `${developmentTool}-${owner}-${name}`;
          let path = `${window.location.protocol}//${window.location.hostname}${response.startDevTool.path}`;
          if (developmentTool === 'Notebook') {
            if (path.includes('/lab/tree')) {
              path = path.replace('/lab/tree', '/tree');
            } else {
              path = `${path}/tree/code`;
            }
          }

          window[tabName] = window.open(path, tabName);
        }
      });

    } else if (window[tabName] && !window[tabName].closed) {
      window[tabName].focus();
    } else {
      setInfoMessage(`Starting ${developmentTool}, make sure to allow popups.`);
      const data = { devTool: developmentTool };
      props.containerMutations.startDevTool(
        data,
        (response, error) => {
          if (response.startDevTool) {
            const tabName = `${developmentTool}-${owner}-${name}`;
            let path = `${window.location.protocol}//${window.location.hostname}${response.startDevTool.path}`;
            if (developmentTool === 'Notebook') {
              if (path.includes('/lab/tree')) {
                path = path.replace('/lab/tree', '/tree');
              } else {
                path = `${path}/tree/code`;
              }
            }

            window[tabName] = window.open(path, tabName);
          }

          if (error) {
            setErrorMessage('Error Starting Dev tool', error);
          }
        },
      );
    }
  }

  /**
  *  @param {string} developmentTool
  *  mutation to trigger opening of development tool
  *  @return {}
  */
  @boundMethod
  _selectDevTool(developmentTool) {
     this.setState({ selectedDevTool: developmentTool, showDevList: false });
     this._openDevToolMuation(developmentTool);
  }

  render() {
    const { props, state } = this,
          devTools = props.labbook.environment.base.developmentTools,
          jupyterButtonCss = classNames({
            'DevTools-button': true,
            'ContainerStatus__button--bottom': state.isMouseOver,
          }),
          containerMenuCSS = classNames({
            'DevTools-menu': true,
            hidden: !state.showDevList,
            'DevTools-menu--hover': state.isMouseOver,
          }),
          expandToolsCSS = classNames({
            'ContainerStatus__expand-tools': true,
            'ContainerStatus__expand-tools--open': state.showDevList,
          }),
          devtToolMenuCSS = classNames({
            'DevTools__dropdown-menu': true,
            hidden: !state.showDevList,
          }),
          buttonDropdownCSS = classNames({
            'DevTools__btn DevTools__btn--dropdown': true,
            'DevTools__btn--open': state.showDevList,
          });

    return (
        <div className="DevTools">
          <div className="DevTools__flex">
            <button
              type="submit"
              className="DevTools__btn DevTools__btn--launch Btn--columns"
              onClick={() => { this._openDevToolMuation(state.selectedDevTool); }}>
                <div className="Btn--label">Launch:</div>
                <div className="Btn--text">{state.selectedDevTool}</div>
            </button>

            <button
              data-id="DevToolDropdown"
              className={buttonDropdownCSS}
                 onClick={ evt => this._toggleDevtoolMenu(evt) }>
            </button>

          </div>

          <div className={devtToolMenuCSS}>
            <div className="DevTool__menu-title">Launch</div>
            <ul className="DevTool__list">
              {

                devTools.map((developmentTool) => {
                  const devToolsCss = classNames({
                    DevTools__item: true,
                    'DevTools__item--selected': (developmentTool === state.selectedDevTool),
                  });

                  return (<li
                    key={developmentTool}
                    className={devToolsCss}
                    onClick={() => this._selectDevTool(developmentTool)}>
                    <div className="DevTools__icon jupyter-icon"></div>
                    <div className="DevTools__text">{developmentTool}</div>
                  </li>);
                })
              }
            </ul>
          </div>
        </div>
    );
  }
}

export default DevTools;

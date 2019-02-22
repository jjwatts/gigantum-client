// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { Link } from 'react-router-dom';
import { boundMethod } from 'autobind-decorator';
import shallowCompare from 'react-addons-shallow-compare';
// config
import Config from 'JS/config';
// store
import store from 'JS/redux/store';
import {
  setSyncingState,
  setPublishingState,
  setExportingState,
  setModalVisible,
  setUpdateDetailView,
} from 'JS/redux/reducers/labbook/labbook';
// components
import ToolTip from 'Components/common/ToolTip';
import SidePanel from './SidePanel';
// assets
import './Branches.scss';

class Branches extends Component {
  state = {
    sidePanelVisible: this.props.sidePanelVisible,
    selectedBranchname: null,
    action: null,
    mergeModalVisible: false,
    deleteModalVisible: false,
    resetModalVisible: false,
    localSelected: false,
    remoteSelected: false,
    branchPage: 0,
  }

  static getDerivedStateFromProps(nextProps, state) {
     return ({
       sidePanelVisible: nextProps.sidePanelVisible,
       ...state,
     });
  }

  shouldComponentUpdate(nextProps, nextState) {
    return shallowCompare(this, nextProps, nextState);
  }

  componentDidMount() {
    window.addEventListener('click', this._closePopups);
  }

  componentWillUnmount() {
    window.removeEventListener('click', this._closePopups);
  }

    /**
    @param {} -
    sets state to toggle the switch dropdown
    @return {}
  */
  @boundMethod
  _closePopups(evt) {
      const { state } = this;
      if (evt.target.className.indexOf('Branches__btn--sync-dropdown') < 0) {
        this.setState({
          syncMenuVisible: false,
        });
      }
  }

  /**
    @param {String} modalName
    reverts state of passed in modalname
    @return {}
  */
  _toggleModal(modalName, branch) {
    if ((modalName === 'mergeModal') && (this.props.activeBranch.branchName !== branch)) {
      this.setState({ mergeModalVisible: branch || !this.state.mergeModalVisible });
    } else if ((modalName === 'deleteModal') && (this.props.activeBranch.branchName !== branch) && (branch !== 'master')) {
      this.setState({ deleteModalVisible: branch || !this.state.deleteModalVisible, localSelected: false, remoteSelected: false });
    } else if ((modalName === 'resetModal') && (!branch || (this.props.activeBranch.branchName === branch))) {
      const upToDate = (this.props.activeBranch.commitsAhead === 0) && (this.props.activeBranch.commitsBehind === 0);
      if (this.props.activeBranch.isRemote && !upToDate) {
      this.setState({ resetModalVisible: branch || !this.state.resetModalVisible });
      }
    }
  }
    /**
    @param {Object} branch
    @param {String} action
    Handles confirm button by doing appropriate action
    @return {}
  */
  _handleConfirm(branch, action) {
    if (action === 'merge') {
      this._mergeBranch(branch);
    } else if (action === 'delete') {

    } else if (action === 'reset') {
      this._resetBranch(branch);
    }
  }
  /**
    @param {Event} evt
    @param {String} selectedBranchname
    sets selected branch in state
    @return {}
  */
  _selectBranchname(evt, selectedBranchname) {
      if (this.state.selectedBranchname !== selectedBranchname) {
        this.setState({ selectedBranchname });
      }
  }
  /**
    @param {} -
    sets state to toggle the switch dropdown
    @return {}
  */
  @boundMethod
  _toggleSyncDropdown() {
    if (this.props.allowSync) {
      const { state } = this;
      this.setState({ syncMenuVisible: !state.syncMenuVisible });
    }
  }
  /**
      @param {Object} branches
      filters array branhces and return the active branch node
    */
  @boundMethod
  _switchBranch(branch) {
    if (!branch.isActive) {
      const { props } = this,
          self = this,
          data = {
            branchName: branch.branchName,
          };
      this.setState({
        action: 'Switching Branches',
      });
      props.branchMutations.switchBranch(data, (response, error) => {
        self.setState({ action: null });
      });
    }
  }
  /**
    @param {Object} branches
    filters array branhces and return the active branch node
  */
  @boundMethod
  _mergeBranch(branch) {
    const { props } = this,
          self = this,
          data = {
            branchName: branch.branchName,
          };
      this.setState({
        action: 'Merging Branches',
      });
      props.branchMutations.mergeBranch(data, (response, error) => {
        if (error) {
          console.log(error)
        }
        self.setState({ action: null, mergeModalVisible: null });
      });
  }
  /**
    @param {Object} branches
    filters array branhces and return the active branch node
  */
  @boundMethod
  _resetBranch(branch) {
    const self = this;
    this.setState({
      action: 'Resetting Branch',
    });
    this.props.branchMutations.resetBranch((response, error) => {
      if (error) {
        console.log(error)
      }
      self.setState({ action: null, resetModalVisible: null });
    });
  }
  /**
    @param {Object} branch
    @param {String} action
    renders JSX for modal
    @return {JSX}
  */
  _renderModal(branch, action) {
    const headerText = action === 'merge' ? 'Merge Branches' : action === 'delete' ? 'Delete Branch' : action === 'reset' ? 'Reset Branch' : '';
    return (
      <Fragment>
        <div className={`Branches__Modal Branches__Modal--${action}`}>
          <div
            className="Branches__close"
            onClick={() => this._toggleModal(`${action}Modal`)}
          />
          <div className="Branches__Modal-header">
            {headerText}
          </div>
          <div className="Branches__Modal-text">
            {
              action === 'merge'
              &&
              <Fragment>
                You are about to merge the branch
                <b>{` ${branch.branchName} `}</b>
                with the current branch
                <b>{` ${this.props.activeBranch.branchName}`}</b>
                . Click 'Confirm' to proceed.
              </Fragment>
            }
            {
              action === 'delete'
              &&
              <Fragment>
                You are about to delete this branch. This action can lead to data loss. Please type
                <b>{` ${branch.branchName} `}</b>
                and click 'Confirm' to proceed.
              </Fragment>
            }
            {
              action === 'reset' &&
              <Fragment>
                You are about to reset this branch. Resetting a branch will get rid of local changes. Click 'Confirm' to proceed.
              </Fragment>
            }
          </div>
          {
            action === 'delete' &&
            <div className="Branches__input-container">
            <label
              htmlFor="delete_local"
            >
              <input
                type="checkbox"
                name="delete_local"
                defaultChecked={!branch.isLocal}
                disabled={!branch.isLocal}
                onClick={() => this.setState({ localSelected: !this.state.localSelected })}
              />
              Local
             </label>
             <label
              htmlFor="delete_remote"
            >
              <input
                type="checkbox"
                name="delete_remote"
                defaultChecked={!branch.isRemote}
                disabled={!branch.isRemote}
                onClick={() => this.setState({ remoteSelected: !this.state.remoteSelected })}
              />
              Remote
            </label>
            </div>
          }
          <div className="Branches__Modal-buttons">
            <button
              onClick={() => this._toggleModal(`${action}Modal`)}
              className="Btn--flat"
            >
              Cancel
            </button>
            <button
              className="Branches__Modal-confirm"
              onClick={() => this._handleConfirm(branch, action)}
            >
              Confirm
            </button>
          </div>
        </div>
      </Fragment>
    );
  }
  /**
    @param {Object} branch
    renders JSX for actions section
    @return {JSX}
  */
  _renderActions(branch) {
    const { props, state } = this;
    const mergeModalVisible = this.state.mergeModalVisible === branch.branchName;
    const deleteModalVisible = this.state.deleteModalVisible === branch.branchName;
    const resetModalVisible = this.state.resetModalVisible === branch.branchName;
    const upToDate = (branch.commitsAhead === 0) && (branch.commitsBehind === 0);
    const mergeButtonCSS = classNames({
      Branches__btn: true,
      'Tooltip-data': true,
     ' Tooltip-data--small': true,
      'Branches__btn--merge': true,
      'Branches__btn--merge--disabled': branch.isActive,
      'Branches__btn--merge--selected': mergeModalVisible,
    }),
    deleteButtonCSS = classNames({
      Branches__btn: true,
      'Tooltip-data': true,
     ' Tooltip-data--small': true,
      'Branches__btn--delete': true,
      'Branches__btn--delete--disabled': branch.isActive || branch.branchName === 'master',
      'Branches__btn--delete--selected': deleteModalVisible,
    }),
    switchButtonCSS = classNames({
      Branches__btn: true,
      'Tooltip-data': true,
     ' Tooltip-data--small': true,
      'Branches__btn--switch': true,
      'Branches__btn--switch--disabled': branch.isActive,
    }),
    resetButtonCSS = classNames({
      Branches__btn: true,
      'Tooltip-data': true,
     ' Tooltip-data--small': true,
      'Branches__btn--reset': true,
      'Branches__btn--reset--disabled': !branch.isRemote || upToDate,
    }),
    syncButtonCSS = classNames({
      Branches__btn: true,
      'Tooltip-data': true,
     ' Tooltip-data--small': true,
      'Branches__btn--sync': true,
      'Branches__btn--sync--disabled': !props.allowSync,
    }),
    syncMenuDropdownButtonCSS = classNames({
      'Branches__btn Branches__btn--sync-dropdown': true,
      'Branches__btn--sync-dropdown--disabled': !props.allowSync,
      'Branches__btn--sync-open': state.syncMenuVisible,
    }),
    syncMenuDropdownCSS = classNames({
      'Branches__dropdown-menu': state.syncMenuVisible,
      hidden: !state.syncMenuVisible,
    });
    let resetTooltip = branch.isRemote ? upToDate ? 'Branch up to date' : 'Reset' : 'Branch must be remote';
    let syncTooltip = props.syncTooltip;
    let mergeTooltip = branch.isActive ? 'Cannot merge active branch with itself' : 'Merge';
    let deleteTooltip = branch.branchName === 'master' ? 'Cannot delete master branch' : branch.isActive ? 'Cannot delete Active branch' : 'Delete';
    return (
      <div className="Branches__actions-section">
        {
          branch.isActive ?
          <Fragment>
            <button
              className="Branches__btn Branches__btn--create"
              onClick={() => props.toggleModal('createBranchVisible') }
            />
            <button
              className={resetButtonCSS}
              data-tooltip={resetTooltip}
              onClick={() => this._toggleModal('resetModal', branch.branchName) }
            />
            <button
              className={syncButtonCSS}
              data-tooltip={syncTooltip}
              onClick={() => props.handleSyncButton(true, props.allowSync) }
            />
            <button
              className={syncMenuDropdownButtonCSS}
              onClick={() => { this._toggleSyncDropdown(); }}
            />
            <div className={syncMenuDropdownCSS}>
              <h5 className="Branches__h5">Sync</h5>
              <ul className="Branches__ul">
                <li
                    className="Branches__list-item"
                    onClick={() => props.handleSyncButton(false, props.allowSync)}>
                    Push & Pull
                </li>
                <li
                    className="Branches__list-item"
                    onClick={() => props.handleSyncButton(true, props.allowSync)}>
                    Pull-only
                </li>
              </ul>
            </div>
          </Fragment>
          :
          <Fragment>
            <button
              className={switchButtonCSS}
              data-tooltip="Switch"
              onClick={() => this._switchBranch(branch) }
            />
            <button
              className={mergeButtonCSS}
              data-tooltip={mergeTooltip}
              onClick={() => this._toggleModal('mergeModal', branch.branchName) }
             />
            <button
              className={deleteButtonCSS}
              data-tooltip={deleteTooltip}
              onClick={() => this._toggleModal('deleteModal', branch.branchName) }
              />
          </Fragment>
        }
        {mergeModalVisible && this._renderModal(branch, 'merge')}
        {deleteModalVisible && this._renderModal(branch, 'delete')}
        {resetModalVisible && this._renderModal(branch, 'reset')}
    </div>);
  }

  render() {
    const { props, state } = this,
          currentBranchNameCSS = classNames({
            'Branches__current-branchname': true,
            // TODO change based on commits ahead & behind
            'Branches__current-branchname--changed': false,
          }),
          currentBranchContainerCSS = classNames({
            'Branches__branch--current': true,
            'Branches__branch--current--selected': state.mergeModalVisible || state.resetModalVisible,
          }),
          modalCoverCSS = classNames({
            'Branches__Modal-cover': true,
            'Branches__Modal-cover--coverall': state.action,
          })
    const filteredBranches = props.branches.filter(branch => branch.branchName !== props.activeBranch.branchName);
    const statusText = props.activeBranch.isLocal ? props.activeBranch.isRemote ? 'Local & Remote' : 'Local only' : 'Remote only';
    return (
      <div>
      { props.sidePanelVisible
        && <SidePanel
            toggleSidePanel={props.toggleSidePanel}
            isSticky={props.isSticky}
            renderContent={() => <div className="Branches">
                {
                  (state.mergeModalVisible || state.deleteModalVisible || state.resetModalVisible || state.action) &&
                  <div className={modalCoverCSS}>
                    {
                      state.action &&
                      <div>
                        {`${state.action}...`}
                      </div>
                    }
                  </div>
                }
                <div className="Branches__header">
                  <div className="Branches__title">Manage Branches</div>
                </div>
              <div className="Branches__label">Current Branch:</div>
              <div className={currentBranchContainerCSS}>
                <div className="Branches__base-section">
                  <div className="Branches__branchname-container">
                    <div className="Branches__branchname">{props.activeBranch.branchName}</div>
                    <div
                      className="Branches__status Tooltip-data Tooltip-data--small"
                      data-tooltip={statusText}
                    >
                      {
                        props.activeBranch.isLocal ?
                        <div className="Branches__status--local"></div>
                        :
                        <div></div>
                      }
                      {
                        props.activeBranch.isRemote ?
                        <div className="Branches__status--remote"></div>
                        :
                        <div></div>
                      }
                      </div>
                  </div>
                </div>
                {
                  this._renderActions(props.activeBranch)
                }
              </div>
              {
                filteredBranches.length !== 0 &&
                <div className="Branches__label">Other Branches:</div>
              }
              {
                filteredBranches.map((branch) => {
                  const mergeModalVisible = this.state.mergeModalVisible === branch.branchName;
                  const deleteModalVisible = this.state.deleteModalVisible === branch.branchName;
                  const branchStatusText = branch.isLocal ? branch.isRemote ? 'Local & Remote' : 'Local only' : 'Remote only',
                  branchContainerCSS = classNames({
                    Branches__branch: true,
                    'Branches__branch--selected': (branch.branchName === state.mergeModalVisible) || (branch.branchName === state.deleteModalVisible),
                    'Branches__branch--active': ((state.selectedBranchname === branch.branchName) || mergeModalVisible || deleteModalVisible),
                  }),
                  branchBaseSectionCSS = classNames({
                    'Branches__base-section': true,
                  });
                  return (
                    <div
                      key={branch.branchName}
                      className={branchContainerCSS}
                      onMouseEnter={evt => this._selectBranchname(evt, branch.branchName)}
                      onMouseLeave={evt => this._selectBranchname(evt, null)}
                    >
                      <div className={branchBaseSectionCSS}>
                        <div className="Branches__branchname-container">
                          <div className="Branches__branchname">{branch.branchName}</div>
                          <div
                            className="Branches__status Tooltip-data Tooltip-data--small"
                            data-tooltip={branchStatusText}

                          >
                          {
                            branch.isLocal ?
                            <div className="Branches__status--local"></div>
                            :
                            <div></div>
                          }
                          {
                            branch.isRemote ?
                            <div className="Branches__status--remote"></div>
                            :
                            <div></div>
                          }
                          </div>
                        </div>
                      </div>
                      {
                        ((state.selectedBranchname === branch.branchName) || mergeModalVisible || deleteModalVisible) &&
                        this._renderActions(branch)
                      }
                    </div>
                  );
                })
              }

            </div>
          }
           />
      }
      </div>
    );
  }
}

export default Branches;

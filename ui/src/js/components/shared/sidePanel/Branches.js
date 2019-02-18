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
    localSelected: false,
    remoteSelected: false,
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
  /**
    @param {String} modalName
    reverts state of passed in modalname
    @return {}
  */
  _toggleModal(modalName, branch) {
    if (modalName === 'mergeModal' && this.props.activeBranch.branchName !== branch) {
      this.setState({ mergeModalVisible: branch || !this.state.mergeModalVisible });
    } else if (modalName === 'deleteModal' && this.props.activeBranch.branchName !== branch) {
      this.setState({ deleteModalVisible: branch || !this.state.deleteModalVisible, localSelected: false, remoteSelected: false });
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
  _syncBranch(branch) {
    if (branch.isActive) {
      const { props } = this,
          self = this,
          data = {
            successCall: () => {
              self.setState({ action: null, mergeModalVisible: null });
            },
            failureCall: () => {
              self.setState({ action: null, mergeModalVisible: null });
            },
          };
      this.setState({
        action: 'Syncing Branch',
      });
      props.branchMutations.syncLabbook(data, (response, error) => {
        if (error) {
          console.log(error)
        }
      });
    }
  }
  /**
    @param {Object} branches
    filters array branhces and return the active branch node
  */
  @boundMethod
  _resetBranch(branch) {
    const upToDate = (branch.commitsAhead === 0) && (branch.commitsBehind === 0);

    if (!branch.isRemote || upToDate) {
      const self = this;
      this.setState({
        action: 'Syncing Branch',
      });
      props.branchMutations.resetBranch((response, error) => {
        if (error) {
          console.log(error)
        }
        self.setState({ action: null, mergeModalVisible: null });
      });
    }
  }
  /**
    @param {Object} branch
    @param {String} action
    renders JSX for modal
    @return {JSX}
  */
  _renderModal(branch, action) {
    const headerText = action === 'merge' ? 'Merge Branches' : action === 'delete' ? 'Delete Branch' : '';
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
    const mergeModalVisible = this.state.mergeModalVisible === branch.branchName;
    const deleteModalVisible = this.state.deleteModalVisible === branch.branchName;
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
      'Branches__btn--sync--disabled': !branch.isActive,
    });
    let resetTooltip = branch.isRemote ? upToDate ? 'Branch up to date' : 'Reset' : 'Branch must be remote';
    let syncTooltip = branch.isActive ? 'Sync' : 'Syncing limited to active branch';
    let mergeTooltip = branch.isActive ? 'Cannot merge active branch with itself' : 'Merge';
    let deleteTooltip = branch.branchName === 'master' ? 'Cannot delete master branch' : branch.isActive ? 'Cannot delete Active branch' : 'Delete';
    return (
      <div className="Branches__actions-section">
        <button
          className={switchButtonCSS}
          data-tooltip="Switch"
          onClick={() => this._switchBranch(branch) }
        />
        <button
          className={resetButtonCSS}
          data-tooltip={resetTooltip}
          onClick={() => this._resetBranch(branch) }
        />
        <button
          className={mergeButtonCSS}
          data-tooltip={mergeTooltip}
          onClick={() => this._toggleModal('mergeModal', branch.branchName) }
        />
        {mergeModalVisible && this._renderModal(branch, 'merge')}
        <button
          className={deleteButtonCSS}
          data-tooltip={deleteTooltip}
          onClick={() => this._toggleModal('deleteModal', branch.branchName) }
        />
        {deleteModalVisible && this._renderModal(branch, 'delete')}
        <button
          className={syncButtonCSS}
          data-tooltip={syncTooltip}
          onClick={() => this._syncBranch(branch) }

        />
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
            'Branches__branch--current--selected': state.mergeModalVisible,
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
                  (state.mergeModalVisible || state.deleteModalVisible || state.action) &&
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
                  <button
                    className="Branches__btn Branches__btn--create"
                    onClick={() => this.props.toggleModal('createBranchVisible') }
                  />
                </div>

              <div className={currentBranchContainerCSS}>
                <div className="Branches__base-section">
                  <div className="Branches__label">Current Branch:</div>
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
                filteredBranches.map((branch) => {
                  const branchStatusText = branch.isLocal ? branch.isRemote ? 'Local & Remote' : 'Local only' : 'Remote only',
                  branchContainerCSS = classNames({
                    Branches__branch: true,
                    'Branches__branch--selected': (branch.branchName === state.mergeModalVisible) || (branch.branchName === state.deleteModalVisible),
                  });
                  return (
                    <div
                      key={branch.branchName}
                      className={branchContainerCSS}
                      onClick={evt => this._selectBranchname(evt, branch.branchName)}
                    >
                      <div className="Branches__base-section">
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
                        state.selectedBranchname === branch.branchName &&
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

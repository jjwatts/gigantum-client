// vendor
import React, { Component } from 'react';
import { boundMethod } from 'autobind-decorator';
import classNames from 'classnames';
// componenets
import Loader from 'Components/common/Loader';
import CreateBranch from 'Components/shared/modals/CreateBranch';
import Branches from 'Components/shared/sidePanel/Branches';
// utils
import BranchMutations from '../../utils/BranchMutations';
// assets
import './BranchMenu.scss';


/**
  @param {Array} branches
  filters array branhces and return the active branch node
  @return {Object} activeBranch
*/
const extraxtActiveBranch = (branches) => {
   const activeBranch = branches.filter(branch => branch.isActive)[0];
   const filteredBranches = branches.filter(branch => !branch.isActive);
   return ({ activeBranch, filteredBranches });
};

class BranchMenu extends Component {
  state = {
    switchMenuVisible: false,
    createBranchVisible: false,
    branchMutations: new BranchMutations({
      parentId: this.props.labbook.id,
      name: this.props.labbook.name,
      owner: this.props.labbook.owner,
    }),
    switchingBranch: false,
    sidePanelVisible: false,
  };


  /**
    @param {Array} branches
    filters array branhces and return the active branch node
    @return {Object} activeBranch
  */
  @boundMethod
  _setModalState(key) {
     const { state } = this;
     const value = !state[key];
     this.setState({ [key]: value });
  }

  /**
    @param {Array} branches
    filters array branhces and return the active branch node
    @return {Object} activeBranch
  */
  @boundMethod
  _switchBranch(branch) {
    const { state } = this,
          self = this,
          data = {
            branchName: branch.branchName,
          };
      this.setState({
        switchingBranch: branch.branchName,
        switchMenuVisible: false,
      });
      state.branchMutations.switchBranch(data, (response, error) => {
        self.setState({ switchingBranch: false });
      });
  }

  /**
    @param {} -
    sets state to toggle the switch dropdown
    @return {}
  */
  @boundMethod
  _toggleBranchSwitch() {
     const { state } = this;
     this.setState({ switchMenuVisible: !state.switchMenuVisible });
  }
  /**
    @param {} -
    sets state to toggle the switch dropdown
    @return {}
  */
  @boundMethod
  _toggleSidePanel(sidePanelVisible) {
      this.setState({ sidePanelVisible });
  }

  render() {
    const { props, state } = this,
          { branches } = props.labbook,
          branchMenuCSS = classNames({
            BranchMenu: true,
            hidden: props.isSticky,
          }),
          switchDropdownCSS = classNames({
            'BranchMenu__dropdown-menu': true,
            hidden: !state.switchMenuVisible,
          }),
          drodownButtonCSS = classNames({
            'BranchMenu__dropdown-btn': true,
            'BranchMenu__dropdown-btn--open': state.switchMenuVisible,
          }),
          branchNameCSS = classNames({
            'BranchMenu__branch-name': !state.switchingBranch,
            hidden: state.switchingBranch,
          }),
          branchSwitchingNameCSS = classNames({
            'BranchMenu__branch-name': state.switchingBranch,
            hidden: !state.switchingBranch,
          }),
          { activeBranch, filteredBranches } = extraxtActiveBranch(branches);
    return (
      <div className={branchMenuCSS}>
          <div className="BranchMenu__dropdown">
                <div
                onClick={() => this._toggleBranchSwitch() }
                className={drodownButtonCSS}>
                  <div className={branchNameCSS}>
                    <div className="BranchMenu__dropdown-label">Branch:</div>
                    <div className="BranchMenu__dropdown-text">{activeBranch.branchName}</div>
                    <span>{`${activeBranch.commitsBehind} / ${activeBranch.commitsAhead}`}</span>
                  </div>

                  <div className={branchSwitchingNameCSS}>
                    <span className="BranchMenu__dropdown-label">Branch:</span>
                    <span className="BranchMenu__dropdown-text ">
                      {`switching to ${state.switchingBranch}...`}
                    </span>
                  </div>
                </div>
                <div className={switchDropdownCSS}>
                  <h5 className="BranchMenu__h5">Quick Switch</h5>
                  <ul className="BranchMenu__ul">
                    {
                      filteredBranches.map(branch => <li
                          onClick={ () => this._switchBranch(branch) }
                          key={branch.branchName}
                          className="BrancMenu__list-item">
                            {branch.branchName}

                            <span>{`${branch.commitsBehind} / ${branch.commitsAhead}`}</span>
                        </li>)
                    }
                  </ul>
                </div>
          </div>
          <div className="BranchMenu__buttons">
            <button
              onClick={() => this._toggleSidePanel(true)}
              className="BranchMenu__btn BranchMenu__btn--manage Btn--flat"
              type="Submit">
              Manage
            </button>
            <button
              className="BranchMenu__btn BranchMenu__btn--manage Btn--flat"
              type="Submit"
              onClick={() => this._setModalState('createBranchVisible') }>
              Create
            </button>
            <button
              className="BranchMenu__btn BranchMenu__btn--manage Btn--flat"
              type="Submit">
              Sync
            </button>
          </div>

          <CreateBranch
            modalVisible={state.createBranchVisible}
            description={props.labbook.description}
            toggleModal={this._setModalState}
          />

          <Branches
            sidePanelVisible={state.sidePanelVisible}
            toggleSidePanel={this._toggleSidePanel}
            branches={props.labbook.branches}
            activeBranch={activeBranch}
            toggleModal={this._setModalState}
            isSticky={props.isSticky}
            branchMutations={this.state.branchMutations}
          />
      </div>
    );
  }
}


export default BranchMenu;

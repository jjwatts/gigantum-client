// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// store
import store from 'JS/redux/store';
import {
  setSyncingState,
  setPublishingState,
  setExportingState,
  setModalVisible,
} from 'JS/redux/actions/labbook/labbook';
// config
import Config from 'JS/config';
// components
import Tooltip from 'Components/common/Tooltip';
import ErrorBoundary from 'Components/common/ErrorBoundary';
import TitleSection from './titleSection/TitleSection';
import ActionsSection from './actionsSection/ActionsSection';
import BranchMenu from './branches/BranchMenu';
import Container from './container/Container';
import Navigation from './navigation/Navigation';
// assets
import './Header.scss';

class Header extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hovered: false,
    };
    // bind functions here
    this._showLabbookModal = this._showLabbookModal.bind(this);
    this._hideLabbookModal = this._hideLabbookModal.bind(this);
    this._setHoverState = this._setHoverState.bind(this);
    this._checkOverflow = this._checkOverflow.bind(this);
  }

  /**
    @param {object} item
    returns nav jsx
  */
  _getSelectedIndex() {
    const pathArray = this.props.location.pathname.split('/');
    const defaultOrder = Config[`${this.props.sectionType}DefaultNavOrder`];
    const selectedPath = (pathArray.length > 4) ? pathArray[pathArray.length - 1] : defaultOrder[0];
    const selectedIndex = defaultOrder.indexOf(selectedPath);

    return selectedIndex;
  }

  /** *******************
   * child functions
   *
   ******************** */
  /**
   @param {boolean} isExporting
   updates container status state
   updates labbook state
  */
  _setExportingState = (isExporting) => {
    this.refs.ContainerStatus && this.refs.ContainerStatus.setState({ isExporting });

    if (this.props.isExporting !== isExporting) {
      setExportingState(isExporting);
    }
  }

  /**
    @param {}
    updates html element classlist and labbook state
  */
  _showLabbookModal = () => {
    if (!this.props.modalVisible) {
      setModalVisible(true);
    }
  }

  /**
    @param {}
    updates html element classlist and labbook state
  */
  _hideLabbookModal = () => {
    if (document.getElementById('labbookModal')) {
      document.getElementById('labbookModal').classList.add('hidden');
    }

    if (document.getElementById('modal__cover')) {
      document.getElementById('modal__cover').classList.add('hidden');
    }

    if (this.props.modalVisible) {
      setModalVisible(false);
    }
  }

  /**
    @param {boolean} isPublishing
    updates container status state
    updates labbook state
  */
 _setPublishingState = (isPublishing) => {
   this.refs.ContainerStatus && this.refs.ContainerStatus.setState({ isPublishing });

   if (this.props.isPublishing !== isPublishing) {
     setPublishingState(isPublishing);
   }
 }

 /** *
    @param {object} element
    checks if element is too large for card area
    @return {boolean}
  */
 _checkOverflow(element) {
   if (element) {
     const curOverflow = element.style.overflow;

     if (!curOverflow || curOverflow === 'visible') { element.style.overflow = 'hidden'; }

     const isOverflowing = element.clientWidth < element.scrollWidth || element.clientHeight < element.scrollHeight;

     element.style.overflow = curOverflow;

     return isOverflowing;
   }
 }

  /** ***
  *  @param {boolean} isSyncing
  *  updates container status state
  *  updates labbook state
  *  @return {}
  */
  _setSyncingState = (isSyncing) => {
    this.refs.ContainerStatus && this.refs.ContainerStatus.setState({ isSyncing });

    if (this.props.isSyncing !== isSyncing) {
      setSyncingState(isSyncing);
    }
  }

  /** ***
  *  @param {boolean, event} hovered, evt
  *  sets hover state
  *  @return {}
  */
  _setHoverState(hovered, evt) {
    if (this._checkOverflow(evt.target) || !hovered) {
      this.setState({ hovered });
    }
  }

  render() {
    const { props, state } = this;


    const {
      labbookName,
      labbook,
      branchesOpen,
      branchName,
      dataset,
    } = props;


    const {
      visibility,
      description,
      collaborators,
      defaultRemote,
      id,
    } = labbook || dataset;


    const section = labbook || dataset;


    const selectedIndex = this._getSelectedIndex();


    const isLabbookSection = props.sectionType === 'labbook';


    const headerCSS = classNames({
      Header: true,
      'Header--sticky': props.isSticky,
      'Header--demo': (window.location.hostname === Config.demoHostName) || props.diskLow,
      'Header--is-deprecated': props.isDeprecated,
      'Header--branchesOpen': props.branchesOpen,
    });


    const branchesErrorCSS = classNames({
      BranchesError: props.branchesOpen,
      hidden: !props.branchesOpen,
    });

    let branches = props.branches || [{
      branchName: 'master',
      isActive: true,
      commitsBehind: 0,
      commitsAhead: 0,
    }];

    branches = props.showMigrationButton ? branches.filter(({ branchName }) => branchName !== 'master') : branches;

    return (

      <div className="Header__wrapper">

        <div className={headerCSS}>
          <div className="Header__flex">
            <div className="Header__columnContainer Header__columnContainer--flex-1">

              <TitleSection
                self={this}
                {...props}
              />
              <ErrorBoundary
                type={branchesErrorCSS}
                key="branches"
              >
                <BranchMenu
                  {...props}
                  defaultRemote={section.defaultRemote}
                  branchesOpen={props.branchesOpen}
                  section={section}
                  branches={branches}
                  sectionId={section.id}
                  activeBranch={section.activeBranchName || 'master'}
                  toggleBranchesView={this.props.toggleBranchesView}
                  mergeFilter={props.mergeFilter}
                  isSticky={props.isSticky}
                  visibility={props.visibility}
                  sectionType={props.sectionType}
                  auth={props.auth}
                  setSyncingState={this._setSyncingState}
                  setPublishingState={this._setPublishingState}
                  setExportingState={this._setExportingState}
                  isLocked={props.isLocked}
                  setBranchUptodate={props.setBranchUptodate}
                />
              </ErrorBoundary>

            </div>

            <div className="Header__columnContainer Header__columnContainer--fixed-width">
              <ActionsSection
                visibility={visibility}
                description={description}
                collaborators={collaborators}
                defaultRemote={defaultRemote}
                labbookId={id}
                remoteUrl={defaultRemote}
                setSyncingState={this._setSyncingState}
                setExportingState={this._setExportingState}
                branchName={branchName}
                isSticky={props.isSticky}
                {...props}
              />
              { isLabbookSection && <Container {...props} /> }
            </div>
          </div>

          <Navigation {...props} />

        </div>
      </div>
    );
  }
}

export default Header;

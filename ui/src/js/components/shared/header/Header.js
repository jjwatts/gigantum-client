// vendor
import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import classNames from 'classnames';
// store
import store from 'JS/redux/store';
import {
  setSyncingState,
  setPublishingState,
  setExportingState,
  setModalVisible,
  setUpdateDetailView,
} from 'JS/redux/reducers/labbook/labbook';
// config
import Config from 'JS/config';
// components
import ToolTip from 'Components/common/ToolTip';
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
    this._setSelectedComponent = this._setSelectedComponent.bind(this);
    this._showLabbookModal = this._showLabbookModal.bind(this);
    this._hideLabbookModal = this._hideLabbookModal.bind(this);
    this._setHoverState = this._setHoverState.bind(this);
    this._checkOverflow = this._checkOverflow.bind(this);
  }

  /**
    @param {string} componentName - input string componenetName
    updates state of selectedComponent
    updates history prop
  */
  _setSelectedComponent = (componentName) => {
    if (componentName !== this.props.selectedComponent) {
      if (store.getState().detailView.selectedComponent === true) {
        setUpdateDetailView(false);
      }
    }
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
    const { props, state } = this,
          {
            labbookName,
            labbook,
            branchesOpen,
            branchName,
            dataset,
          } = props,
          {
            visibility,
            description,
            collaborators,
            defaultRemote,
            id,
          } = labbook || dataset,
          selectedIndex = this._getSelectedIndex(),
          isLabbookSection = props.sectionType === 'labbook',
          headerCSS = classNames({
            Header: true,
            'Header--sticky': props.isSticky,
            'Header--branchesOpen': props.branchesOpen,
          }),
          branchesErrorCSS = classNames({
            BranchesError: props.branchesOpen,
            hidden: !props.branchesOpen,
          }),
          hiddenStickCSS = classNames({
            hidden: props.isStick,
          });

    return (

      <div className="Header__wrapper">

        <div className={headerCSS}>
            <div className="Header__flex">
              <div className="Header__columnContainer Header__columnContainer--flex-1">

                <TitleSection
                  self={this}
                  {...props}
                />
                { isLabbookSection
                 && <ErrorBoundary
                  type={branchesErrorCSS}
                  key="branches">
                  <BranchMenu
                    defaultRemote={labbook.defaultRemote}
                    branchesOpen={this.props.branchesOpen}
                    labbook={labbook}
                    labbookId={labbook.id}
                    activeBranch={labbook.activeBranchName}
                    toggleBranchesView={this.props.toggleBranchesView}
                    mergeFilter={this.props.mergeFilter}
                    setBuildingState={this.props.setBuildingState}
                    isSticky={props.isSticky}
                  />
                </ErrorBoundary>
                }

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
                  setPublishingState={this._setPublishingState}
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

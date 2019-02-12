// vendor
import React, { Component } from 'react';
import { Link } from 'react-router-dom';
// environment
import classNames from 'classnames';
// components
import Branches from './branches/Branches';
import Description from './description/Description';
import BranchMenu from './branchMenu/BranchMenu';
import ContainerStatus from './containerStatus/ContainerStatus';
import ToolTip from 'Components/common/ToolTip';
import ErrorBoundary from 'Components/common/ErrorBoundary';
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
// assets
import './Header.scss';

class LabbookHeader extends Component {
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
    const {
      labbookName, labbook, branchesOpen, branchName, dataset,
    } = this.props;
    const { visibility } = labbook || dataset;
    const selectedIndex = this._getSelectedIndex();
    const {
      description,
      collaborators,
      defaultRemote,
      id,
    } = labbook || dataset;

    const labbookHeaderCSS = classNames({
      LabbookHeader: true,
      'LabbookHeader--sticky': this.props.isSticky,
      'LabbookHeader--branchesOpen': this.props.branchesOpen,
    });

    const branchesErrorCSS = classNames({
      BranchesError: this.props.branchesOpen,
      hidden: !this.props.branchesOpen,
    });

    return (

      <div className="LabbookHeader__wrapper">

        <div className={labbookHeaderCSS}>

          <div className="LabbookHeader__bar">

            <div className="LabbookHeader__columnContainer LabbookHeader__columnContainer--flex-1">

              <LabbookTitle
                self={this}
                visibility={visibility}
                labbook={labbook}
                branchName={branchName}
                labbookName={labbookName}
                type={this.props.sectionType}
                owner={this.props.owner}
                datasetName={this.props.datasetName}
              />

              <BranchName
                self={this}
                branchesOpen={branchesOpen}
                branchName={branchName}
                description={this.props.description}
                hovered={this.state.hovered}
                setHoverState={this._setHoverState}
                sectionType={this.props.sectionType}
              />
            </div>

            <div className="LabbookHeader__columnContainer">
              <BranchMenu
                sectionType={this.props.sectionType}
                visibility={visibility}
                description={description}
                history={this.props.history}
                collaborators={collaborators}
                defaultRemote={defaultRemote}
                labbookId={id}
                remoteUrl={defaultRemote}
                setSyncingState={this._setSyncingState}
                setPublishingState={this._setPublishingState}
                setExportingState={this._setExportingState}
                isExporting={this.props.isExporting}
                toggleBranchesView={this.props.toggleBranchesView}
                isMainWorkspace={branchName === 'workspace' || branchName === `gm.workspace-${localStorage.getItem('username')}`}
                auth={this.props.auth}
              />
              {
                this.props.sectionType === 'labbook' &&
                <ErrorBoundary type="containerStatusError" key="containerStatus">

                  <ContainerStatus
                    ref="ContainerStatus"
                    auth={this.props.auth}
                    base={labbook.environment.base}
                    containerStatus={labbook.environment.containerStatus}
                    imageStatus={labbook.environment.imageStatus}
                    labbookId={labbook.id}
                    setBuildingState={this.props.setBuildingState}
                    isBuilding={this.props.isBuilding}
                    isSyncing={this.props.isSyncing}
                    isPublishing={this.props.isPublishing}
                    creationDateUtc={labbook.creationDateUtc}
                  />

                </ErrorBoundary>
              }


            </div>

          </div>
          {
            this.props.sectionType === 'labbook' &&
            <ErrorBoundary
              type={branchesErrorCSS}
              key="branches"
            >

              <Branches
                defaultRemote={labbook.defaultRemote}
                branchesOpen={this.props.branchesOpen}
                labbook={labbook}
                labbookId={labbook.id}
                activeBranch={labbook.activeBranchName}
                toggleBranchesView={this.props.toggleBranchesView}
                mergeFilter={this.props.mergeFilter}
                setBuildingState={this.props.setBuildingState}
              />

            </ErrorBoundary>
          }
          {
            !branchesOpen &&
            <div className="LabbookHeader__navContainer flex-0-0-auto">

            <ul className="LabbookHeader__nav flex flex--row">
              {
                Config[`${this.props.sectionType}_navigation_items`].map((item, index) => (
                  <NavItem
                    self={this}
                    item={item}
                    index={index}
                    key={item.id}
                    type={this.props.sectionType}
                  />))
              }

              <hr className={`LabbookHeader__navSlider LabbookHeader__navSlider--${selectedIndex}`} />
            </ul>

          </div>
          }

        </div>
      </div>
    );
  }
}

const LabbookTitle = ({
  self, visibility, labbook, branchName, labbookName, type, datasetName, owner,
}) => {
  const labbookLockCSS = classNames({
    [`LabbookHeader__${visibility}`]: true,
    [`LabbookHeader__${visibility}--sticky`]: self.props.isSticky,
  });

  let title;

  if (type === 'labbook') {
    title = `${labbook.owner}/${labbookName}${self.props.isSticky ? '/ ' : ''}`;
  } else {
    title = `${owner}/${datasetName}${self.props.isSticky ? '/ ' : ''}`;
  }

  return (
    <div className="LabbookHeader__section--title">

      <div>
        {title}
      </div>

      {
        self.props.isSticky &&
        <div className="LabbookHeader__branchName">{branchName}</div>
      }

      { ((visibility === 'private') ||
          (visibility === 'public')) &&

          <div className={labbookLockCSS} />
      }
    </div>
  );
};

const BranchName = ({
  self,
  branchesOpen,
  branchName,
  description,
  hovered,
  setHoverState,
  sectionType,
}) => {
  const branchNameCSS = classNames({
    LabbookHeader__branchTitle: true,
    'LabbookHeader__branchTitle--open': branchesOpen,
    'LabbookHeader__branchTitle--closed': !branchesOpen,
  });

  return (
    <div className={branchNameCSS}>
      <div className="LabbookHeader__name-container">
        <div
          onMouseEnter={evt => setHoverState(true, evt)}
          onMouseLeave={evt => setHoverState(false, evt)}
          className="LabbookHeader__name"
          onClick={() => self.props.toggleBranchesView(!branchesOpen, false)}
        >
          {branchName}
        </div>
        <ToolTip section="branchView" />
      </div>
      <Description
        hovered={hovered}
        description={description}
        sectionType={sectionType}
      />
    </div>
  );
};
/**
    @param {object, int}
    retruns jsx for nav items and sets selected
    @return {jsx}
*/
const NavItem = ({
  self,
  item,
  index, type,
}) => {
  const pathArray = self.props.location.pathname.split('/');
  const selectedPath = (pathArray.length > 4) ? pathArray[pathArray.length - 1] : 'overview'; // sets avtive nav item to overview if there is no menu item in the url

  const navItemCSS = classNames({
    'LabbookHeader__navItem--selected': selectedPath === item.id,
    [`LabbookHeader__navItem LabbookHeader__navItem--${item.id}`]: !selectedPath !== item.id,
    [`LabbookHeader__navItem--${index}`]: true,
  });

  const section = type === 'labbook' ? 'projects' : 'datasets';
  const name = type === 'labbook' ? self.props.match.params.labbookName : self.props.match.params.datasetName;

  return (
    <li
      id={item.id}
      className={navItemCSS}
      onClick={() => self._setSelectedComponent(item.id)}
      title={Config.navTitles[item.id]}
    >

      <Link
        onClick={self._scrollToTop}
        to={`../../../${section}/${self.props.owner}/${name}/${item.id}`}
        replace
      >

        {item.name}

      </Link>

    </li>);
};

export default LabbookHeader;

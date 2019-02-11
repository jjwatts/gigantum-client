// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import { setContainerMenuWarningMessage } from 'JS/redux/reducers/labbook/environment/environment';
import store from 'JS/redux/store';
// config
import config from 'JS/config';
// Components
import Loader from 'Components/common/Loader';
import CreateBranch from 'Components/shared/header/branches/CreateBranch';
import ErrorBoundary from 'Components/common/ErrorBoundary';
import PaginationLoader from './loaders/PaginationLoader';
import ClusterCardWrapper from './wrappers/ClusterCardWrapper';
import CardWrapper from './wrappers/CardWrapper';
import UserNoteWrapper from './wrappers/UserNoteWrapper';
// utils
import NewActivity from './NewActivity';
// assets
import './Activity.scss';

// local variables
let pagination = false;

let counter = 5;
let isMounted = false;

export const getGlobals = () => ({ counter, pagination });

class Activity extends Component {
  constructor(props) {
    super(props);
    const section = props[props.sectionType];
  	this.state = {
      modalVisible: false,
      isPaginating: false,
      selectedNode: null,
      createBranchVisible: false,
      refetchEnabled: false,
      newActivityAvailable: false,
      newActivityPolling: false,
      editorFullscreen: false,
      hoveredRollback: null,
      expandedClusterObject: new Map(),
      newActivityForcePaused: false,
      refetchForcePaused: false,
      activityRecords: section.activityRecords ? [] : this._transformActivity(section.activityRecords),
      stickyDate: false,
      compressedElements: new Set(),
    };
    this.dates = [];

    // bind functions here
    this._loadMore = this._loadMore.bind(this);
    this._toggleActivity = this._toggleActivity.bind(this);
    this._hideAddActivity = this._hideAddActivity.bind(this);
    this._handleScroll = this._handleScroll.bind(this);
    this._refetch = this._refetch.bind(this);
    this._startRefetch = this._startRefetch.bind(this);
    this._scrollTo = this._scrollTo.bind(this);
    this._stopRefetch = this._stopRefetch.bind(this);
    this._toggleCreateModal = this._toggleCreateModal.bind(this);
    this._toggleRollbackMenu = this._toggleRollbackMenu.bind(this);
    this._getNewActivities = this._getNewActivities.bind(this);
    this._changeFullscreenState = this._changeFullscreenState.bind(this);
    this._handleVisibilityChange = this._handleVisibilityChange.bind(this);
    this._transformActivity = this._transformActivity.bind(this);
    this._countUnexpandedRecords = this._countUnexpandedRecords.bind(this);
    this._addCluster = this._addCluster.bind(this);
    this._expandCluster = this._expandCluster.bind(this);
    this._compressExpanded = this._compressExpanded.bind(this);
    this._setStickyDate = this._setStickyDate.bind(this);
  }

  UNSAFE_componentWillReceiveProps(nextProps) {
    const section = nextProps[nextProps.sectionType],
          activityRecords = nextProps[nextProps.sectionType].activityRecords,
          {
            state,
            props,
          } = this,
          currentActivityRecords = JSON.stringify(this._transformActivity(activityRecords)),
          previousActivityRecords = JSON.stringify(state.activityRecords);

    if (activityRecords && (currentActivityRecords !== previousActivityRecords)) {
      const previousSection = props[props.sectionType];
      const prevCommit = previousSection && previousSection.activityRecords.edges && section.activityRecords.edges[0].node && false;
      const newcommit = section && section.activityRecords.edges && section.activityRecords.edges[0] && section.activityRecords.edges[0].node;

      if (prevCommit && (prevCommit !== newcommit)) {
        this.setState({ expandedClusterObject: new Map() }, () => this.setState({ activityRecords: this._transformActivity(activityRecords) }));
      } else {
        this.setState({ activityRecords: this._transformActivity(activityRecords) });
      }
    }

    if (activityRecords.pageInfo.hasNextPage && (activityRecords.edges.length < 3)) {
      this._loadMore();
    }
  }

  /**
  *  @param {}
  *   add scroll listener
  *   add interval to poll for new activityRecords
  */
  componentDidMount() {
    isMounted = true;
    const { props } = this,
          section = props[props.sectionType],
          activityRecords = section.activityRecords;

    window.addEventListener('scroll', this._handleScroll);
    window.addEventListener('visibilitychange', this._handleVisibilityChange);

    this.setState({ activityRecords: this._transformActivity(activityRecords) });

    if (activityRecords.pageInfo.hasNextPage && (this._countUnexpandedRecords() < 7)) {
      this._loadMore();
    }

    if (activityRecords.edges && activityRecords.edges.length) {
      this.setState({ refetchEnabled: true });
      this._refetch();
    }


  }

  componentWillUnmount() {
    counter = 5;
    pagination = false;
    clearInterval(this.interval);
    clearTimeout(this.refetchTimeout);
    clearTimeout(this.newActivityTimeout);
    isMounted = false;

    window.removeEventListener('visibilitychange', this._handleVisibilityChange);
    window.removeEventListener('scroll', this._handleScroll);
  }

  /**
   * @param {}
   * scroll to top of page
   * deletes activity feed in the relay store
   * resets counter
   * calls restart function
   * removes scroll listener
   * @return {}
   */
  _scrollTo(evt) {
    if (document.documentElement.scrollTop === 0) {
      const { props } = this,
            { relay } = props,
            store = relay.environment.getStore(),
            section = props[props.sectionType];

      section.activityRecords.edges.forEach((edge) => {
        store._recordSource.delete(edge.node.id);
      });

      counter = 5;

      this._startRefetch();

      window.removeEventListener('scroll', this._scrollTo);
    }
  }

  /**
   * @param {}
   * handles refiring new activity query if visibility changes back to visible
   * @return {}
   */
  _handleVisibilityChange() {
    const { state } = this;
    if (state.newActivityForcePaused) {
      this._stopRefetch();
      this.setState({ newActivityForcePaused: false });
    } else if (state.refetchForcePaused) {
      this._refetch();
      this.setState({ refetchForcePaused: false });
    }
  }

  /**
   * @param {}
   * sets scroll listener
   * kicks off scroll to top
   * @return {}
   */
  _getNewActivities() {
    window.addEventListener('scroll', this._scrollTo);

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  }

  /**
   * @param {}
   * restarts refetch
   * @return {}
   */
  _startRefetch() {
    const { state } = this;
    if (state.newActivityPolling) {
      this.setState({
        refetchEnabled: true,
        newActivityPolling: false,
        newActivityAvailable: false,
      });

      this._refetch();
    }
  }

  /**
   * @param {}
   * stops refetch from firing
   * @return {}
   */
  _stopRefetch() {
    const self = this,
          { state } = this;

    if (!state.newActivityPolling) {
      this.setState({
        refetchEnabled: false,
        newActivityPolling: true,
        newActivityAvailable: false,
      });

      const { labbookName, owner } = store.getState().routes;

      const getNewActivity = () => {
        NewActivity.getNewActivity(labbookName, owner).then((response) => {
          const firstRecordCommitId = self.props.labbook.activityRecords.edges[0].node.commit;
          const newRecordCommitId = response.data.labbook.activityRecords.edges[0].node.commit;

          if (firstRecordCommitId === newRecordCommitId) {
            self.newActivityTimeout = setTimeout(() => {
              if (isMounted && (document.visibilityState === 'visible') && !state.refetchEnabled) {
                getNewActivity();
              } else if (isMounted && (document.visibilityState !== 'visible') && !state.refetchEnabled) {
                this.setState({ newActivityForcePaused: true, newActivityPolling: false });
              }
            }, 3000);
          } else {
            this.setState({ newActivityAvailable: true });
          }
        }).catch(error => console.log(error));
      };

      getNewActivity();
    }
  }

  /**
  * @param {}
  * refetches component looking for new edges to insert at the top of the activity feed
  * @return {}
  */
  _refetch() {
    const self = this,
          { props } = this,
          { relay } = props,
          section = props[props.sectionType],
          activityRecords = section.activityRecords;

    const cursor = activityRecords.edges.node ? activityRecords.edges[activityRecords.edges.length - 1].node.cursor : null;
    relay.refetchConnection(
      counter,
      (response, error) => {
        self.refetchTimeout = setTimeout(() => {
          if (self.state.refetchEnabled && isMounted && (document.visibilityState === 'visible')) {
            self._refetch();
          } else if (self.state.refetchEnabled && isMounted && (document.visibilityState !== 'visible')) {
            self.setState({ refetchForcePaused: true });
          }
        }, 5000);
      },
      {
        cursor,
      },
    );
  }

  /**
  *  @param {}
  *  pagination container loads more items
  */
  _loadMore() {
    const self = this,
          { props } = this,
          section = props[props.sectionType],
          activityRecords = section.activityRecords;

    pagination = true;

    this.setState({
      isPaginating: true,
    });

    props.relay.loadMore(
      5, // Fetch the next 5 feed items
      (error) => {
        if (error) {
          console.error(error);
        }

        if ((activityRecords.pageInfo.hasNextPage) && (this._countUnexpandedRecords() < 7) && (this._countUnexpandedRecords() > 2)) {
          self._loadMore();
        } else {
          this.setState({
            isPaginating: false,
          });
        }
      }, {
        name: 'labbook',
      },
    );
    if (activityRecords.pageInfo.hasNextPage) {
      counter += 5;
    }
  }

  /**
  *  @param {}
  *  counts visible non clustered activity records
  */
  _countUnexpandedRecords() {
    const { props } = this,
          section = props[props.sectionType];
    let records = section.activityRecords.edges,
        hiddenCount = 0,
        recordCount = 0;

    const visibleRecords = records.filter((record) => {
      if (record) {
        if (!record.node.show) {
          hiddenCount++;
        } else if (hiddenCount > 2) {
          hiddenCount = 0;
          recordCount++;
        }
      }

      return record && record.node && record.node.show;
    });

    if (hiddenCount > 0) {
      recordCount++;
    }

    return visibleRecords.length + recordCount;
  }

  /**
    *  @param {}
    *   determines value of stickyDate by checking vertical offset and assigning it to the state
    *
  */
  _setStickyDate() {
    let isDemo = window.location.hostname === config.demoHostName,
      upperBound = isDemo ? 170 : 120,
      lowerBound = isDemo ? 130 : 80,
      stickyDate = null,
      { state } = this;

    this.offsetDistance = window.pageYOffset;

    this.dates.forEach((date) => {
      if (date && date.e) {
        const bounds = date.e.getBoundingClientRect();

        if (bounds.top < upperBound) {
          stickyDate = date.time;
          date.e.classList.add('not-visible');
          date.e.nextSibling && date.e.nextSibling.classList.add('next-element');
        } else {
          date.e.classList.remove('not-visible');
          date.e.nextSibling && date.e.nextSibling.classList.remove('next-element');
        }
      }
    });

    if (stickyDate !== state.stickyDate) {
      this.setState({ stickyDate });
    }
  }

  /**
  *  @param {evt}
  *   handles scolls and passes off loading to pagination container
  *
  */

  _handleScroll(evt) {
    this._setStickyDate();
    const { props, state } = this,
       { isPaginating } = state,
       section = props[props.sectionType],
       activityRecords = section.activityRecords,
       root = document.getElementById('root'),
       distanceY = window.innerHeight + document.documentElement.scrollTop + 1000,
       expandOn = root.scrollHeight;

    if ((distanceY > expandOn) && !isPaginating && activityRecords.pageInfo.hasNextPage) {
      this._loadMore(evt);
    }

    if ((distanceY > 3000)) {
      this._stopRefetch();
    } else {
      this._startRefetch();
    }
  }

  /**
  *   @param {array}
  *   loops through activityRecords array and sorts into days
  *   @return {Object}
  */
  _transformActivity(activityRecords) {
    const { state } = this;
    let activityTime = {},
        count = 0,
        previousTimeHash = null,
        clusterIndex = 0;
    activityRecords.edges.forEach((edge, index) => {
      if (edge && edge.node) {
         const date = (edge.node && edge.node.timestamp) ? new Date(edge.node.timestamp) : new Date(),
              year = date.getFullYear(),
              month = date.getMonth(),
              day = date.getDate(),
              timeHash = `${year}_${month}_${day}`;

        count = (edge.node.show || (previousTimeHash && (timeHash !== previousTimeHash))) ? 0 : count + 1;
        if (count === 0) {
          clusterIndex = 0;
        }
        previousTimeHash = timeHash;

        const isExpandedHead = state && state.expandedClusterObject.has(index) && !state.expandedClusterObject.has(index - 1);
        const isExpandedEnd = state && state.expandedClusterObject.has(index) && !state.expandedClusterObject.has(index + 1);
        const isExpandedNode = state && state.expandedClusterObject.has(index);
        const attachedCluster = state && state.expandedClusterObject.has(index) && state.expandedClusterObject.get(index);
        const newActivityObject = {
          edge,
          date,
          collapsed: ((count > 2) && ((this.state && !state.expandedClusterObject.has(index)) || (!state))),
          flatIndex: index,
          isExpandedHead,
          isExpandedEnd,
          isExpandedNode,
          attachedCluster,
        };

        if (count > 2 && ((this.state && !state.expandedClusterObject.has(index)) || (!state))) {
          if (count === 3) {
            let activityOne = activityTime[timeHash][activityTime[timeHash].length - 1];
            activityTime[timeHash][activityTime[timeHash].length - 1].collapsed = true;

           let activityTwo = activityTime[timeHash][activityTime[timeHash].length - 2];
            activityTime[timeHash][activityTime[timeHash].length - 2].collapsed = true;

            let clusterObject = {
              cluster: [activityOne, activityTwo, newActivityObject],
              attachedCluster,
              expanded: false,
              id: activityOne.edge.node.id,
            };

            activityTime[timeHash].splice(activityTime[timeHash].length - 1, 1);
            activityTime[timeHash].splice(activityTime[timeHash].length - 2, 1);

            activityTime[timeHash] ? activityTime[timeHash].push(clusterObject) : activityTime[timeHash] = [clusterObject];

            clusterIndex = activityTime[timeHash].length - 1;
          } else {
            activityTime[timeHash][clusterIndex].cluster.push(newActivityObject);
          }
        } else {
          clusterIndex = 0;
          activityTime[timeHash] ? activityTime[timeHash].push(newActivityObject) : activityTime[timeHash] = [newActivityObject];
        }
      }
    });
    return activityTime;
  }

  /**
  *   @param {}
  *   toggles activity visibility
  *   @return {}
  */
  _toggleActivity() {
    const { modalVisible } = this.state;
    this.setState({
      modalVisible: !modalVisible,
    });
  }

  /**
  *   @param {}
  *   hides add activity
  *   @return {}
  */
  _hideAddActivity() {
    this.setState({
      modalVisible: false,
    });
  }

  /**
  *   @param {}
  *   hides add activity
  *   @return {}
  */
  _toggleRollbackMenu(node) {
    const { status } = store.getState().containerStatus;
    const { props } = this;
    const canEditEnvironment = config.containerStatus.canEditEnvironment(status);
    if (canEditEnvironment) {
      const selectedNode = {
         activityNode: node,
         activeBranch: props.activeBranch,
         description: props.description,
      };
      this.setState({ selectedNode, createBranchVisible: true });
    } else {
      setContainerMenuWarningMessage('Stop Project before editing the environment. \n Be sure to save your changes.');
    }
  }

  /**
  *   @param {}
  *   toggle create branch modal visibility
  *   @return {}
  */
  _toggleCreateModal() {
    const { createBranchVisible } = this.state;
    this.setState({ createBranchVisible: !createBranchVisible });
  }

  /**
  *   @param {}
  *   opens create branch modal and also sets selectedNode to null
  *   @return {}
  */
  _createBranch() {
    const { status } = store.getState().containerStatus;
    const canEditEnvironment = config.containerStatus.canEditEnvironment(status);
    if (canEditEnvironment) {
      this.setState({ createBranchVisible: true, selectedNode: null });
    } else {
      setContainerMenuWarningMessage('Stop Project before creating branches. \n Be sure to save your changes.');
    }
  }

  /**
  *   @param {boolean} isFullscreen
  *   Changes editorFullscreen in state to true if isFullscreen is true, else it swaps existing state
  *   @return {}
  */

  _changeFullscreenState(isFullscreen) {
    if (isFullscreen) {
      this.setState({ editorFullscreen: isFullscreen });
    } else {
      const { editorFullscreen } = this.state;
      this.setState({ editorFullscreen: !editorFullscreen });
    }
  }

  /**
  *   @param {array} clusterElements
  *   modifies expandedClusterObject from state
  *   @return {}
  */
  _expandCluster(indexItem) {
    const { props, state } = this;
    let activityRecords = state.activityRecords;
    activityRecords[indexItem.timestamp][indexItem.j].cluster = true;

    this.setState({ activityRecords });
  }

  /**
    *   @param {array} clusterElements
    *   modifies expandedClusterObject from state
    *   @return {}
  */
  _addCluster(clusterElements) {
    const { props, state } = this,
          section = props[props.sectionType],
          newExpandedClusterObject = new Map(state.expandedClusterObject);

    if (newExpandedClusterObject !== {}) {
      clusterElements.forEach((val) => {
        newExpandedClusterObject.delete(val);
      });
    }

    this.setState({ expandedClusterObject: newExpandedClusterObject }, () => {
      this.setState({ activityRecords: this._transformActivity(section.activityRecords) });
      this._compressExpanded(clusterElements, true);
    });
  }

  /**
  *   @param {array} clusterElements
  *   @param {boolean} remove
  *   adds or removes elements to cluster on expand and collapse
  *   @return {}
  */
  _compressExpanded(clusterElements, remove) {
    const { compressedElements } = this.state,
          newCompressedElements = new Set(compressedElements);

    if (remove) {
      clusterElements.forEach((val) => {
        newCompressedElements.delete(val);
      });
    } else {
      clusterElements.forEach((val) => {
        newCompressedElements.add(val);
      });
    }
    this.setState({ compressedElements: newCompressedElements });
  }

  /**
  *   @param {event} evt
  *   assigns open-menu class to parent element and ActivityExtended to previous element
  *   @return {}
  */
  _toggleSubmenu(evt) {
    const submenu = evt.target.parentElement,
          wrapper = submenu && submenu.parentElement;

    if (wrapper.previousSibling) {
      wrapper.previousSibling.className.indexOf('ActivityExtended') !== -1 ? wrapper.previousSibling.classList.remove('ActivityExtended') : wrapper.previousSibling.classList.add('ActivityExtended');
    } else {
      wrapper.parentElement.previousSibling.className.indexOf('ActivityExtended') !== -1 ? wrapper.parentElement.previousSibling.classList.remove('ActivityExtended') : wrapper.parentElement.previousSibling.classList.add('ActivityExtended');
    }
    submenu.className.indexOf('open-menu') !== -1 ? submenu.classList.remove('open-menu') : submenu.classList.add('open-menu');
  }

  render() {
    const { props, state } = this,
          section = props[props.sectionType],
          activityCSS = classNames({
            Activity: true,
            fullscreen: state.editorFullscreen,
          }),
          newActivityCSS = classNames({
            'Activity__new-record box-shadow': true,
            'is-demo': window.location.hostname === config.demoHostName,
          });
    if (section) {
      const recordDates = Object.keys(state.activityRecords),
            stickyDateCSS = classNames({
              'Activity__date-tab': true,
              fixed: state.stickyDate,
              'is-demo': window.location.hostname === config.demoHostName,
            });
      return (
        <div
          key={props.sectionType}
          className={activityCSS}>
          {
            (!state.refetchEnabled && state.newActivityAvailable)
            && <div className="Activity__new-record-wrapper column-1-span-10">
              <div
                onClick={() => this._getNewActivities()}
                className={newActivityCSS}>
                New Activity
              </div>
           </div>
          }
          {
            state.stickyDate
            && <div className={stickyDateCSS}>
              <div className="Activity__date-day">{state.stickyDate.split('_')[2]}</div>
              <div className="Activity__date-sub">

                <div className="Activity__date-month">
                  {
                    config.months[parseInt(state.stickyDate.split('_')[1], 10)]
                  }
                </div>

                <div className="Activity__date-year">{state.stickyDate.split('_')[0]}</div>
              </div>
            </div>

          }

          <div
            key={`${props.sectionType}_labbooks__container`}
            className="Activity__inner-container flex flex--row flex--wrap justify--flex-start">
            <div
              key={`${props.sectionType}_labbooks__labook-id-container`}
              className="Activity__sizer flex-1-0-auto">
              { state.createBranchVisible
                && <CreateBranch
                  ref="createBranch"
                  selected={state.selectedNode}
                  activeBranch={props.activeBranch}
                  modalVisible={state.createBranchVisible}
                  toggleModal={this._toggleCreateModal}
                  setBuildingState={props.setBuildingState}
                />
              }

              {
                recordDates.map((timestamp, i) => {
                  let clusterElements = [];
                  const ActivityDateCSS = classNames({
                    'Activity__date-tab': true,
                    note: (i === 0),
                  });
                  const ActivityContainerCSS = classNames({
                    'Activity__card-container': true,
                    'Activity__card-container--last': recordDates.length === i + 1,
                  });
                  return (
                    <div className={`Activity__date-section Activity__date-section--${i}`} key={timestamp}>
                      <div
                        ref={evt => this.dates[i] = { e: evt, time: timestamp }} className={ActivityDateCSS}>

                        <div className="Activity__date-day">
                          { timestamp.split('_')[2] }
                        </div>

                        <div className="Activity__date-sub">

                          <div className="Activity__date-month">
                            { config.months[parseInt(timestamp.split('_')[1], 10)] }
                          </div>

                          <div className="Activity__date-year">
                            {timestamp.split('_')[0]}
                          </div>
                        </div>
                      </div>
                      {
                        (i === 0)
                        && <UserNoteWrapper
                            modalVisible={state.modalVisible}
                            hideLabbookModal={this._hideAddActivity}
                            changeFullScreenState={this._changeFullscreenState}
                            labbookId={section.id}
                            editorFullscreen={state.editorFullscreen}
                            {...props}
                           />
                      }
                      <div
                        key={`${timestamp}__card`}
                        className={ActivityContainerCSS}>
                        {
                          state.activityRecords[timestamp].map((record, timestampIndex) => {
                            if (record.cluster) {
                              return (
                                <ClusterCardWrapper
                                    sectionType={props.sectionType}
                                    isMainWorkspace={props.isMainWorkspace}
                                    section={section}
                                    activityRecords={state.activityRecords}
                                    key={`ClusterCardWrapper_${timestamp}_${record.id}`}
                                    record={record}
                                    hoveredRollback={state.hoveredRollback}
                                    indexItem={{ i, timestampIndex, timestamp }}
                                    toggleSubmenu={this._toggleSubmenu}
                                    toggleRollbackMenu={this._toggleRollbackMenu}
                                 />);
                            }

                            return (<CardWrapper
                                section={section}
                                isMainWorkspace={props.isMainWorkspace}
                                activityRecords={state.activityRecords}
                                clusterElements={clusterElements}
                                sectionType={props.sectionType}
                                record={record}
                                compressExpanded={this._compressExpanded}
                                clusterObject={state.clusterObject}
                                compressedElements={state.compressedElements}
                                hoveredRollback={state.hoveredRollback}
                                indexItem={{ i, timestampIndex, timestamp }}
                                addCluster={this._addCluster}
                                key={`VisibileCardWrapper_${record.flatIndex}`}
                                toggleSubmenu={this._toggleSubmenu}
                                toggleRollbackMenu={this._toggleRollbackMenu}
                              />);
                          })
                        }
                      </div>
                    </div>);
                })
              }
              {
                Array(5).fill(1).map((value, index) => (
                  <PaginationLoader
                    key={`Actvity_paginationLoader${index}`}
                    index={index}
                    isLoadingMore={state.isPaginating}
                  />
                  ))
              }
            </div>
          </div>
        </div>
      );
    }
    return (
      <Loader />
    );
  }
}

export default Activity;

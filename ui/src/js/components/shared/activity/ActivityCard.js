// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// components
import ActivityDetails from 'Components/shared/activity/ActivityDetails';
// assets
import './ActivityCard.scss';

export default class ActivityCard extends Component {
  constructor(props) {
    super(props);

    const showDetails = props.edge.node.show && props.edge.node.detailObjects.filter(details => details.show).length !== 0;

    this.state = {
      showExtraInfo: showDetails,
      show: true,
      isOver: false,
    };
  }

  /**
    @param {string} timestamp
    if input is undefined. current time of day is used
    inputs a time stamp and return the time of day HH:MM am/pm
    @return {string}
  */
  _getTimeOfDay(timestamp) {
    const time = (timestamp !== undefined) ? new Date(timestamp) : new Date();
    const hour = (time.getHours() % 12 === 0) ? 12 : time.getHours() % 12;
    const minutes = (time.getMinutes() > 9) ? time.getMinutes() : `0${time.getMinutes()}`;
    const ampm = time.getHours() >= 12 ? 'pm' : 'am';

    return `${hour}:${minutes}${ampm}`;
  }

  /**
    @param {}
    * determines the appropriate margins for cards when compressing
    @return {object}
  */
  _processCardStyle() {
    const activityCardStyle = {};


    const { props, state } = this;

    if (props.isCompressed) {
      if (!props.isExpandedHead && !props.isExpandedEnd) {
        activityCardStyle.marginTop = '-7.5px';
        activityCardStyle.marginBottom = '-7.5px';
      } else if (props.isExpandedHead) {
        const distance = props.attachedCluster.length - 1;
        const calculatedMargin = distance * 7.5;

        activityCardStyle.marginTop = `${calculatedMargin}px`;
        activityCardStyle.marginBottom = '-7.5px';
      } else if (props.isExpandedEnd) {
        const distance = props.attachedCluster.length - 1;
        const calculatedMargin = distance * 7.5;

        activityCardStyle.marginTop = '-7.5px';
        activityCardStyle.marginBottom = `${calculatedMargin}px`;
      }
    }

    return activityCardStyle;
  }


  _expandCollapseSideBar(isOver) {
    const { props } = this;
    props.compressExpanded(props.attachedCluster, !isOver);

    this.setState({ isOver });
  }


  render() {
    const { props, state } = this;
    const node = props.edge.node;


    const type = node.type && node.type.toLowerCase();

    const activityCardCSS = classNames({
      'ActivityCard card': state.showExtraInfo,
      'ActivityCard ActivityCard--collapsed card': !state.showExtraInfo,
      'ActivityCard--faded': props.hoveredRollback > props.position,
      ActivityCard__expanded: props.isExpandedNode,
      ActivityCard__compressed: props.isCompressed && !props.isExpandedEnd,
    });


    const titleCSS = classNames({
      'ActivityCard__title flex flex--row justify--space-between': true,
      open: state.showExtraInfo || (type === 'note' && state.show),
      closed: !state.showExtraInfo || (type === 'note' && !state.show),
    });


    const expandedCSS = classNames({
      ActivityCard__node: props.isExpandedNode && !props.isExpandedHead && !props.isExpandedEnd,
      'ActivityCard__start-node': props.isExpandedHead,
      'ActivityCard__end-node': props.isExpandedEnd,
    });

    const expandedHeight = props.attachedCluster ? 110 * (props.attachedCluster.length - 1) : 0;

    const expandedBarHeight = state.isOver ? expandedHeight - ((props.attachedCluster.length - 1) * 15) : expandedHeight;

    const margin = state.isOver ? ((props.attachedCluster.length - 1) * 7.5) : 0;

    const expandedContainerStyle = props.attachedCluster && {
      height: `${expandedHeight}px`,
    };

    const expandedStyle = props.attachedCluster && {
      height: `${expandedBarHeight}px`,
      margin: `${margin}px 0 0 0`,
    };

    if (props.isFirstCard && props.attachedCluster) {
      expandedStyle.top = '2px';
    }

    const activityCardStyle = this._processCardStyle();
    return (
      <div className="ActivityCard__container column-1-span-9">

        <div className={activityCardCSS} ref="card" style={activityCardStyle}>

          <div
            className={`ActivityCard__badge ActivityCard__badge--${type}`}
            title={type}
          />

          <div className="ActivityCard__content">

            <div
              className={titleCSS}
              onClick={() => this.setState({ show: !state.show, showExtraInfo: !state.showExtraInfo })}
            >

              <div className="ActivityCard__stack">

                <p className="ActivityCard__time">
                  {this._getTimeOfDay(props.edge.node.timestamp)}
                </p>

                <div className="ActivityCard__user" />
              </div>

              <h6 className="ActivityCard__commit-message">
                <b>{`${props.edge.node.username} - `}</b>
                { props.edge.node.message }
              </h6>

            </div>

            {
              (state.showExtraInfo && (type !== 'note' || state.show))
                && (
                <ActivityDetails
                  sectionType={props.sectionType}
                  edge={props.edge}
                  show={state.showExtraInfo}
                  key={`${node.id}_activity-details`}
                  node={node}
                />
                )
            }
          </div>
        </div>
      </div>
    );
  }
}

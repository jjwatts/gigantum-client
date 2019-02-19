// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import ErrorBoundary from 'Components/common/ErrorBoundary';
import ToolTip from 'Components/common/ToolTip';
import ActivityCard from '../ActivityCard';
import CardWrapper from './CardWrapper';
// Styles
import './ClusterCardWrapper.scss';

export default class ClusterCardWrapper extends Component {
  constructor(props) {
  	super(props);
  	this.state = {
      expanded: props.record.cluster.expanded,
      shrink: false,
      mousePoint: null,
    };
  }

  /**
    @param {Object} evt
    toggles submenu
    @return {}
  */
  _toggleSubmenu(evt) {
    const { props } = this;
    props.toggleSubmenu(evt);
  }

  /**
    @param {boolean} expanded
    sets state of cluster to expand or collapse
    @return {}
  */
  _toggleCluster(expanded) {
    this.setState({ expanded });
  }

  /**
    @param {Object} evt
    @param {boolean} shrink
    shrinks cards on mouseover to indicate collapse
    @return {}
  */
  _toggleShrink(evt, shrink) {
    const { state } = this;
    this.setState({ shrink });
  }

  render() {
    const { props, state } = this,
        { record } = props,
        shouldBeFaded = props.hoveredRollback > props.record.flatIndex,
        clusterCSS = classNames({
          'ActivityCard--cluster': true,
          'column-1-span-10': true,
          faded: shouldBeFaded,
        }),
        clusterWrapperCSS = classNames({
          'ClusterCardWrapper flex justify--space-between flex--column': true,
          'ClusterCardWrapper--shrink': state.shrink,
        });

    if (!state.expanded) {
      return (
        <div className="CardWrapper CardWrapper--cluster">

          <ToolTip section="activityCluster" />

          <div
            className={clusterCSS}
            ref={`cluster--${props.record.flatindex}`}
            onClick={() => this._toggleCluster(true)}>
            <div className="ActivityCard__cluster--layer1 box-shadow">
              {`${props.record.cluster.length} Minor Activities`}
            </div>
            <div className="ActivityCard__cluster--layer2 box-shadow" />
            <div className="ActivityCard__cluster--layer3 box-shadow" />
          </div>
        </div>
      );
    }
    return (
      <div className={clusterWrapperCSS}>

        <div
          className="ClusterCard__sidebar-container"
          ref="expanded"
          onMouseEnter={(evt) => { this._toggleShrink(evt, true); }}
          onMouseLeave={(evt) => { this._toggleShrink(evt, false); }}
          onClick={() => this._toggleCluster(false)}>
          <div className="ClusterCard__sidebar"></div>
         </div>
        {
          props.record.cluster.map(record => <CardWrapper
               toggleCluster={this._toggleCluster}
               {...props}
               record={record}
               isLocked={props.isLocked}
          />)
        }
      </div>
    );
  }
}

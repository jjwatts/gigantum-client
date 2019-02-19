// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import ToolTip from 'Components/common/ToolTip';
// assets
import './Rollback.scss';

export default class Rollback extends Component {
  state = {
    isOver: false,
  }
  /**
    @param {Object} evt
    shows rollback modal, and passes record node to the modal
    @return {}
  */
  _toggleRollback(evt) {
    const { props } = this;
    props.toggleRollbackMenu(props.record.edge.node);
  }
  render() {
    const { props, state } = this,
          section = props.section,
          record = props.record,
          showTooltip = state.isOver && props.isLocked,
          rollbackCSS = classNames({
            Rollback: true,
            'Rollback--locked': props.isLocked,
            'Tooltip-data Tooltip-data--right': props.isLocked,
          });

    return (
        <div
          className={rollbackCSS}
          data-tooltip="Can't rollback when the container is running.">
            <ToolTip section="activitySubmenu" />
            <button
              disabled={props.isLocked}
              className="Rollback__button"
              onClick={evt => this._toggleRollback(evt)}>
              Rollback
            </button>
      </div>);
    }
}

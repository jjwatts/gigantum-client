// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import ErrorBoundary from 'Components/common/ErrorBoundary';
import ToolTip from 'Components/common/ToolTip';
import ActivityCard from '../ActivityCard';
import Rollback from './Rollback';
// assets
import './CardWrapper.scss';

export default class CardWrapper extends Component {
  render() {
    const { props, state } = this,
          section = props.section,
          record = props.record,
          rollbackableDetails = record.edge.node.detailObjects.filter(detailObjs => detailObjs.type !== 'RESULT' && detailObjs.type !== 'CODE_EXECUTED'),
          hasRollback = ((props.indexItem.i !== 0) || (props.indexItem.timestampIndex !== 0))
            && (!!rollbackableDetails.length && (props.sectionType === 'labbook')),
          activityCardWrapperCSS = classNames({
            CardWrapper: true,
           'CardWrapper--rollback': hasRollback,
         });

    return (
      <Fragment key={record.edge.node.id}>
        <div className={activityCardWrapperCSS}>

          { hasRollback
              && <Rollback
                toggleRollbackMenu={props.toggleRollbackMenu}
                record={record}
                sectionType={props.sectionType}
                isLocked={props.isLocked}
              />
          }

          <ErrorBoundary
              type="activityCardError"
              key={`activityCard${record.edge.node.id}`}>
                <ActivityCard
                  sectionType={props.sectionType}
                  isFirstCard={props.indexItem.timestampIndex === 0}
                  position={record.flatIndex}
                  key={`${record.edge.node.id}_activity-card`}
                  edge={record.edge}
                  isLocked={props.isLocked}
                />
          </ErrorBoundary>


        </div>

      </Fragment>
    );
  }
}

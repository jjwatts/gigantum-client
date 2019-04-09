// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import ErrorBoundary from 'Components/common/ErrorBoundary';
import Tooltip from 'Components/common/Tooltip';
import ActivityCard from '../ActivityCard';
import Rollback from './Rollback';
// assets
import './CardWrapper.scss';

export default class CardWrapper extends Component {
  render() {
    const { props, state } = this;


    const section = props.section;


    const record = props.record;


    const rollbackableDetails = record.edge.node.detailObjects.filter(detailObjs => detailObjs.type !== 'RESULT' && detailObjs.type !== 'CODE_EXECUTED');


    const hasRollback = ((props.indexItem.i !== 0) || (props.indexItem.timestampIndex !== 0))
            && (!!rollbackableDetails.length && (props.sectionType === 'labbook'));


    const activityCardWrapperCSS = classNames({
      CardWrapper: true,
      'CardWrapper--rollback': hasRollback,
    });

    return (
      <Fragment key={record.edge.node.id}>
        <div className={activityCardWrapperCSS}>

          { hasRollback
              && (
              <Rollback
                setHoveredRollback={props.setHoveredRollback}
                hoveredRollback={props.hoveredRollback}
                toggleRollbackMenu={props.toggleRollbackMenu}
                record={record}
                sectionType={props.sectionType}
                isLocked={props.isLocked}
              />
              )
          }

          <ErrorBoundary
            type="activityCardError"
            key={`activityCard${record.edge.node.id}`}
          >
            <ActivityCard
              sectionType={props.sectionType}
              hoveredRollback={props.hoveredRollback}
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

// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import Moment from 'moment';
// assets
import './LinkCard.scss';

export default class Overview extends Component {
  render() {
    const { node, selectedDataset } = this.props;
    const linkCardCSS = classNames({
      'LinkCard__dataset--selected': selectedDataset && selectedDataset.owner === node.owner
      && selectedDataset.name === node.name,
      LinkCard__dataset: true,
      Card: true,
    });

    return (
      <div className={linkCardCSS}>
        <img
          alt=""
          src={`data:image/jpeg;base64,${node.datasetType.icon}`}
          height="50"
          width="50"
        />
        <div className="LinkCard__details">
          <h6><b>{node.name}</b></h6>
          <p>{node.datasetType.isManaged ? 'Managed' : 'Unmanaged'}</p>
          <p>{`Created on ${Moment(node.createdOnUtc).format('MM/DD/YY')}`}</p>
          <p>{`Modified ${Moment(node.modifiedOnUtc).fromNow()}`}</p>
        </div>
        <div className="LinkCard__text">
          <p className="LinkCard__description">
            {node.description}
          </p>
        </div>
      </div>);
  }
}

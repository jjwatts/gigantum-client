// vendor
import React from 'react';
import classNames from 'classnames';
import Moment from 'moment';
// assets
import './LinkCard.scss';

const LinkCard = ({ node, selectedDataset }) => {
  const managedText = node.datasetType.isManaged ? 'Managed' : 'Unmanaged';
  // declare css here
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
        <h6 data-name={node.name}><b>{node.name}</b></h6>
        <p
          className="break-word"
          data-owner={node.owner}
        >
          {`Created By: ${node.owner}`}
        </p>
        <p className="break-word">{managedText}</p>
        <p className="break-word">{`Created on ${Moment(node.createdOnUtc).format('MM/DD/YY')}`}</p>
        <p className="break-word">{`Modified ${Moment(node.modifiedOnUtc).fromNow()}`}</p>
      </div>
      <div className="LinkCard__text">
        <p className="LinkCard__description">
          {node.description}
        </p>
      </div>
    </div>
  );
};

export default LinkCard;

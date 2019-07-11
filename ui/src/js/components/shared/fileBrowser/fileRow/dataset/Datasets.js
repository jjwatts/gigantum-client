// vendor
import React, { PureComponent } from 'react';
// components
import DatasetCard from './DatasetCard';
// assets
import './Datasets.scss';

export default class Datasets extends PureComponent {
  render() {
    const { props } = this;

    return (
      <div className="DatasetsBrowser">
        <div className="DatasetsBrowser__header flex justify--space-between">
          <h4 className="margin--0">Datasets</h4>
          <button
            className="Btn Btn__FileBrowserAction Btn__FileBrowserAction--link"
            type="button"
            onClick={() => props.showLinkModal(true)}
            disabled={props.isLocked}
          >
            Link Dataset
          </button>
        </div>
        {
          (props.linkedDatasets.length === 0)
          && (
            <div>
              There are no Datasets linked to this project.
            </div>
          )
        }
        {
          props.linkedDatasets.map(dataset => (
            <DatasetCard
              formattedFiles={props.files[dataset.name]}
              isLocal={props.checkLocal(props.files[dataset.name])}
              checkLocal={props.checkLocal}
              key={dataset.name}
              dataset={dataset}
              isLocked={props.isLocked}
              owner={props.owner}
              name={props.name}
              mutationData={props.mutationData}
              mutations={props.mutations}
            />
          ))
        }
      </div>
    );
  }
}

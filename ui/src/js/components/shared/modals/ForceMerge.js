// vendor
import React, { Component, Fragment } from 'react';
// component
import Modal from 'Components/common/Modal';
// assets
import './ForceMerge.scss';

export default class ForceMerge extends Component {
  /**
  *  @param {}
  *  triggers merge with force set top True
  *  hides modal
  *  @return {}
  */
  _forceMerge(method) {
    this.props.merge(this.props.branchName, method);
    this.props.toggleModal();
  }

  render() {
    return (

      <Modal
        handleClose={() => this.props.toggleModal()}
        header="Merge Conflict"
        size="medium"
        icon="merge"
        renderContent={() => (
          <Fragment>
            <p className="ForceMege__text">Merge failed due to conflicts. Which changes would you like to use?</p>

            <div className="ForceMege__buttonContainer">

              <button onClick={() => this._forceMerge('ours')}>
                Use Mine
              </button>

              <button onClick={() => this._forceMerge('theirs')}>
                Use Theirs
              </button>

              <button onClick={() => this.props.toggleModal('forceMergeVisible')}>
                Abort
              </button>

            </div>

          </Fragment>
        )
        }
      />
    );
  }
}

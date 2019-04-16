// vendor
import React, { Component, Fragment } from 'react';
import uuidv4 from 'uuid/v4';
// mutations
import SyncLabbookMutation from 'Mutations/branches/SyncLabbookMutation';
import SyncDatasetMutation from 'Mutations/branches/SyncDatasetMutation';
// component
import Modal from 'Components/common/Modal';
// store
import store from 'JS/redux/store';
import { setMultiInfoMessage } from 'JS/redux/actions/footer';
// assets
import './ForceSync.scss';

export default class ForceSync extends Component {
  /**
  *  @param {}
  *  Triggers sync with the correct override method
  *  @return {}
  */
  _forceSync(method) {
    const id = uuidv4;
    const { owner, labbookName } = store.getState().routes;
    if (this.props.sectionType === 'labbook') {
      setMultiInfoMessage(id, 'Syncing Project with Gigantum cloud ...', false, false);

      SyncLabbookMutation(
        owner,
        labbookName,
        method,
        this.props.pullOnly,
        () => {},
        () => {},
        (error) => {
          if (error) {
            setMultiInfoMessage(id, `Could not 'force' sync ${labbookName}`, true, true, error);
          }
        },
      );
    } else {
      setMultiInfoMessage(id, 'Syncing Dataset with Gigantum cloud ...', false, false);

      SyncDatasetMutation(
        owner,
        labbookName,
        method,
        this.props.pullOnly,
        () => {},
        () => {},
        (error) => {
          if (error) {
            setMultiInfoMessage(id, `Could not 'force' sync ${labbookName}`, true, true, error);
          }
        },
      );
    }
    this.props.toggleSyncModal();
  }

  render() {
    return (
      <Modal
        header="Sync Conflict"
        handleClose={() => this.props.toggleSyncModal()}
        size="medium"
        icon="sync"
        renderContent={() => (
          <Fragment>
            <div>
              <p>Your Project conflicts with changes already synced to the server. You can choose which changes to use</p>
              <p><b>**Note: This will overwrite the unselected conflicting files.</b></p>
              <p>Which changes would you like to use?</p>
            </div>
            <div className="ForceSync__buttonContainer">
              <button onClick={() => { this._forceSync('ours'); }}>Use Mine</button>
              <button onClick={() => { this._forceSync('theirs'); }}>Use Theirs</button>
              <button onClick={() => { this.props.toggleSyncModal(); }}>Abort</button>
            </div>
          </Fragment>
        )
        }
      />
    );
  }
}

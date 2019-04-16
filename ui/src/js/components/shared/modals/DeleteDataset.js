// vendor
import React, { Component } from 'react';
// config
import config from 'JS/config';
// store
import { setErrorMessage, setWarningMessage, setInfoMessage } from 'JS/redux/actions/footer';
import store from 'JS/redux/store';
// Mutations
import DeleteDatasetMutation from 'Mutations/DeleteDatasetMutation';
import ImportRemoteDatasetMutation from 'Mutations/ImportRemoteDatasetMutation';
// components
import ButtonLoader from 'Components/common/ButtonLoader';
import Modal from 'Components/common/Modal';
// assets
import './DeleteDataset.scss';


export default class DeleteDataset extends Component {
  constructor(props) {
  	super(props);
  	this.state = {
      datasetName: '',
      deletePending: false,
      deleteDatasetButtonState: '',
    };
    this._deleteDataset = this._deleteDataset.bind(this);
  }

  /**
    @param {object} evt
    sets state of datasetName
  */
  _setDatasetName(evt) {
    this.setState({ datasetName: evt.target.value });
  }

  /**
    @param {String} datasetName
    @param {String} owner
    @param {Boolean} deleteLocal
    @param {Boolean} deleteRemote
    @param {Boolean} forceImportLocal
    fires delete dataset mutation
  */
  _handleDatasetDelete(datasetName, owner, deleteLocal, deleteRemote) {
    const { remoteId, datasetListId, remoteConnection } = this.props;
    DeleteDatasetMutation(
      datasetName,
      owner,
      remoteId,
      datasetListId,
      remoteConnection,
      deleteLocal,
      deleteRemote,
      (response, error) => {
        this.setState({ deletePending: false });

        if (error) {
          setErrorMessage(`The was a problem deleting ${datasetName}`, error);
          this.setState({ deleteDatasetButtonState: 'error' });
          setTimeout(() => {
            this.setState({ datasetName: '', deletePending: false, deleteDatasetButtonState: '' });
            this.props.toggleModal();

            if (document.getElementById('deleteInput')) {
              document.getElementById('deleteInput').value = '';
            }
          }, 1000);
        } else if (deleteRemote) {
          setInfoMessage(`${datasetName} has been remotely deleted`);
          this.setState({ deleteDatasetButtonState: 'finished' });
          setTimeout(() => {
            this.setState({ datasetName: '', deletePending: false, deleteDatasetButtonState: '' });
            this.props.toggleModal();

            if (document.getElementById('deleteInput')) {
              document.getElementById('deleteInput').value = '';
            }
          }, 1000);
        } else {
          setInfoMessage(`${datasetName} has been deleted`);
          this.setState({ deleteDatasetButtonState: 'finished' });
          setTimeout(() => {
            this.props.history.replace('/datasets/local');
          }, 2000);
        }
      },
    );
  }

    /**
        *  @param {String} owner
        *  @param {String} datasetName
        *  @param {String} remote
        *  @param {Function} callback
        *  handles importing dataset mutation
    */
    _handleImportDataset = (owner, datasetName, remote, callback) => {
      ImportRemoteDatasetMutation(
        owner,
        datasetName,
        remote,
        (response, error) => {
          if (error) {
            console.error(error);
            setMultiInfoMessage(id, 'ERROR: Could not delete remote Dataset', null, true, error);
          } else if (response) {
            callback();
          }
        },
      );
    }

    /**
    @param {}
    fires appropriate delete dataset mutation
  */
    _deleteDataset() {
      const { labbookName, owner } = this.props.remoteDelete ? { labbookName: this.props.remoteDatasetName, owner: this.props.remoteOwner } : store.getState().routes;
      const datasetName = labbookName;
      const remote = `https://repo.${config.domain}/${owner}/${datasetName}`;


      if (datasetName === this.state.datasetName) {
        this.setState({ deletePending: true, deleteDatasetButtonState: 'loading' });
        if (!this.props.remoteDelete) {
          this._handleDatasetDelete(datasetName, owner, true, false);
        } else if (this.props.remoteDelete && this.props.existsLocally) {
          this._handleDatasetDelete(datasetName, owner, false, true);
        } else {
          this._handleImportDataset(owner, datasetName, remote, () => {
            this._handleDatasetDelete(datasetName, owner, true, true);
          });
        }
      } else {
        setWarningMessage('Names do not match');
      }
    }

    /**
    *  @param {}
    *  determines the warning text to be displayed to the user
  */
    _getExplanationText() {
      const { labbookName, owner } = store.getState().routes;
      const datasetName = labbookName;

      if (this.props.remoteDelete) {
        if (this.props.existsLocally) {
          return (
            <div>
              <p>
              This will delete
                {' '}
                <b>{this.props.remoteDatasetName}</b>
                {' '}
              from the cloud.
              </p>
              <p>The Dataset will still exist locally.</p>
            </div>
          );
        }
        return (
          <p>
          This will delete
            {' '}
            <b>{this.props.remoteDatasetName}</b>
            {' '}
          from the cloud.
          All data will be removed and can not be recovered.
          </p>
        );
      } if (this.props.remoteAdded) {
        return (
          <div>
            <p>
            This will delete
              {' '}
              <b>{datasetName}</b>
              {' '}
            from this Gigantum client.
            </p>
            <p>{`You can still download it from gigantum.com/${owner}/${datasetName}.`}</p>
          </div>);
      }
      return (
        <p>
      This will delete
          {' '}
          <b>{datasetName}</b>
          {' '}
      from this Gigantum instance. All data will be removed and can not be recovered.
        </p>
      );
    }

    render() {
      const deleteText = this.props.remoteDelete ? 'Delete Remote Dataset' : 'Delete Dataset';
      const { labbookName } = this.props.remoteDelete ? { labbookName: this.props.remoteDatasetName } : store.getState().routes;
      const datasetName = labbookName;
      return (
        <Modal
          header={deleteText}
          handleClose={() => this.props.handleClose()}
          size="medium"
          icon="delete"
          renderContent={() => (
            <div className="DeleteDataset">
              {this._getExplanationText()}
              <input
                id="deleteInput"
                placeholder={`Enter ${datasetName} to delete`}
                onKeyUp={(evt) => { this._setDatasetName(evt); }}
                onChange={(evt) => { this._setDatasetName(evt); }}
                type="text"
              />

              <ButtonLoader
                buttonState={this.state.deleteDatasetButtonState}
                buttonText={deleteText}
                className=""
                params={{}}
                buttonDisabled={this.state.deletePending || datasetName !== this.state.datasetName}
                clicked={this._deleteDataset}
              />
            </div>
          )
        }
        />
      );
    }
}

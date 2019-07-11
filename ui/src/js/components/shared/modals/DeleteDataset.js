// vendor
import React, { Component } from 'react';
import uuidv4 from 'uuid/v4';
// config
import config from 'JS/config';
// store
import {
  setErrorMessage,
  setWarningMessage,
  setInfoMessage,
  setMultiInfoMessage,
} from 'JS/redux/actions/footer';
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
      id: uuidv4(),
    };
    this._deleteDataset = this._deleteDataset.bind(this);
  }

  /**
      *  @param {String} owner
      *  @param {String} datasetName
      *  @param {String} remote
      *  @param {Function} callback
      *  handles importing dataset mutation
  */
  _handleImportDataset = (owner, datasetName, remote, callback) => {
    const { state } = this;
    ImportRemoteDatasetMutation(
      owner,
      datasetName,
      remote,
      (response, error) => {
        if (error) {
          console.error(error);
          const messageData = {
            id: state.id,
            message: 'ERROR: Could not delete remote Dataset',
            isLast: null,
            error: true,
            messageBody: error,
          };
          setMultiInfoMessage(messageData);
        } else if (response) {
          callback();
        }
      },
    );
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
    const { props } = this;
    const {
      remoteId,
      datasetListId,
      remoteConnection,
    } = props;
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
            this.setState({
              datasetName: '',
              deletePending: false,
              deleteDatasetButtonState: '',
            });
            props.toggleModal();

            if (document.getElementById('deleteInput')) {
              document.getElementById('deleteInput').value = '';
            }
          }, 1000);
        } else if (deleteRemote) {
          setInfoMessage(`${datasetName} has been remotely deleted`);

          this.setState({ deleteDatasetButtonState: 'finished' });
          setTimeout(() => {
            this.setState({
              datasetName: '',
              deletePending: false,
              deleteDatasetButtonState: '',
            });

            props.toggleModal();

            if (document.getElementById('deleteInput')) {
              document.getElementById('deleteInput').value = '';
            }
          }, 1000);
        } else {
          setInfoMessage(`${datasetName} has been deleted`);
          this.setState({ deleteDatasetButtonState: 'finished' });
          setTimeout(() => {
            props.history.replace('/datasets/local');
          }, 2000);
        }
      },
    );
  }

  /**

  /**
    @param {object} evt
    sets state of datasetName
  */
  _setDatasetName(evt) {
    this.setState({ datasetName: evt.target.value });
  }

  /**
  @param {}
  fires appropriate delete dataset mutation
*/
  _deleteDataset() {
    const { props, state } = this;
    const { labbookName, owner } = props.remoteDelete
      ? {
        labbookName: props.remoteDatasetName,
        owner: props.remoteOwner,
      }
      : store.getState().routes;
    const datasetName = labbookName;
    const remote = `https://repo.${config.domain}/${owner}/${datasetName}`;


    if (datasetName === state.datasetName) {
      this.setState({
        deletePending: true,
        deleteDatasetButtonState: 'loading',
      });
      if (!props.remoteDelete) {
        this._handleDatasetDelete(datasetName, owner, true, false);
      } else if (props.remoteDelete && props.existsLocally) {
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
    const { props } = this;
    const { labbookName, owner } = store.getState().routes;
    const datasetName = labbookName;

    if (props.remoteDelete) {
      if (props.existsLocally) {
        return (
          <div>
            <p>
              This will delete
              {' '}
              <b>{props.remoteDatasetName}</b>
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
          <b>{props.remoteDatasetName}</b>
          {' '}
          from the cloud.
          All data will be removed and can not be recovered.
        </p>
      );
    } if (props.remoteAdded) {
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
        </div>
      );
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
    const { props, state } = this;
    const deleteText = props.remoteDelete ? 'Delete Remote Dataset' : 'Delete Dataset';
    const { labbookName } = props.remoteDelete
      ? { labbookName: props.remoteDatasetName }
      : store.getState().routes;
    const datasetName = labbookName;
    return (
      <Modal
        header={deleteText}
        handleClose={() => props.handleClose()}
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
            <div className="Modal__button-container">
              <button
                type="button"
                className="Btn Btn--flat"
                onClick={() => props.handleClose()}
              >
                Cancel
              </button>
              <ButtonLoader
                buttonState={state.deleteDatasetButtonState}
                buttonText={deleteText}
                className="Btn Btn--wide Btn--last"
                params={{}}
                buttonDisabled={state.deletePending || datasetName !== state.datasetName}
                clicked={this._deleteDataset}
              />
            </div>
          </div>
        )
      }
      />
    );
  }
}

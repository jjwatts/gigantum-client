// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import uuidv4 from 'uuid/v4';
// config
import config from 'JS/config';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// components
import LoginPrompt from 'Components/shared/modals/LoginPrompt';
import Tooltip from 'Components/common/Tooltip';
import Modal from 'Components/common/Modal';
import Loader from 'Components/common/Loader';
// store
import store from 'JS/redux/store';
import { setUploadMessageRemove } from 'JS/redux/actions/footer';
// mutations
import ImportRemoteDatasetMutation from 'Mutations/ImportRemoteDatasetMutation';
import ImportRemoteLabbookMutation from 'Mutations/ImportRemoteLabbookMutation';
import BuildImageMutation from 'Mutations/container/BuildImageMutation';
// utilities
import JobStatus from 'JS/utils/JobStatus';
import ChunkUploader from 'JS/utils/ChunkUploader';
import ImportUtils from './ImportUtils';
// assets
import './ImportModule.scss';

let counter = 0;
const dropZoneId = uuidv4();

export default class ImportModule extends Component {
  constructor(props) {
    super(props);

    this.state = {
      show: false,
      message: '',
      files: [],
      type: 'info',
      error: false,
      isImporting: false,
      stopPropagation: false,
      importingScreen: false,
      importTransition: null,
      remoteURL: '',
    };

    this._getBlob = this._getBlob.bind(this);
    this._dragoverHandler = this._dragoverHandler.bind(this);
    this._dropHandler = this._dropHandler.bind(this);
    this._dragendHandler = this._dragendHandler.bind(this);
    this._fileSelected = this._fileSelected.bind(this);
    this._fileUpload = this._fileUpload.bind(this);
    this._importingState = this._importingState.bind(this);
    this._clearState = this._clearState.bind(this);
    this._toggleImportScreen = this._toggleImportScreen.bind(this);
    this._closeLoginPromptModal = this._closeLoginPromptModal.bind(this);
    this._drop = this._drop.bind(this);
    this._dragover = this._dragover.bind(this);
    this._dragleave = this._dragleave.bind(this);
    this._dragenter = this._dragenter.bind(this);
  }

  componentWillUnmount() {
    window.removeEventListener('drop', this._drop);
    window.removeEventListener('dragover', this._dragover);
    window.removeEventListener('dragleave', this._dragleave);
    window.removeEventListener('dragenter', this._dragenter);
  }

  componentDidMount() {
    const fileInput = document.getElementById('file__input');
    if (fileInput) {
      fileInput.onclick = (evt) => {
        evt.cancelBubble = true;
        evt.stopPropagation(evt);
      };
    }

    this.setState({ isImporting: false });

    window.addEventListener('drop', this._drop);
    window.addEventListener('dragover', this._dragover);
    window.addEventListener('dragleave', this._dragleave);
    window.addEventListener('dragenter', this._dragenter);
  }

  /**
  *  @param {object}
  *  detects when a file has been dropped
  */
  _drop(evt) {
    if (document.getElementById('dropZone')) {
      this._toggleImportScreen(false);
      document.getElementById('dropZone').classList.remove('ImportModule__drop-area-highlight');
    }

    if (evt.target.classList.contains(dropZoneId)) {
      evt.preventDefault();
      evt.dataTransfer.effectAllowed = 'none';
      evt.dataTransfer.dropEffect = 'none';
    }
  }

  /**
  *  @param {}
  *  sets state of app for importing
  *  @return {}
  */
  _importingState = () => {
    this.setState({
      isImporting: true,
      showImportModal: false,
    });
    document.getElementById('modal__cover').classList.remove('hidden');
    document.getElementById('loader').classList.remove('hidden');
  }

  /**
  *  @param {object}
  *  detects when file has been dragged over the DOM
  */
  _dragover(evt) {
    if (document.getElementById('dropZone')) {
      this._toggleImportScreen(true);

      document.getElementById('dropZone').classList.add('ImportModule__drop-area-highlight');
    }

    if (evt.target.classList.contains(dropZoneId) < 0) {
      evt.preventDefault();
      evt.dataTransfer.effectAllowed = 'none';
      evt.dataTransfer.dropEffect = 'none';
    }
  }

  /**
  *  @param {object}
  *  detects when file leaves dropzone
  */
  _dragleave(evt) {
    counter--;

    if (evt.target.classList && evt.target.classList.contains(dropZoneId) < 0) {
      if (document.getElementById('dropZone')) {
        if (counter === 0) {
          this._toggleImportScreen(false);

          document.getElementById('dropZone').classList.remove('ImportModule__drop-area-highlight');
        }
      }
    }
  }

  /**
  *  @param {object}
  *  detects when file enters dropzone
  */
  _dragenter(evt) {
    counter++;

    if (document.getElementById('dropZone')) {
      this._toggleImportScreen(true);

      document.getElementById('dropZone').classList.add('ImportModule__drop-area-highlight');
    }

    if (evt.target.classList && evt.target.classList.contains(dropZoneId) < 0) {
      evt.preventDefault();
      evt.dataTransfer.effectAllowed = 'none';
      evt.dataTransfer.dropEffect = 'none';
    }
  }

  /**
  *  @param {String} filename
  *  returns corrected version of filename
  *  @return {}
  */

  _getFilename(filename) {
    const fileArray = filename.split('-');
    fileArray.pop();
    const newFilename = fileArray.join('-');
    return newFilename;
  }


  /**
  *  @param {object} dataTransfer
  *  preventDefault on dragOver event
  */
  _getBlob = (dataTransfer) => {
    const chunkSize = 1024;
    let offset = 0;
    const fileReader = new FileReader();
    let file;
    function seek() {
      if (offset >= file.size) {
        return;
      }
      const slice = file.slice(offset, offset + chunkSize);
      fileReader.readAsArrayBuffer(slice);
    }
    const self = this;
    for (let i = 0; i < dataTransfer.files.length; i++) {
      file = dataTransfer.files[0];
      if (file.name.slice(file.name.length - 4, file.name.length) !== '.lbk' && file.name.slice(file.name.length - 4, file.name.length) !== '.zip') {
        this.setState({ error: true });

        setTimeout(() => {
          self.setState({ error: false });
        }, 5000);
      } else {
        this.setState({ error: false });

        fileReader.onloadend = function (evt) {
          const arrayBuffer = evt.target.result;

          const blob = new Blob([new Uint8Array(arrayBuffer)]);

          self.setState({
            files: [
              {
                blob,
                file,
                arrayBuffer,
                filename: file.name,
              },
            ],
            ready: {
              name: self._getFilename(file.name),
              owner: localStorage.getItem('username'),
              method: 'local',
            },
          });
        };

        fileReader.onload = function () {
          const view = new Uint8Array(fileReader.result);
          for (let i = 0; i < view.length; ++i) {
            if (view[i] === 10 || view[i] === 13) {
              return;
            }
          }
          offset += chunkSize;
          seek();
        };
        seek();
      }
    }
  }

  /**
  *  @param {Object} event
  *  preventDefault on dragOver event
  */
  _dragoverHandler = (evt) => { // use evt, event is a reserved word in chrome
    evt.preventDefault(); // this kicks the event up the event loop
  }

  /**
  *  @param {Object} event
  *  handle file drop and get file data
  */
  _dropHandler = (evt) => {
    // use evt, event is a reserved word in chrome
    const dataTransfer = evt.dataTransfer;
    evt.preventDefault();
    evt.dataTransfer.effectAllowed = 'none';
    evt.dataTransfer.dropEffect = 'none';
    this._getBlob(dataTransfer);

    return false;
  }

  /**
  *  @param {Object}
  *  handle end of dragover with file
  */
  _dragendHandler = (evt) => { // use evt, event is a reserved word in chrome
    const dataTransfer = evt.dataTransfer;

    evt.preventDefault();
    evt.dataTransfer.effectAllowed = 'none';
    evt.dataTransfer.dropEffect = 'none';

    if (dataTransfer.items) {
      // Use DataTransferItemList interface to remove the drag data
      for (let i = 0; i < dataTransfer.items.length; i++) {
        dataTransfer.items.remove(i);
      }
    } else {
      // Use DataTransfer interface to remove the drag data
      evt.dataTransfer.clearData();
    }
    return false;
  }

  /**
  *  @param {Object}
  *  opens file system for user to select file
  */
  _fileSelected = (evt) => {
    this._getBlob(document.getElementById('file__input'));
    this.setState({ stopPropagation: false });
  }

  /**
  *  @param {Object}
  *   trigger file upload
  */
  _fileUpload = () => { // this code is going to be moved to the footer to complete the progress bar
    const { props } = this;
    const self = this;

    this._importingState();
    const filepath = this.state.files[0].filename;

    const data = {
      file: this.state.files[0].file,
      filepath,
      username: localStorage.getItem('username'),
      accessToken: localStorage.getItem('access_token'),
      type: props.section,
    };

    // dispatch loading progress
    store.dispatch({
      type: 'UPLOAD_MESSAGE_SETTER',
      payload: {
        uploadMessage: 'Preparing Import ...',
        totalBytes: this.state.files[0].file.size / 1000,
        percentage: 0,
        id: '',
      },
    });

    const postMessage = (workerData) => {
      if (workerData) {
        const importObject = (props.section === 'labbook') ? workerData.importLabbook : workerData.importDataset;
        if (importObject) {
          store.dispatch({
            type: 'UPLOAD_MESSAGE_UPDATE',
            payload: {
              uploadMessage: 'Upload Complete',
              percentage: 100,
              id: '',
            },
          });

          JobStatus.getJobStatus(importObject.importJobKey).then((response) => {
            store.dispatch({
              type: 'UPLOAD_MESSAGE_UPDATE',
              payload: {
                uploadMessage: 'Unzipping Project',
                percentage: 100,
                id: '',
              },
            });

            if (response.jobStatus.status === 'finished') {
              self._clearState();
              ImportUtils.dispatchFinishedStatus(response.jobStatus.result, self.props, self._buildImage);
            } else if (response.jobStatus.status === 'failed') {
              ImportUtils.dispatchFailedStatus();

              self._clearState();
            }
          }).catch((error) => {
            console.log(error);

            store.dispatch({
              type: 'UPLOAD_MESSAGE_UPDATE',
              payload: {
                uploadMessage: 'Import failed',
                uploadError: true,
                id: '',
                percentage: 0,
              },
            });
            self._clearState();
          });
        } else if (workerData.chunkSize) {
          ImportUtils.dispatchLoadingProgress(workerData);
        } else {
          store.dispatch({
            type: 'UPLOAD_MESSAGE_UPDATE',
            payload: {
              uploadMessage: workerData[0].message,
              uploadError: true,
              id: '',
              percentage: 0,
            },
          });
          self._clearState();
        }
      }
    };

    ChunkUploader.chunkFile(data, postMessage);
  }

  /**
    @param {object} error
    shows error message
  * */
  _showError(message) {
    store.dispatch({
      type: 'UPLOAD_MESSAGE_UPDATE',
      payload: {
        uploadMessage: message,
        uploadError: true,
        id: '',
        percentage: 0,
      },
    });
  }

  /**
  *  @param {}
  *  clears state of file and sets css back to import
  *  @return {}
  */
  _clearState = () => {
    if (document.getElementById('dropZone__filename')) {
      document.getElementById('dropZone__filename').classList.remove('ImportModule__animation');
    }
    this.setState({ files: [], isImporting: false });
  }

  /**
  *  @param {}
  *  @return {string} returns text to be rendered
  */
  _getImportDescriptionText() {
    return this.state.error
      ? 'File must be .zip'
      : 'Drag & Drop .zip file, or click to select.';
  }

  /**
  *  @param {}
  *  shows create project modal
  *  @return {}
  */
  _showModal(evt) {
    if (navigator.onLine) {
      if (evt.target.id !== 'file__input-label') {
        this.props.showModal();
      }
    } else {
      store.dispatch({
        type: 'ERROR_MESSAGE',
        payload: {
          message: 'Cannot create a Project at this time.',
          messageBody: [
            {
              message: 'An internet connection is required to create a Project.',
            },
          ],
        },
      });
    }
  }

  /**
  *  @param {}
  *  closes import modal
  *  @return {}
  */
  _closeImportModal = () => {
    this.setState({ showImportModal: false, remoteUrl: '', readyLabbook: null });
  }

  /**
  *  @param {}
  *  shows import screen
  *  uses transition delay
  *  @return {}
  */
  _toggleImportScreen(value) {
    this.setState({ importTransition: value });

    setTimeout(() => {
      this.setState({ importingScreen: value });
    }, 250);
  }

  /**
  *  @param {Object} evt
  *  updated url in state
  *  @return {}
  */
  _updateRemoteUrl(evt) {
    const newValue = evt.target.value;
    const name = newValue.split('/')[newValue.split('/').length - 1];
    const owner = newValue.split('/')[newValue.split('/').length - 2];
    if (newValue.indexOf('gigantum.com/') > -1 && name && owner) {
      this.setState({
        ready: {
          name,
          owner,
          method: 'remote',
        },
      });
    }
    this.setState({ remoteURL: evt.target.value });
  }

  /**
  *  @param {Object} evt
  *  imports labbook from remote url, builds the image, and redirects to imported labbook
  *  @return {}
  */
  _import = (evt) => {
    const { props, state } = this;
    if (!state.files[0]) {
      const id = uuidv4();


      const name = state.remoteURL.split('/')[state.remoteURL.split('/').length - 1];


      const owner = state.remoteURL.split('/')[state.remoteURL.split('/').length - 2];


      const remote = `https://repo.${config.domain}/${owner}/${name}.git`;

      const self = this;

      UserIdentity.getUserIdentity().then((response) => {
        if (navigator.onLine) {
          if (response.data) {
            if (response.data.userIdentity.isSessionValid) {
              self._importingState();

              store.dispatch({
                type: 'MULTIPART_INFO_MESSAGE',
                payload: {
                  id,
                  message: 'Importing Project please wait',
                  isLast: false,
                  error: false,
                },
              });
              if (props.section === 'labbook') {
                self._importRemoteProject(owner, name, remote, id);
              } else {
                self._importRemoteDataset(owner, name, remote, id);
              }
            } else {
              props.auth.renewToken(true, () => {
                this.setState({ showLoginPrompt: true });
              }, () => {
                this._import();
              });
            }
          }
        } else {
          this.setState({ showLoginPrompt: true });
        }
      });
    } else {
      this._fileUpload();
    }
  }

  /**
  *  @param {}
  *  @return {} hides login prompt modal
  */
  _closeLoginPromptModal() {
    this.setState({ showLoginPrompt: false });
  }

  /**
  *  @param {String, String, String, String}
  *  trigers ImportRemoteLabbookMutation
  *  @return {}
  */
  _importRemoteProject(owner, name, remote, id) {
    const self = this;
    const sucessCall = () => {
      this._clearState();
      store.dispatch({
        type: 'MULTIPART_INFO_MESSAGE',
        payload: {
          id,
          message: `Successfully imported remote Project ${name}`,
          isLast: true,
          error: false,
        },
      });

      self._buildImage(name, owner, id);

      self.props.history.replace(`/projects/${owner}/${name}`);
    };

    const failureCall = (error) => {
      this._clearState();
      store.dispatch({
        type: 'MULTIPART_INFO_MESSAGE',
        payload: {
          id,
          message: 'ERROR: Could not import remote Project',
          messageBody: error,
          error: true,
        },
      });
    };
    ImportRemoteLabbookMutation(owner, name, remote, sucessCall, failureCall, (response, error) => {
      if (error) {
        failurecall(error);
      }
    });
  }


  /**
  *  @param {String, String, String, String}
  *  trigers ImportRemoteDatasetMutation
  *  @return {}
  */
  _importRemoteDataset(owner, name, remote, id) {
    const self = this;

    ImportRemoteDatasetMutation(owner, name, remote, (response, error) => {
      this._clearState();
      document.getElementById('modal__cover').classList.add('hidden');
      document.getElementById('loader').classList.add('hidden');
      if (error) {
        console.error(error);
        store.dispatch({
          type: 'MULTIPART_INFO_MESSAGE',
          payload: {
            id,
            message: 'ERROR: Could not import remote Dataset',
            messageBody: error,
            error: true,
          },
        });
      } else if (response) {
        store.dispatch({
          type: 'MULTIPART_INFO_MESSAGE',
          payload: {
            id,
            message: `Successfully imported remote Dataset ${name}`,
            isLast: true,
            error: false,
          },
        });
        self.props.history.replace(`/datasets/${response.importRemoteDataset.newDatasetEdge.node.owner}/${name}`);
      }
    });
  }

  /**
  *  @param {String, String, String}
  *  trigers §
  *  @return {}
  */
  _buildImage(name, owner, id) {
    BuildImageMutation(owner, name, false, (response, error) => {
      if (error) {
        console.error(error);

        store.dispatch({
          type: 'MULTIPART_INFO_MESSAGE',
          payload: {
            id,
            message: `ERROR: Failed to build ${name}`,
            messsagesList: error,
            error: true,
          },
        });
      }
    });
  }

  render() {
    const { props, state } = this;
    const loadingMaskCSS = classNames({
      'ImportModule__loading-mask': this.state.isImporting,
      hidden: !this.state.isImporting,
    });

    return (
      <div
        className="ImportModule Card Card--line-50 Card--text-center Card--add Card--import column-4-span-3"
        key="AddLabbookCollaboratorPayload"
      >

        <ImportModal self={this} />

        <div className="Import__header">
          <div className={`Import__icon Import__icon--${props.section}`}>
            <div className="Import__add-icon" />
          </div>
          <div className="Import__title">
            <h2 className="Import__h2 Import__h2--azure">{props.title}</h2>
          </div>
        </div>

        <div
          className="btn--import"
          onClick={(evt) => { this._showModal(evt); }}
        >
          Create New
        </div>

        <div
          className="btn--import"
          onClick={(evt) => { this.setState({ showImportModal: true }); }}
        >
          Import Existing
        </div>

        <Tooltip section="createLabbook" />
        <div className={loadingMaskCSS} />
      </div>);
  }
}

const ImportModal = ({ self }) => {
  let owner = '';
  let name = '';
  const { props, state } = self;
  const importCSS = classNames({
    'btn--import': true,
    'btn--expand': state.importTransition,
    'btn--collapse': !state.importTransition && state.importTransition !== null,
  });

  const section = props.section === 'labbook' ? 'Project' : 'Dataset';

  if (state.ready) {
    owner = state.ready.owner;
    name = state.ready.name;
  }

  return (
    <div className="Import__main">
      {
      state.showImportModal
      && (
      <Modal
        header={`Import ${section}`}
        handleClose={() => self._closeImportModal()}
        size="large"
        icon="add"
        renderContent={() => (
          <div className="ImportModal">
            <p>{`Import a ${section} by either pasting a URL or drag & dropping below`}</p>
            <input
              className="Import__input"
              type="text"
              placeholder={`Paste ${section} URL`}
              onChange={evt => self._updateRemoteUrl(evt)}
              defaultValue={state.remoteUrl}
            />

            <div
              id="dropZone"
              className="ImportDropzone"
              ref={div => self.dropZone = div}
              type="file"
              onDragEnd={evt => self._dragendHandler(evt)}
              onDrop={evt => self._dropHandler(evt)}
              onDragOver={evt => self._dragoverHandler(evt)}
            >
              {
                 (state.ready && state.files[0])
                   ? (
                     <div className="Import__ready">
                       <div>{`Select Import to import the following ${section}`}</div>
                       <hr />
                       <div>{`${section} Owner: ${owner}`}</div>
                       <div>{`${section} Name: ${name}`}</div>
                     </div>
                   ) : (
                     <div className="DropZone">
                       <p>{`Drag and drop an exported ${section} here`}</p>
                     </div>
                   )}
            </div>

            <div className="Import__buttonContainer">
              <button
                onClick={() => self._closeImportModal()}
                className="Btn--flat"
              >
                  Cancel
              </button>
              <button
                onClick={() => { self._import(); }}
                className="Btn--last"
                disabled={!self.state.ready || self.state.isImporting}
              >
                  Import
              </button>
            </div>
          </div>
        )
        }
      />
      )
    }

    </div>
  );
};

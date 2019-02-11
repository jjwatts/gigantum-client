// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
import uuidv4 from 'uuid/v4';
// components
import ToolTip from 'Components/common/ToolTip';
import Modal from 'Components/common/Modal';
import JobStatus from 'JS/utils/JobStatus';
import ChunkUploader from 'JS/utils/ChunkUploader';
import { setUploadMessageRemove } from 'JS/redux/reducers/footer';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// store
import store from 'JS/redux/store';
// assets
import './ImportModule.scss';
// mutations
import ImportRemoteDatasetMutation from 'Mutations/ImportRemoteDatasetMutation';
// config
import config from 'JS/config';


let counter = 0;
const dropZoneId = uuidv4();
/*
 @param {object} workerData
 uses redux to dispatch file upload to the footer
*/
const dispatchLoadingProgress = (workerData) => {
  let bytesUploaded = (workerData.chunkSize * (workerData.chunkIndex + 1)) / 1000;
  const totalBytes = workerData.fileSizeKb;
  bytesUploaded = bytesUploaded < totalBytes
    ? bytesUploaded
    : totalBytes;
  const totalBytesString = config.humanFileSize(totalBytes);
  const bytesUploadedString = config.humanFileSize(bytesUploaded);

  store.dispatch({
    type: 'UPLOAD_MESSAGE_UPDATE',
    payload: {
      id: '',
      uploadMessage: `${bytesUploadedString} of ${totalBytesString} uploaded`,
      totalBytes,
      percentage: (Math.floor((bytesUploaded / totalBytes) * 100) <= 100)
        ? Math.floor((bytesUploaded / totalBytes) * 100)
        : 100,
    },
  });

  if (document.getElementById('footerProgressBar')) {
    const width = Math.floor((bytesUploaded / totalBytes) * 100);
    document.getElementById('footerProgressBar').style.width = `${width}%`;
  }
};

/*
 @param {}
 uses redux to dispatch file upload failed status to the footer
*/
const dispatchFailedStatus = () => {
  store.dispatch({
    type: 'UPLOAD_MESSAGE_UPDATE',
    payload: {
      uploadMessage: 'Import failed',
      id: '',
      percentage: 0,
      uploadError: true,
    },
  });
};

/*
 @param {string} filePath
  gets new labbook name and url route
 @return
*/
const getRoute = (filepath) => {
  const filename = filepath.split('/')[filepath.split('/').length - 1];
  return filename.split('_')[0];
};
/*
 @param {string} filePath
 dispatched upload success message and passes labbookName/route to the footer
*/
const dispatchFinishedStatus = (filepath, history, buildImage) => {
  const route = getRoute(filepath);
  history.push(`/datasets/${localStorage.getItem('username')}/${route}`);
  setUploadMessageRemove('', uuidv4(), 0);
};

export default class ImportModule extends Component {
  constructor(props) {
    super(props);

    this.state = {
      show: false,
      remoteURL: '',
      files: [],
    };
    this._fileUpload = this._fileUpload.bind(this);
    this._importingState = this._importingState.bind(this);
    this._clearState = this._clearState.bind(this);
    this._drop = this._drop.bind(this);
    this._dragover = this._dragover.bind(this);
    this._dragleave = this._dragleave.bind(this);
    this._dragenter = this._dragenter.bind(this);
    this._fileUpload = this._fileUpload.bind(this);
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
    this.setState({ isImporting: true });
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
  *  @param {Object}
  *   trigger file upload
  */
  _fileUpload = () => { // this code is going to be moved to the footer to complete the progress bar
    const self = this;

    this._importingState();
    const filepath = this.state.files[0].filename;

    const data = {
      file: this.state.files[0].file,
      filepath,
      username: localStorage.getItem('username'),
      accessToken: localStorage.getItem('access_token'),
      type: 'dataset',
    };

    // dispatch loading progress
    store.dispatch({
      type: 'UPLOAD_MESSAGE_SETTER',
      payload: {
        uploadMessage: 'Prepparing Import ...',
        totalBytes: this.state.files[0].file.size / 1000,
        percentage: 0,
        id: '',
      },
    });

    const postMessage = (workerData) => {
      if (workerData.importDataset) {
        store.dispatch({
          type: 'UPLOAD_MESSAGE_UPDATE',
          payload: {
            uploadMessage: 'Upload Complete',
            percentage: 100,
            id: '',
          },
        });

        const importDataset = workerData.importDataset;
        JobStatus.getJobStatus(importDataset.importJobKey).then((response) => {
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
            dispatchFinishedStatus(response.jobStatus.result, self.props.history, self._buildImage);
          } else if (response.jobStatus.status === 'failed') {
            dispatchFailedStatus();

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
        dispatchLoadingProgress(workerData);
      } else if (workerData[0]) {
        store.dispatch({
          type: 'UPLOAD_MESSAGE_UPDATE',
          payload: {
            uploadMessage: workerData[0].message,
            uploadError: false,
            id: '',
            percentage: 0,
          },
        });
        self._clearState();
      }
    };

    ChunkUploader.chunkFile(data, postMessage);
  }

    /**
    *  @param {object} dataTransfer
    *  preventDefault on dragOver event
    */
    _getBlob = (dataTransfer) => {
      let chunkSize = 1024;
      let offset = 0;
      let fileReader = new FileReader();
      let file;
      function seek() {
        if (offset >= file.size) {
          return;
        }
        var slice = file.slice(offset, offset + chunkSize);
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
          let self = this;
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
              readyDataset: {
                datasetName: self._getFilename(file.name),
                owner: localStorage.getItem('username'),
              },
            });
          };

          fileReader.onload = function () {
            var view = new Uint8Array(fileReader.result);
            for (var i = 0; i < view.length; ++i) {
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
  *  @param {}
  *  clears state of file and sets css back to import
  *  @return {}
  */
  _clearState = () => {
    this.setState({ files: [], isImporting: false, readyDataset: null });
  }

  /**
  *  @param {}
  *  closes import modal
  *  @return {}
  */
  _closeImportModal = () => {
    this.setState({ showImportModal: false, remoteUrl: '', readyDataset: null });
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
  *  @param {Object} evt
  *  imports dataset from remote url, builds the image, and redirects to imported dataset
  *  @return {}
  */
  importDataset = (evt) => {
    if (!this.state.files[0]) {
      const id = uuidv4(),
        datasetName = this.state.remoteURL.split('/')[this.state.remoteURL.split('/').length - 1],
        owner = this.state.remoteURL.split('/')[this.state.remoteURL.split('/').length - 2],
        remote = `https://repo.${config.domain}/${owner}/${datasetName}.git`;
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
                  message: 'Importing Dataset please wait',
                  isLast: false,
                  error: false,
                },
              });

              self._importRemoteDataset(owner, datasetName, remote, id);
            } else {
              this.props.auth.renewToken(true, () => {
                this.setState({ showLoginPrompt: true });
              }, () => {
                this.importDataset();
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
  *  @param {String, String, String, String}
  *  trigers ImportRemoteDatasetMutation
  *  @return {}
  */
  _importRemoteDataset(owner, datasetName, remote, id) {
    const self = this;

    ImportRemoteDatasetMutation(owner, datasetName, remote, (response, error) => {
      this._clearState();
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
            message: `Successfully imported remote Dataset ${datasetName}`,
            isLast: true,
            error: false,
          },
        });
        self.props.history.replace(`/datasets/${response.importRemoteDataset.newDatasetEdge.node.owner}/${datasetName}`);
      }
    });
  }

  /**
  *  @param {Object} evt
  *  updated url in state
  *  @return {}
  */
  _updateRemoteUrl(evt) {
    const newValue = evt.target.value;
    const datasetName = newValue.split('/')[newValue.split('/').length - 1];
    const owner = newValue.split('/')[newValue.split('/').length - 2];
    if (newValue.indexOf('gigantum.com/') > -1 && datasetName && owner) {
      this.setState({
        readyDataset: {
          datasetName,
          owner,
        },
      });
    }
    this.setState({ remoteURL: evt.target.value });
  }

  /**
  *  @param {String} filename
  *  returns corrected version of filename
  *  @return {}
  */

  _getFilename(filename) {
    let fileArray = filename.split('-');
    fileArray.pop();
    let newFilename = fileArray.join('-');
    return newFilename;
  }

  render() {
    const loadingMaskCSS = classNames({
      'ImportModule__loading-mask': this.state.isImporting,
      hidden: !this.state.isImporting,
    });

    return (<Fragment>

      <div className="ImportModule Card Card--line-50 Card--text-center Card--add Card--import column-4-span-3" key="AddDatasetCollaboratorPayload">
        <ImportMain self={this} />
        <div className={loadingMaskCSS} />
      </div>

    </Fragment>);
  }
}

const ImportMain = ({ self }) => {
  const importCSS = classNames({
    'btn--import': true,
    'btn--expand': self.state.importTransition,
    'btn--collapse': !self.state.importTransition && self.state.importTransition !== null,
  });

  return (<div className="Import__dataset-main">
    {
      self.state.showImportModal &&
      <Modal
        header="Import Dataset"
        handleClose={() => self._closeImportModal()}
        size="large"
        renderContent={() =>
          (<Fragment>
            <div className="ImportModal">
              <p>In order to import a dataset by either pasting a URL or drag & dropping below</p>
              <input
                className="Import__input"
                type="text"
                placeholder="Paste Dataset URL"
                onChange={evt => self._updateRemoteUrl(evt)}
                defaultValue={self.state.remoteUrl}
              />

              <div id="dropZone" className="ImportDropzone" ref={div => self.dropZone = div} type="file" onDragEnd={evt => self._dragendHandler(evt)} onDrop={evt => self._dropHandler(evt)} onDragOver={evt => self._dragoverHandler(evt)}>
                {
                  self.state.readyDataset ?
                  <div className="Import__ReadyDataset">
                    <div>Select Import to import the following dataset</div>
                    <hr/>
                    <div>Dataset Owner: {self.state.readyDataset.owner}</div>
                    <div>Dataset Name: {self.state.readyDataset.datasetName}</div>
                  </div> :
                  <div className= "DropZone">
                     <p>Drag and drop the exported Dataset here</p>
                  </div>
                }
              </div>
              <div className="Import__buttonContainer">
                <button
                  onClick={() => { self.importDataset(); }}
                  disabled={!self.state.readyDataset}
                >
                  Import
                </button>
                <button onClick={() => self._closeImportModal()}>Cancel</button>
              </div>
            </div>
            </Fragment>)
        }
      />
    }

    <div className="Import__dataset-header">
      <div className="Import__dataset-icon">
        <div className="Import__dataset-add-icon" />
      </div>
      <div className="Import__dataset-title">
        <h4>Add Dataset</h4>
      </div>

    </div>

    <div
      className="btn--import"
      onClick={(evt) => {
        self._showModal(evt);
      }}
    >
      Create New
    </div>

    <div
      className="btn--import"
      onClick={(evt) => {
        self.setState({ showImportModal: true });
      }}
    >
      Import Existing
    </div>

    <ToolTip section="createLabbook" />


  </div>);
};

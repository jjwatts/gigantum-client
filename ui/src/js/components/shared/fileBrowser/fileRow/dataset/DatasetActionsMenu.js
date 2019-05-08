// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import uuidv4 from 'uuid/v4';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// assets
import './DatasetActionsMenu.scss';
// mutations
import ModifyDatasetLinkMutation from 'Mutations/ModifyDatasetLinkMutation';
// store
import store from 'JS/redux/store';
import { setErrorMessage } from 'JS/redux/actions/footer';

export default class DatasetActionsMenu extends Component {
  constructor(props) {
  	super(props);
  	this._closePopup = this._closePopup.bind(this);
    this._setWrapperRef = this._setWrapperRef.bind(this);
  }

  state = {
    popupVisible: false,
    showSessionValidMessage: false,
  }

  /**
  *  LIFECYCLE MEHTODS START
  */
  componentDidMount() {
    window.addEventListener('click', this._closePopup);
  }

  componentWillMount() {
    window.removeEventListener('click', this._closePopup);
  }
  /**
  *  LIFECYCLE MEHTODS END
  */

  /**
  *  @param {Object} event
  *  closes popup when clicking
  *  @return {}
  */
  _closePopup(evt) {
    if (this.state.popupVisible && this[this.props.edge.node.id] && !this[this.props.edge.node.id].contains(evt.target)) {
      this.setState({ popupVisible: false });
    }
  }

  /**
  *  @param {}
  *  unlinks a dataset
  *  @return {}
  */
  _unlinkDataset() {
    const labbookOwner = store.getState().routes.owner;
    const labbookName = store.getState().routes.labbookName;
    const datasetOwner = this.props.edge.node.owner;
    const datasetName = this.props.edge.node.datasetName;
    this.setState({ buttonState: 'loading' });
    ModifyDatasetLinkMutation(
      labbookOwner,
      labbookName,
      datasetOwner,
      datasetName,
      'unlink',
      null,
      (response, error) => {
        if (error) {
          setErrorMessage('Unable to unlink dataset', error);
        }
      },
    );
  }

  /**
  *  @param {Obect} evt
  *  @param {boolean} popupVisible - boolean value for hiding and showing popup state
  *  triggers favoirte unfavorite mutation
  *  @return {}
  */
  _togglePopup(evt, popupVisible) {
    if (!popupVisible) {
      evt.stopPropagation(); // only stop propagation when closing popup, other menus won't close on click if propagation is stopped
    }
    this.setState({ popupVisible });
  }

  /**
  *  @param {event} evt - event from clicking delete button
  *  triggers DeleteLabbookFileMutation
  *  @return {}
  */
  _triggerDeleteMutation(evt) {
    const deleteFileData = {
      filePaths: [this.props.edge.node.key],
      edges: [this.props.edge],
    };

    this.props.mutations.deleteLabbookFiles(deleteFileData, (reponse) => {});

    this._togglePopup(evt, false);
  }

  /**
  *  @param {Object} node - Dom object to be assigned as a ref
  *  set wrapper ref
  *  @return {}
  */
  _setWrapperRef(node) {
    this[this.props.edge.node.id] = node;
  }

  /**
   *  @param {} node - Dom object to be assigned as a ref
   *  set wrapper ref
   *  @return {}
   */
  _downloadFile(isLocal) {
    UserIdentity.getUserIdentity().then((response) => {
      const isSessionValid = response.data && response.data.userIdentity && response.data.userIdentity.isSessionValid;

      if (!isLocal && !this.state.fileDownloading && !this.props.parentDownloading && isSessionValid) {
        const id = uuidv4;
        this.setState({ fileDownloading: true });
        const searchChildren = (parent) => {
          if (parent.children) {
            Object.keys(parent.children).forEach((childKey) => {
              if (parent.children[childKey].edge) {
                if (!parent.children[childKey].edge.node.isDir) {
                  let key = parent.children[childKey].edge.node.key;
                  if (this.props.section !== 'data') {
                    const splitKey = key.split('/');
                    key = splitKey.slice(1, splitKey.length).join('/');
                  }
                  keyArr.push(key);
                }
                searchChildren(parent.children[childKey]);
              }
            });
          }
        };

        let { key, owner, datasetName } = this.props.edge.node;
        const labbookOwner = store.getState().routes.owner;
        const labbookName = store.getState().routes.labbookName;
        const splitKey = key.split('/');

        if (this.props.section === 'data') {
          owner = labbookOwner;
          datasetName = labbookName;
        } else {
          key = splitKey.slice(1, splitKey.length).join('/');
        }

        const keyArr = this.props.edge.node.isDir ? [] : [key];
        if (this.props.folder && !this.props.isParent) {
          searchChildren(this.props.fullEdge);
        }
        let data;

        if (this.props.section === 'data') {
          data = {
            owner,
            datasetName,
          };
        } else {
          data = {
            owner,
            datasetName,
            labbookName,
            labbookOwner,
          };
        }
        data.successCall = () => {
          this.setState({ fileDownloading: false });
          if (this.props.setFolderIsDownloading) {
            this.props.setFolderIsDownloading(false);
          }
        };
        data.failureCall = () => {
          this.setState({ fileDownloading: false });
          if (this.props.setFolderIsDownloading) {
            this.props.setFolderIsDownloading(true);
          }
        };

        if (this.props.setFolderIsDownloading) {
          this.props.setFolderIsDownloading(true);
        }

        if (this.props.isParent) {
          data.allKeys = true;
        } else {
          data.allKeys = false;
          data.keys = keyArr;
        }

        const callback = (response, error) => {
          if (error) {
            this.setState({ fileDownloading: false });
          }
        };
        this.props.mutations.downloadDatasetFiles(data, callback);
      } else if (!isSessionValid) {
        this.setState({ showSessionValidMessage: true });

        setTimeout(() => { this.setState({ showSessionValidMessage: false }); }, 5000);
      }
    });
  }

  /**
  *  @param {boolean} isLocal
  *  set wrapper ref
  *  @return {}
  */
  _getTooltipText(isLocal) {
    const { props, state } = this;
    let downloadText = isLocal ? 'Downloaded' : 'Download';
    downloadText = props.folder && !isLocal ? 'Download Directory' : downloadText;
    downloadText = props.isParent ? 'Download All' : downloadText;
    downloadText = state.showSessionValidMessage ? 'A valid session is required to download a dataset file.' : downloadText;
    downloadText = props.isDragging && !isLocal ? 'File is not downloaded. Download file to move it.' : downloadText;

    return downloadText;
  }

  render() {
    const { props, state } = this;
    const { isLocal } = props;
    console.log(isLocal)
    const fileIsNotLocal = ((!props.edge.node.isLocal || (props.folder)) && !isLocal);
    const fileIsLocal = (props.edge.node.isLocal && isLocal) || (props.isParent && isLocal);
    const blockDownload = props.folder ? false : props.edge.node.isLocal || isLocal;
    const downloadText = this._getTooltipText(fileIsLocal);
    const isLoading = state.fileDownloading || ((props.parentDownloading || props.isDownloading) && !fileIsLocal);
    const showDownloadIcon = (props.section !== 'data') && !state.fileDownloading && !isLoading;
    const popupCSS = classNames({
      DatasetActionsMenu__popup: true,
      hidden: !state.popupVisible,
      Tooltip__message: true,
    });
    const downloadCSS = classNames({
      'DatasetActionsMenu__item Btn--round': true,
      'Tooltip-data Tooltip-data--small': !isLoading,
      'Tooltip-data--visible': state.showSessionValidMessage || (!props.isLocal && props.isDragging),
      'DatasetActionsMenu__item--download': fileIsNotLocal && showDownloadIcon,
      'DatasetActionsMenu__item--downloaded': fileIsLocal && showDownloadIcon,
      Btn__download: (fileIsNotLocal) && (props.section === 'data') && !state.fileDownloading && !isLoading,
      Btn__downloaded: fileIsLocal && (props.section === 'data') && !state.fileDownloading && !isLoading,
      'DatasetActionsMenu__item--loading': isLoading,
    });
    const unlinkCSS = classNames({
      'DatasetActionsMenu__item DatasetActionsMenu__item--unlink': true,
      'DatasetActionsMenu__popup-visible': state.popupVisible,
      'Tooltip-data Tooltip-data--small': !state.popupVisible,
    });

    return (

      <div
        className="DatasetActionsMenu"
        key={`${props.edge.node.id}-action-menu}`}
        ref={this._setWrapperRef}
      >
        {
            this.props.isParent
              && (
              <div
                className={unlinkCSS}
                data-tooltip="Unlink Dataset"
                onClick={(evt) => { this._togglePopup(evt, true); }}
              >

                <div className={popupCSS}>
                  <div className="Tooltip__pointer" />
                  <p>Are you sure?</p>
                  <div className="flex justify--space-around">
                    <button
                      className="File__btn--round File__btn--cancel"
                      onClick={(evt) => { this._togglePopup(evt, false); }}
                    />
                    <button
                      className="File__btn--round File__btn--add"
                      onClick={(evt) => { this._unlinkDataset(); }}
                    />
                  </div>
                </div>
              </div>
              )
          }
        <button
          onClick={() => this._downloadFile(fileIsLocal)}
          className={downloadCSS}
          data-tooltip={downloadText}
        />
      </div>
    );
  }
}

// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './AddSecret.scss';
// utils


export default class AddSecret extends Component {
  state = {
    file: null,
    path: '~/',
    error: null,
  }

  /**
  *  @param {}
  *  calls insert and upload file mutations
  *  @calls {props.secretsMutations.uploadSecret}
  */
  _uploadFile() {
    const { props, state } = this;
    const { file } = state;
    const insertData = {
      filename: file.name,
      mountPath: state.path,
    };
    const uploadData = {
      file,
      filename: file.name,
      component: this,
    };

    const callback = (response, error) => {
      if (response && response.insertSecretsEntry) {
        const newEdges = response.insertSecretsEntry.environment.secretsFileMapping.edges;
        const edge = newEdges.filter(({ node }) => node.filename === file.name)[0];
        uploadData.id = edge.node.id;
        props.secretsMutations.uploadSecret(uploadData);
        this.setState({
          file: null,
          error: null,
          path: '~/',
        });
      }
      if (error) {
        this.setState({ error: error[0].message });
      }
    };

    props.secretsMutations.insertSecret(insertData, callback);
  }

  /**
  *  @param {Obect} file
  * sets file in state
  */
  _setFile(files) {
    const file = (files && files[0]) ? files[0] : null;
    this.setState({
      file,
      error: null,
      path: '~/',
    });
    // need to reset value
    document.getElementById('add_secret').value = '';
  }

  /**
  *  @param {evt} Object
  * updates mount path
  */
  _updatePath(evt) {
    this.setState({ path: evt.target.value });
  }

  render() {
    const { state } = this;
    const displayedName = state.file ? state.file.name : '';
    const buttonCSS = classNames({
      'Btn Btn--allStyling Btn--noMargin': true,
      hidden: (state.file !== null),
    });
    const buttonText = state.file ? 'Change File' : 'Choose File';
    return (
      <div className="AddSecret">
        <div className="AddSecret__form flex justify--space-between">
          <div className="AddSecret__label-container flex flex--column justify--flex-start">
            <h6 className="AddSecrets__h6 AddSecrets__h6--width-120 relative">
              <b>Source File</b>
              <div
                className="Tooltip-data Tooltip-data--top-offset Tooltip-data--info"
                data-tooltip="Select file to upload into project container."
              />
            </h6>
            <label
              htmlFor="add_secret"
              className="AddSecret__label"
            >
              {displayedName}
              <div
                className={buttonCSS}
              >
                {buttonText}
              </div>
              <input
                id="add_secret"
                className="hidden"
                type="file"
                onChange={evt => this._setFile(evt.target.files)}
              />
            </label>
          </div>
          <div className="flex-1 flex flex--column justify--flex-start">
            <h6 className="AddSecrets__h6 AddSecrets__h6--width-190 relative">
              <b>Destination Directory</b>
              <div
                className="Tooltip-data Tooltip-data--top-offset Tooltip-data--info"
                data-tooltip="Enter the destination directory inside project container. `~/` is the home directory."
              />
            </h6>
            <input
              className="AddSecret__input"
              type="text"
              defaultValue="~/"
              onChange={evt => this._updatePath(evt)}
            />
          </div>
        </div>
        { state.file
          && (
          <div className="AddSecret__actions flex justify--right">
            { state.error
              && <p className="AddSecrets__paragraph AddSecrets__paragraph--error error">{state.error}</p>
            }
            <button
              type="button"
              className="Btn Btn--flat AddSecrets__btn"
              onClick={() => this._setFile(null)}
            >
              Cancel
            </button>
            <button
              disabled={state.file === null}
              type="button"
              className="Btn"
              onClick={() => this._uploadFile()}
            >
              Save
            </button>
          </div>
          )
        }
      </div>
    );
  }
}

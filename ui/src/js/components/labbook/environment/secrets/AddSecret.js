// vendor
import React, { Component } from 'react';
// components
// import Tooltip from 'Components/common/Tooltip';
// assets
import './AddSecret.scss';
// utils


export default class AddSecret extends Component {
  state = {
    file: null,
    path: '~/',
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

    const callback = (response) => {
      if (response && response.insertSecretsEntry) {
        const newEdges = response.insertSecretsEntry.environment.secretsFileMapping.edges;
        const edge = newEdges.filter(({ node }) => node.filename === file.name)[0];
        uploadData.id = edge.node.id;
        props.secretsMutations.uploadSecret(uploadData);
      }
    };

    props.secretsMutations.insertSecret(insertData, callback);
  }

  /**
  *  @param {Obect} file
  * sets file in state
  */
  _setFile(file) {
    this.setState({ file });
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
    const buttonText = state.file ? 'Change File' : 'Choose File';
    return (
      <div className="AddSecret">
        <div className="AddSecret__input flex justify--space-between">
          <div className="AddSecret__label-container flex flex--column justify--space-between">
            <b>Source File</b>
            <label
              htmlFor="add_secret"
              className="AddSecret__label"
            >
              {displayedName}
              <div
                className="Btn Btn--allStyling Btn--noMargin"
              >
                {buttonText}
              </div>
              <input
                id="add_secret"
                className="hidden"
                type="file"
                onChange={evt => this._setFile(evt.target.files[0])}
              />
            </label>
          </div>
          <div className="flex-1 flex flex--column justify--space-between">
            <b>Destination Path</b>
            <input
              type="text"
              defaultValue="~/"
              onChange={evt => this._updatePath(evt)}
            />
          </div>
        </div>
        {
          state.file
          && (
          <div className="AddSecret__actions flex justify--right">
            <button
              type="button"
              className="Btn Btn--flat"
              onClick={() => this._setFile(null)}
            >
              Cancel
            </button>
            <button
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

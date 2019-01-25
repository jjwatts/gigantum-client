import React, { Component } from 'react';
import classNames from 'classnames';
import { DragSource, DropTarget } from 'react-dnd';
import { NativeTypes } from 'react-dnd-html5-backend';
// assets
import './AddSubfolder.scss';
// components
import Connectors from './../utilities/Connectors';


class AddSubfolder extends Component {
  constructor(props) {
      super(props);

      this.state = {
        editMode: false,
        folderName: '',
      };

      this._clickedOffInput = this._clickedOffInput.bind(this);
  }
  componentDidMount() {
    window.addEventListener('click', this._clickedOffInput);
  }
  componentWillUnmount() {
    window.removeEventListener('click', this._clickedOffInput);
  }
  /*
    sets auto focus on visibility change
  */
  componentDidUpdate() {
    if (this.props.addFolderVisible) {
      this.subfolderInput.focus();
    }
  }

  /**
  *  @param {Object} evt
  *  clears state on click other subfolders
  *  @return {}
  */
  _clickedOffInput(evt) {
    if (!(evt.target.className.indexOf('AddSubfolder') > -1) && !(evt.target.className.indexOf('FileBrowser__button--add-folder') > -1) && (this.props.addFolderVisible || this.props.addFolderVisible === undefined)) {
      this._clearState();
      if (this.props.setAddFolderVisible) {
        this.props.setAddFolderVisible(false);
      }
    }
  }

  /**
  *  @param {string} key - key for the state object
  *  @param {boolean} value - value for key
  *  sets state on a boolean value
  *  @return {}
  */
  _updateStateBoolean(key, value) {
    this.setState({
      [key]: value,
    }, () => {
      this.subfolderInput.focus();
    });
  }

  /**
  *  @param {event}
  *  sets state on folderName
  *  triggers muation on enter
  *  triggers clear on escape
  *  @return {}
  */
  _updateFolderName(evt) {
    this.setState({
      folderName: evt.target.value,
    });

    if (evt.key === 'Enter') {
      this._triggerMutation();
    }

    if (evt.key === 'Escape') {
      this._clearState();
    }
  }

  /**
  *  @param {}
  *  sets state on a boolean value
  *  @return {}
  */
  _clearState() {
    this.setState({
      folderName: '',
      editMode: false,
    });

    if (this.subfolderInput) {
      this.subfolderInput.value = '';
    }
  }

  /**
  *  @param {}
  *  sets state on a boolean value
  *  @return {}
  */
  _clearInput() {
    this.setState({
      folderName: '',
    });

    this.subfolderInput.value = '';
  }

  /**
  *  @param {}
  *  trigger MakeLabbookDirectoryMutation
  *  @return {}
  */
  _triggerMutation() {
    const data = {
      key: this.props.folderKey + this.state.folderName,
    };

    this.props.mutations.makeLabbookDirectory(data, (response) => {
       this._clearState();
       if (this.props.setAddFolderVisible) {
        this.props.setAddFolderVisible(false);
       }
    });
  }

  render() {
    const subfolderInputCSS = classNames({
            AddSubfolder__edit: true,
            hidden: !this.state.editMode && !this.props.addFolderVisible,
          }),
          addFolderCSS = classNames({
            AddSubfolder: true,
            hidden: !this.props.addFolderVisible,
          }),
          subfolderTextCSS = classNames({
            AddSubfolder__text: true,
            hidden: (this.state.editMode) || this.props.addFolderVisible,
          });

    return (
      <div
          onClick={() => { this._updateStateBoolean('editMode', true); }}
          style={this.props.rowStyle}
          className={addFolderCSS}>
          <div className={subfolderTextCSS}>
            Add Folder
          </div>
           <div className={subfolderInputCSS}>
             <div className="AddSubfolder__container">
               <input
                 ref={(input) => { this.subfolderInput = input; }}
                 placeholder="Enter Folder Name"
                 type="text"
                 className="AddSubfolder__input"
                 onKeyUp={(evt) => { this._updateFolderName(evt); }}
               />
               { (this.state.folderName.length > 0) &&
                   <button
                     className="AddSubfolder__btn AddSubfolder__btn--clear"
                     onClick={() => { this._clearInput(); }}>
                     Clear
                   </button>
                 }
            </div>
            <div className="flex justify--space-around">
              <button
                className="File__btn--round File__btn--cancel"
                onClick={(evt) => { this._clearInput(); }} />
              <button
                className="File__btn--round File__btn--add"
                onClick={(evt) => { this._triggerMutation(); }}
              />
            </div>
          </div>
      </div>
    );
  }
}

export default AddSubfolder;

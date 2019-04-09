// vendor
import React, { Component } from 'react';
import Moment from 'moment';
import fileIconsJs from 'file-icons-js';
import classNames from 'classnames';
import { DragSource, DropTarget } from 'react-dnd';
import { NativeTypes } from 'react-dnd-html5-backend';
import TextTruncate from 'react-text-truncate';
// config
import config from 'JS/config';
// components
import ActionsMenu from './DatasetActionsMenu';
// assets
import './DatasetFile.scss';

class File extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isSelected: (props.isSelected || this.props.childrenState[this.props.fileData.edge.node.key].isSelected) || false,
      stateSwitch: false,
    };
    this._setSelected = this._setSelected.bind(this);
  }

  static getDerivedStateFromProps(nextProps, state) {
    const isSelected = (nextProps.multiSelect === 'all')
      ? true
      : (nextProps.multiSelect === 'none')
        ? false
        : state.isSelected;

    if ((nextProps.isOverCurrent !== nextProps.isOverChildFile) && !nextProps.isDragging && state.hover) {
      nextProps.updateParentDropZone(nextProps.isOverCurrent);
    }
    return {
      ...state,
      isSelected,
    };
  }

  componentDidUpdate(prevProps, prevState, snapshot) {
    if (this.state.renameEditMode) {
      this.reanmeInput.focus();
    }
  }

  /**
  *  @param {boolean} isSelected - sets if file has been selected
  *  sets elements to be selected and parent
  */
  _setSelected(isSelected) {
    this.props.updateChildState(this.props.fileData.edge.node.key, isSelected, false);
    this.setState({ isSelected }, () => {
      Object.keys(this.refs).forEach((ref) => {
        this.refs[ref]._setSelected();
      });
      if (this.props.checkParent) {
        this.props.checkParent();
      }
    });
  }

  render() {
    const { props, state } = this;
    const { node } = props.fileData.edge;
    const { index } = props.fileData;
    const fileName = props.filename;
    const fileRowCSS = classNames({
      File__row: true,
      'File__row--hover': state.hover,
      'File__row--background': props.isDragging,
    });


    const buttonCSS = classNames({
      'Btn Btn--round Btn--medium': true,
      Btn__uncheck: !state.isSelected,
      Btn__check: state.isSelected,
    });


    const textIconsCSS = classNames({
      'File__cell File__cell--name': true,
      hidden: state.renameEditMode,
    });


    const paddingLeft = 40 * index;


    const rowStyle = { paddingLeft: `${paddingLeft}px` };
    return (
      <div
        style={props.style}
        className="File"
      >

        <div
          className={fileRowCSS}
          style={rowStyle}
        >

          <div className={textIconsCSS}>

            <div className={`File__icon ${fileIconsJs.getClass(fileName)}`} />

            <div className="File__text">
              {
                    this.props.expanded
                    && (
                    <TextTruncate
                      className="File__paragragh"
                      line={1}
                      truncateText="…"
                      text={fileName}
                    />
                    )
                  }
            </div>

          </div>

          <div className="File__cell File__cell--size">
            {config.humanFileSize(node.size)}
          </div>

          <div className="File__cell File__cell--date">
            {Moment((node.modifiedAt * 1000), 'x').fromNow()}
          </div>

          <div className="File__cell File__cell--menu">
            <ActionsMenu
              edge={props.fileData.edge}
              mutationData={props.mutationData}
              mutations={props.mutations}
              renameEditMode={this._renameEditMode}
              isDownloading={props.isDownloading}
            />
          </div>
        </div>
      </div>
    );
  }
}


export default File;

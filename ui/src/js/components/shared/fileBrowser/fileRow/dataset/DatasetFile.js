// vendor
import React, { Component } from 'react';
import Moment from 'moment';
import fileIconsJs from 'file-icons-js';
import classNames from 'classnames';
import { DragSource, DropTarget } from 'react-dnd';
import { NativeTypes } from 'react-dnd-html5-backend';
import TextTruncate from 'react-text-truncate';
// components
import ActionsMenu from './DatasetActionsMenu';
// config
import config from 'JS/config';
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
    let isSelected = (nextProps.multiSelect === 'all')
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
    const { node } = this.props.fileData.edge;
    const { index } = this.props.fileData;
    const fileName = this.props.filename;
    const fileRowCSS = classNames({
            File__row: true,
            'File__row--hover': this.state.hover,
            'File__row--background': this.props.isDragging,
          }),
          buttonCSS = classNames({
            'Btn Btn--round': true,
            'Btn--uncheck': !this.state.isSelected,
            'Btn--check': this.state.isSelected,
          }),
          textIconsCSS = classNames({
            'File__cell File__cell--name': true,
            hidden: this.state.renameEditMode,
          }),
          paddingLeft = 40 * index,
          rowStyle = { paddingLeft: `${paddingLeft}px` };
    return (<div
      style={this.props.style}
      className="File">

             <div
               className={fileRowCSS}
               style={rowStyle}>

                <div className={textIconsCSS}>

                  <div className={`File__icon ${fileIconsJs.getClass(fileName)}`}></div>

                  <div className="File__text">
                  {
                    this.props.expanded &&
                    <TextTruncate
                      className="File__paragragh"
                      line={1}
                      truncateText="…"
                      text={fileName}
                    />
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
                    edge={this.props.fileData.edge}
                    mutationData={this.props.mutationData}
                    mutations={this.props.mutations}
                    renameEditMode={ this._renameEditMode }
                  />
                </div>

            </div>
        </div>);
  }
}


export default File;

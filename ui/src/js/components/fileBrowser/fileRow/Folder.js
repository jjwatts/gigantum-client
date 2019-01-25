// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import Moment from 'moment';
import { DragSource, DropTarget } from 'react-dnd';
import { NativeTypes } from 'react-dnd-html5-backend';
// assets
import './Folder.scss';
// components
import ActionsMenu from './ActionsMenu';
import File from './File';
import AddSubfolder from './AddSubfolder';
import DatasetActionsMenu from './dataset/DatasetActionsMenu';
// components
import Connectors from './../utilities/Connectors';


class Folder extends Component {
    constructor(props) {
        super(props);

        this.state = {
            isDragging: props.isDragging,
            expanded: this.props.childrenState[this.props.fileData.edge.node.key].isExpanded || false,
            isSelected: (props.isSelected || this.props.childrenState[this.props.fileData.edge.node.key].isSelected) || false,
            isIncomplete: this.props.childrenState[this.props.fileData.edge.node.key].isIncomplete || false,
            hoverId: '',
            isOver: false,
            prevIsOverState: false,
            addFolderVisible: this.props.childrenState[this.props.fileData.edge.node.key].isAddingFolder || false,
            renameEditMode: false,
            isOverChildFile: false,
            renameValue: props.filename,
        };

        this._setSelected = this._setSelected.bind(this);
        this._setIncomplete = this._setIncomplete.bind(this);
        this._checkParent = this._checkParent.bind(this);
        this._checkRefs = this._checkRefs.bind(this);
        this._setState = this._setState.bind(this);
        this._setHoverState = this._setHoverState.bind(this);
        this._addFolderVisible = this._addFolderVisible.bind(this);
        this._mouseLeave = this._mouseLeave.bind(this);
        this._checkHover = this._checkHover.bind(this);
        this._renameEditMode = this._renameEditMode.bind(this);
        this._updateDropZone = this._updateDropZone.bind(this);
    }


    static getDerivedStateFromProps(nextProps, state) {
      let isSelected = (nextProps.multiSelect === 'all')
        ? true
        : (nextProps.multiSelect === 'none')
        ? false
        : state.isSelected;
        let isIncomplete = (nextProps.multiSelect === 'none') ? false : state.isIncomplete;
      return {
        ...state,
        isOver: nextProps.isOver,
        prevIsOverState: state.isOver,
        isSelected,
        isIncomplete,

      };
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
      if (this.state.renameEditMode) {
             this.reanmeInput.focus();
        }
    }

    /**
    *  @param {string} key
    *  @param {string || boolean} value - updates key value in state
    *  update state of component for a given key value pair
    *  @return {}
    */
    _setState(key, value) {
       this.setState({ [key]: value });
    }
    /**
    *  @param {boolean} isSelected
    *  sets child elements to be selected and current folder item
    *  @return {}
    */
    _setSelected(isSelected) {
        this.props.updateChildState(this.props.fileData.edge.node.key, isSelected, false, this.state.expanded, this.state.addFolderVisible);
        this.setState(
          {
            isSelected,
            isIncomplete: false,
          },
          () => {
              Object.keys(this.refs).forEach((ref) => {
                    const folder = this.refs[ref];

                    if (folder._setSelected) {
                      folder._setSelected(isSelected);
                    } else if (folder.getDecoratedComponentInstance && folder.getDecoratedComponentInstance().getDecoratedComponentInstance) {
                      folder.getDecoratedComponentInstance().getDecoratedComponentInstance()._setSelected(isSelected);
                    } else {
                      folder.getDecoratedComponentInstance()._setSelected(isSelected);
                    }
              });
              if (this.props.checkParent) {
                  this.props.checkParent();
              }
          },
        );
    }

    /**
    *  @param {}
    *  sets parents element to selected if count matches child length
    *  @return {}
    */
    _setIncomplete() {
        this.setState({
          isIncomplete: true,
          isSelected: false,
        });
    }

    /**
    *  @param {}
    *  checks parent item
    *  @return {}
    */
    _checkParent() {
        let checkCount = 0;
        let incompleteCount = 0;
        Object.keys(this.refs).forEach((ref) => {
            let state = (this.refs[ref] && this.refs[ref].getDecoratedComponentInstance && this.refs[ref].getDecoratedComponentInstance().getDecoratedComponentInstance) ? this.refs[ref].getDecoratedComponentInstance().getDecoratedComponentInstance().state : this.refs[ref].getDecoratedComponentInstance().state;
            if (state.isSelected) {
                checkCount += 1;
            }
            if (state.isIncomplete) {
              incompleteCount += 1;
            }
        });

        if (checkCount === 0 && incompleteCount === 0) {
            this.props.updateChildState(this.props.fileData.edge.node.key, false, false, this.state.expanded, this.state.addFolderVisible);
            this.setState(
              {
                isIncomplete: false,
                isSelected: false,
              },
              () => {
                if (this.props.checkParent) {
                   this.props.checkParent();
                }
              },
            );
        } else if (checkCount === Object.keys(this.refs).length && this.state.isSelected) {
            this.props.updateChildState(this.props.fileData.edge.node.key, true, false, this.state.expanded, this.state.addFolderVisible);
            this.setState(
              {
                isIncomplete: false,
                isSelected: true,
              },
              () => {
                if (this.props.checkParent) {
                    this.props.checkParent();
                }
              },
            );
        } else {
            this.props.updateChildState(this.props.fileData.edge.node.key, false, true, this.state.expanded, this.state.addFolderVisible);
            this.setState(
              {
                isIncomplete: true,
                isSelected: false,
              },
              () => {
                if (this.props.setIncomplete) {
                    this.props.setIncomplete();
                }
              },
          );
        }
    }

    /**
    *  @param {Object} evt
    *  sets item to expanded
    *  @return {}
    */
    _expandSection(evt) {
      if (!evt.target.classList.contains('Folder__btn') && !evt.target.classList.contains('ActionsMenu__item') && !evt.target.classList.contains('Btn--round') &&
      !evt.target.classList.contains('File__btn--round')) {
        this.setState({ expanded: !this.state.expanded }, () => {
          this.props.updateChildState(this.props.fileData.edge.node.key, this.state.isSelected, this.state.isIncomplete, this.state.expanded, this.state.addFolderVisible);
          // this.props.listRef.recomputeGridSize()
        });
      }
      if (evt.target.classList.contains('ActionsMenu__item--AddSubfolder')) {
        this.setState({ expanded: true }, () => {
          this.props.updateChildState(this.props.fileData.edge.node.key, this.state.isSelected, this.state.isIncomplete, this.state.expanded, this.state.addFolderVisible);
          // this.props.listRef.recomputeGridSize()
        });
      }
    }

    /**
    *  @param {jsx} render
    *  sets elements to be selected and parent
    */
    connectDND(render) {
      if (this.state.isDragging || this.props.parentIsDragged) {
        render = this.props.connectDragSource(render);
      } else {
        render = this.props.connectDropTarget(render);
      }

      return render;
    }
    /**
    *  @param {}
    *  sets dragging state
    */
    _mouseEnter() {
      if (this.props.setParentDragFalse) {
        this.props.setParentDragFalse();
      }
      this.setState({ isDragging: true, isHovered: true });
    }

    /**
    *  @param {}
    *  sets dragging state
    *  @return {}
    */
    _mouseLeave() {
      if (this.props.setParentDragTrue) {
        this.props.setParentDragTrue();
      }
      this.setState({ isDragging: false, isHovered: false });
    }
    /**
    *  @param {}
    *  sets dragging state to true
    *  @return {}
    */
    _checkHover() {
      if (this.state.isHovered && !this.state.isDragging) {
        this.setState({ isDragging: true });
      }
    }
    /**
      *  @param {}
      *  sets addFolderVisible state
      *  @return {}
    */
    _addFolderVisible(reverse) {
      if (reverse) {
        this.props.updateChildState(this.props.fileData.edge.node.key, this.state.isSelected, this.state.isIncomplete, this.state.expanded, !this.state.addFolderVisible);

        this.setState({ addFolderVisible: !this.state.addFolderVisible });
      } else {
        this.props.updateChildState(this.props.fileData.edge.node.key, this.state.isSelected, this.state.isIncomplete, this.state.expanded, false);
        this.setState({ addFolderVisible: false });
      }
    }
    /**
    *  @param {}
    *  checks if folder refs has props.isOver === true
    *  @return {boolean}
    */
    _checkRefs() {
      let isOver = this.props.isOverCurrent || this.props.isOver, // this.state.isOverChildFile,
          { refs } = this;

      Object.keys(refs).forEach((childname) => {
        if (refs[childname].getDecoratedComponentInstance && refs[childname].getDecoratedComponentInstance() && refs[childname].getDecoratedComponentInstance().getDecoratedComponentInstance && refs[childname].getDecoratedComponentInstance().getDecoratedComponentInstance()) {
          const child = refs[childname].getDecoratedComponentInstance().getDecoratedComponentInstance();
          if (child.props.fileData && !child.props.fileData.edge.node.isDir) {
            if (child.props.isOverCurrent) {
              isOver = true;
            }
          }
        }
      });

      return (isOver);
    }

    /**
    *  @param {event}
    *  @param {boolean} hover - boolean that sets if the component should show a hover state
    *  sets hover state
    *  @return {}
    */
    _setHoverState(evt, hover) {
      evt.preventDefault();
      evt.stopPropagation();
      this.setState({ hover });

      if (this.props.setParentHoverState && hover) {
        let fakeEvent = {
          preventDefault: () => {},
          stopPropagation: () => {},
        };
        this.props.setParentHoverState(fakeEvent, false);
      }
    }
    /**
    *  @param {event}
    *  sets dragging state
    *  @return {}
    */
    _updateFileName(evt) {
      this.setState({
        renameValue: evt.target.value,
      });
    }
    /**
    *  @param {event}
    *  sumbit or clear
    *  @return {}
    */
    _submitCancel(evt) {
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
        renameValue: this.props.filename,
        renameEditMode: false,
      });
    }

    /**
    *  @param {}
    *  sets state on a boolean value
    *  @return {}
    */
    _triggerMutation() {
      let fileKeyArray = this.props.fileData.edge.node.key.split('/');
      fileKeyArray.pop();
      fileKeyArray.pop();
      let folderKeyArray = fileKeyArray;
      let folderKey = folderKeyArray.join('/');

      let removeIds = [this.props.fileData.edge.node.id];
      let currentHead = this.props.fileData;

      const searchChildren = (parent) => {
        if (parent.children) {
          Object.keys(parent.children).forEach((childKey) => {
            if (parent.children[childKey].edge) {
              removeIds.push(parent.children[childKey].edge.node.id);
              searchChildren(parent.children[childKey]);
            }
          });
        }
      };

      searchChildren(currentHead);

      const data = {
        newKey: folderKey === '' ? `${this.state.renameValue}/` : `${folderKey}/${this.state.renameValue}/`,
        edge: this.props.fileData.edge,
        removeIds,
      };
      if (this.props.section !== 'data') {
        this.props.mutations.moveLabbookFile(data, (response) => {
          this._clearState();
       });
      } else {
        this.props.mutations.moveDatasetFile(data, (response) => {
          this._clearState();
       });
      }
    }
    /**
    *  @param {boolean} renameEditMode -sets
    *  sets hover state
    *  @return {}
    */
    _renameEditMode(renameEditMode) {
      this.setState({ renameEditMode });
    }

    /**
    *  @param {boolean} isOverChildFile
    *  update state to update drop zone
    *  @return {}
    */
    _updateDropZone(isOverChildFile) {
      this.setState({ isOverChildFile });
    }
    /**
    *  @param {Array} array
    *  @param {String} type
    *  @param {Boolean} reverse
    *  @param {Object} children
    *  @param {String} section
    *  returns sorted children
    *  @return {}
    */
    _childSort(array, type, reverse, children, section) {
      array.sort((a, b) => {
        let lowerA,
        lowerB;
        if (type === 'az' || type === 'size' && section === 'folder') {
          lowerA = a.toLowerCase();
          lowerB = b.toLowerCase();
          if (type === 'size' || !reverse) {
            return (lowerA < lowerB) ? -1 : (lowerA > lowerB) ? 1 : 0;
          }
          return (lowerA < lowerB) ? 1 : (lowerA > lowerB) ? -1 : 0;
        } else if (type === 'modified') {
          lowerA = children[a].edge.node.modifiedAt;
          lowerB = children[b].edge.node.modifiedAt;
          return reverse ? lowerB - lowerA : lowerA - lowerB;
        } else if (type === 'size') {
          lowerA = children[a].edge.node.size;
          lowerB = children[b].edge.node.size;
          return reverse ? lowerB - lowerA : lowerA - lowerB;
        }
        return 0;
      });
      return array;
    }

    render() {
        const { node } = this.props.fileData.edge,
              { children, index } = this.props.fileData,
              { isOver } = this.props,
              splitKey = node.key.split('/'),
              folderName = this.props.filename,
              folderRowCSS = classNames({
                Folder__row: true,
                'Folder__row--expanded': this.state.expanded,
                'Folder__row--hover': this.state.hover,
              }),
              buttonCSS = classNames({
                'Btn Btn--round': true,
                'Btn--uncheck': !this.state.isSelected && !this.state.isIncomplete,
                'Btn--check': this.state.isSelected && !this.state.isIncomplete,
                'Btn--partial': this.state.isIncomplete,
              }),

              folderChildCSS = classNames({
                Folder__child: true,
                hidden: !this.state.expanded,
              }),

              folderNameCSS = classNames({
                'Folder__cell Folder__cell--name': true,
                'Folder__cell--open': this.state.expanded,
                hidden: this.state.renameEditMode,
              }),

              folderCSS = classNames({
                Folder: true,
                'Folder--highlight': isOver,
                'Folder--background': this.props.isDragging,
              }),
              renameCSS = classNames({
                'File__cell File__cell--edit': true,
                hidden: !this.state.renameEditMode,
              }),
              paddingLeft = 40 * index,
              rowStyle = { paddingLeft: `${paddingLeft}px` },
              addRowStyle = {
                paddingLeft: `${paddingLeft + 120}px`,
                backgroundPositionX: `${99 + paddingLeft}px`,
              };
        let folderKeys = children && Object.keys(children).filter(child => children[child].edge && children[child].edge.node.isDir) || [];
        folderKeys = this._childSort(folderKeys, this.props.sort, this.props.reverse, children, 'folder');
        let fileKeys = children && Object.keys(children).filter(child => children[child].edge && !children[child].edge.node.isDir) || [];
        fileKeys = this._childSort(fileKeys, this.props.sort, this.props.reverse, children, 'files');
        let childrenKeys = folderKeys.concat(fileKeys);

        let folder = // this.props.connectDragPreview(
          <div
          onMouseOver={(evt) => { this._setHoverState(evt, true); }}
          onMouseOut={(evt) => { this._setHoverState(evt, false); }}
          onMouseLeave={() => { this._mouseLeave(); }}
          onMouseEnter={() => { this._mouseEnter(); }}
          style={this.props.style}
          className={ folderCSS }>
                <div
                    className={folderRowCSS}
                    style={rowStyle}
                    onClick={evt => this._expandSection(evt)}>
                    <button
                        className={buttonCSS}
                        onClick={() => this._setSelected(!this.state.isSelected)}>
                    </button>
                    <div className={folderNameCSS}>
                      <div className="Folder__icon">
                      </div>
                      <div className="Folder__name">
                          {folderName}
                      </div>
                    </div>
                    <div className={renameCSS}>

                      <div className="File__container">
                        <input
                          draggable
                          ref={(input) => { this.reanmeInput = input; }}
                          placeholder="Rename File"
                          type="text"
                          className="File__input"
                          value={this.state.renameValue}
                          onDragStart={(evt) => { evt.preventDefault(); evt.stopPropagation(); }}
                          onChange={(evt) => { this._updateFileName(evt); }}
                          onKeyDown={(evt) => { this._submitCancel(evt); }}
                        />
                      </div>
                      <div className="flex justify-space-around">
                        <button
                          className="File__btn--round File__btn--cancel File__input--rename-cancel"
                          onClick={() => { this._clearState(); }} />
                        <button
                          className="File__btn--round File__btn--add File__input--rename-add"
                          onClick={() => { this._triggerMutation(); }}
                        />
                      </div>
                    </div>
                    <div className="Folder__cell Folder__cell--size">

                    </div>
                    <div className="Folder__cell Folder__cell--date">
                        {Moment((node.modifiedAt * 1000), 'x').fromNow()}
                    </div>
                    <div className="Folder__cell Folder__cell--menu">
                      <ActionsMenu
                          edge={this.props.fileData.edge}
                          mutationData={this.props.mutationData}
                          mutations={this.props.mutations}
                          addFolderVisible={this._addFolderVisible}
                          fileData={this.props.fileData}
                          section={this.props.section}
                          folder
                          renameEditMode={ this._renameEditMode}
                        />
                    {
                      this.props.section === 'data' &&
                        <DatasetActionsMenu
                        edge={this.props.fileData.edge}
                        mutationData={this.props.mutationData}
                        mutations={this.props.mutations}
                        addFolderVisible={this._addFolderVisible}
                        fileData={this.props.fileData}
                        folder
                        renameEditMode={ this._renameEditMode}
                        section={this.props.section}
                        fullEdge={this.props.fileData}
                      />
                    }
                    </div>
                </div>
                <div className={folderChildCSS}>
                {
                  this.state.expanded &&
                    <AddSubfolder
                      rowStyle={addRowStyle}
                      key={`${node.key}__subfolder`}
                      folderKey={node.key}
                      mutationData={this.props.mutationData}
                      mutations={this.props.mutations}
                      setAddFolderVisible={this._addFolderVisible}
                      addFolderVisible={this.state.addFolderVisible}
                    />
                }
                  {
                    this.state.expanded &&
                      childrenKeys.map((file, index) => {
                          if ((children && children[file] && children[file].edge && children[file].edge.node.isDir)) {
                              return (
                                  <FolderDND
                                      filename={file}
                                      index={index}
                                      key={children[file].edge.node.key}
                                      ref={children[file].edge.node.key}
                                      mutations={this.props.mutations}
                                      mutationData={this.props.mutationData}
                                      fileData={children[file]}
                                      isSelected={this.state.isSelected}
                                      multiSelect={this.props.multiSelect}
                                      setIncomplete={this._setIncomplete}
                                      checkParent={this._checkParent}
                                      setState={this._setState}
                                      setParentHoverState={this._setHoverState}
                                      expanded={this.state.expanded}
                                      setParentDragFalse={() => this.setState({ isDragging: false })}
                                      setParentDragTrue={this._checkHover}
                                      parentIsDragged={this.state.isDragging || this.props.parentIsDragged}
                                      childrenState={this.props.childrenState}
                                      listRef={this.props.listRef}
                                      updateChildState={this.props.updateChildState}
                                      section={this.props.section}
                                      codeDirUpload={this.props.codeDirUpload}>
                                  </FolderDND>
                              );
                          } else if ((children && children[file] && children[file].edge && !children[file].edge.node.isDir)) {
                            return (
                                <File
                                    filename={file}
                                    mutations={this.props.mutations}
                                    mutationData={this.props.mutationData}
                                    ref={children[file].edge.node.key}
                                    fileData={children[file]}
                                    key={children[file].edge.node.key}
                                    isSelected={this.state.isSelected}
                                    multiSelect={this.props.multiSelect}
                                    checkParent={this._checkParent}
                                    section={this.props.section}
                                    expanded={this.state.expanded}
                                    setParentHoverState={this._setHoverState}
                                    setParentDragFalse={(() => this.setState({ isDragging: false }))}
                                    setParentDragTrue={this._checkHover}
                                    isOverChildFile={this.state.isOverChildFile}
                                    updateParentDropZone={this._updateDropZone}
                                    childrenState={this.props.childrenState}
                                    updateChildState={this.props.updateChildState}>
                                </File>
                            );
                          } else if (children[file]) {
                            return (
                              <div
                                key={file + index}
                              />
                              );
                          }
                          return (
                            <div
                                key={file + index}
                            >
                              Loading
                            </div>
                            );
                      })
                  }
                </div>
            </div>;

        return (
          this.connectDND(folder)
        );
    }
}

const FolderDND = DragSource(
  'card',
  Connectors.dragSource,
  Connectors.dragCollect,
)(DropTarget(
    ['card', NativeTypes.FILE],
    Connectors.targetSource,
    Connectors.targetCollect,
  )(Folder));


export default FolderDND;

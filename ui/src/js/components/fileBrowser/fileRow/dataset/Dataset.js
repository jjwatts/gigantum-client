// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import Moment from 'moment';
import uuidv4 from 'uuid/v4';
// components
import ActionsMenu from './DatasetActionsMenu';
import File from './DatasetFile';
import Folder from './DatasetFolder';
// assets
import './Dataset.scss';


class Dataset extends Component {
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
        };

        this._setSelected = this._setSelected.bind(this);
        this._setIncomplete = this._setIncomplete.bind(this);
        this._checkParent = this._checkParent.bind(this);
        this._setState = this._setState.bind(this);
        this._addFolderVisible = this._addFolderVisible.bind(this);
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
            let state = (this.refs[ref] && this.refs[ref].state);
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
      if (!evt.target.classList.contains('Folder__btn') && !evt.target.classList.contains('ActionsMenu__item') && !evt.target.classList.contains('Btn--round') && !evt.target.classList.contains('DatasetActionsMenu__item') &&
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
        newKey: folderKey === '' ? `${this.state.newFolderName}/` : `${folderKey}/${this.state.newFolderName}/`,
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
              datasetName = this.props.filename,
              datasetRowCSS = classNames({
                DatasetBrowser__row: true,
                'DatasetBrowser__row--expanded': this.state.expanded,
                'DatasetBrowser__row--hover': this.state.hover,
              }),
              buttonCSS = classNames({
                'Btn Btn--round': true,
                'Btn--uncheck': !this.state.isSelected && !this.state.isIncomplete,
                'Btn--check': this.state.isSelected && !this.state.isIncomplete,
                'Btn--partial': this.state.isIncomplete,
              }),
              datasetChildCSS = classNames({
                Folder__child: true,
                hidden: !this.state.expanded,
              }),
              datasetNameCSS = classNames({
                'DatasetBrowser__cell DatasetBrowser__cell--name': true,
                'DatasetBrowser__cell--open': this.state.expanded,
                hidden: this.state.renameEditMode,
              }),
              datasetCSS = classNames({
                DatasetBrowser: true,
                'DatasetBrowser--highlight': isOver,
                'DatasetBrowser--background': this.props.isDragging,
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

        return (<div
          style={this.props.style}
          className={ datasetCSS }>
                <div
                    className={datasetRowCSS}
                    style={rowStyle}
                    onClick={evt => this._expandSection(evt)}>
                    <div className={datasetNameCSS}>
                      <div className="DatasetBrowser__icon">
                      </div>
                      <div className="DatasetBrowser__name">
                          {datasetName}
                      </div>
                    </div>
                    <div className="DatasetBrowser__cell DatasetBrowser__cell--size">

                    </div>
                    <div className="DatasetBrowser__cell DatasetBrowser__cell--date">
                        {Moment((node.modifiedAt * 1000), 'x').fromNow()}
                    </div>
                    <div className="DatasetBrowser__cell DatasetBrowser__cell--menu">
                      <ActionsMenu
                        edge={this.props.fileData.edge}
                        mutationData={this.props.mutationData}
                        mutations={this.props.mutations}
                        addFolderVisible={this._addFolderVisible}
                        folder
                        renameEditMode={ this._renameEditMode}
                        fullEdge={this.props.fileData}
                        isParent
                      />
                    </div>
                </div>
                <div className={datasetChildCSS}>
                  {
                    this.state.expanded &&
                      childrenKeys.map((file, index) => {
                          if ((children && children[file] && children[file].edge && children[file].edge.node.isDir)) {
                              return (
                                  <Folder
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
                                      codeDirUpload={this.props.codeDirUpload}>
                                  </Folder>
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
            </div>);
    }
}


export default Dataset;

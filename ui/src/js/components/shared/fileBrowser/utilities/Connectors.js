import React from 'react';
import { DragSource } from 'react-dnd';
import uuidv4 from 'uuid/v4';
// store
import store from 'JS/redux/store';
// config
import config from 'JS/config';
// utilities
import FileBrowserMutations from './FileBrowserMutations';
import CreateFiles from './CreateFiles';


/**
* @param {Array:[Object]} files
* @param {String} promptType
*
* @return {number} totalFiles
*/
const checkFileSize = (files, promptType) => {
  const tenMB = 10 * 1000 * 1000;
  const oneHundredMB = 100 * 1000 * 1000;
  const fiveHundredMB = oneHundredMB * 5;
  const fiveGigs = oneHundredMB * 50;
  const fileSizePrompt = [];
  const fileSizeNotAllowed = [];

  function filesRecursionCount(file) {
    if (Array.isArray(file)) {
      file.forEach((nestedFile) => {
        filesRecursionCount(nestedFile);
      });
    } else if (file.file && Array.isArray(file.file) && (file.file.length > 0)) {
      file.file.forEach((nestedFile) => {
        filesRecursionCount(nestedFile);
      });
    } else {
      const extension = file.name ? file.name.replace(/.*\./, '') : file.entry.fullPath.replace(/.*\./, '');
      if ((config.fileBrowser.excludedFiles.indexOf(extension) < 0) && ((file.entry && file.entry.isFile) || (typeof file.type === 'string'))) {
        if (promptType === 'code') {
          if (file.size > oneHundredMB) {
            fileSizeNotAllowed.push(file);
          }

          if ((file.size > tenMB) && (file.size < oneHundredMB)) {
            fileSizePrompt.push(file);
          }
        } else if ((promptType === 'output') || (promptType === 'input')) {
          if (file.size > fiveHundredMB) {
            fileSizeNotAllowed.push(file);
          }

          if ((file.size > oneHundredMB) && (file.size < fiveHundredMB)) {
            fileSizePrompt.push(file);
          }
        } else if (file.size > fiveGigs) {
          fileSizeNotAllowed.push(file);
        }
      }
    }
  }
  filesRecursionCount(files);
  return { fileSizeNotAllowed, fileSizePrompt };
};

const dragSource = {

  canDrag(props) {
    // You can disallow drag based on props
    return true;
  },

  isDragging(props, monitor) {
    return monitor.getItem().key === props.key;
  },

  beginDrag(props, monitor) {

    return {
      isDragging: true,
      fileData: props.fileData,
      isLocal: props.isLocal,
      section: props.section,
    };
  },

  endDrag(props, monitor, component) {
    if (!monitor.didDrop()) {
      return;
    }

    const dropResult = monitor.getDropResult();
    const fileNameParts = props.fileData.edge.node.key.split('/');
    const fileName = fileNameParts[fileNameParts.length - 1];

    if (dropResult.fileData && !((props.section === 'data') && !dropResult.isLocal)) {
      const pathArray = dropResult.fileData.edge.node.key.split('/');
      // remove filename or empty string
      pathArray.pop();
      const path = pathArray.join('/');
      const newKey = path ? `${path}/${fileName}` : `${fileName}`;
      const newKeyArray = dropResult.fileData.edge.node.key.split('/');
      const fileKeyArray = props.fileData.edge.node.key.split('/');

      newKeyArray.pop();
      fileKeyArray.pop();

      let newKeyPath = newKeyArray.join('/');
      const fileKeyPath = fileKeyArray.join('/');
      newKeyPath = newKeyPath.replace(/\/\/\/g/, '/');
      const trimmedFilePath = (fileKeyPath + (fileName.length ? `/${fileName}` : '')).split('/').slice(0, -1).join('/');

      if ((newKeyPath !== fileKeyPath) && (trimmedFilePath !== newKeyPath)) {
        if (newKey !== props.fileData.edge.node.key) {
          const removeIds = [props.fileData.edge.node.id];
          const currentHead = props.fileData;
          // check if folder has children and push id into array to removed by optomistic updater
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
          const moveLabbookFileData = {
            newKey,
            edge: props.fileData.edge,
            removeIds,
          };

          if (props.mutations) {
            if (props.section !== 'data') {
              props.mutations.moveLabbookFile(moveLabbookFileData, (response) => {});
            } else {
              props.mutations.moveDatasetFile(moveLabbookFileData, (response) => {});
            }
          } else {
            const {
              parentId,
              connection,
              favoriteConnection,
              section,
            } = props;
            const { owner, labbookName } = store.getState().routes;

            const mutationData = {
              owner,
              labbookName,
              parentId,
              connection,
              favoriteConnection,
              section,
            };

            const mutations = new FileBrowserMutations(mutationData);
            if (section !== 'data') {
              mutations.moveLabbookFile(moveLabbookFileData, (response) => {});
            } else {
              mutations.moveLDatasetFile(moveLabbookFileData, (response) => {});
            }
          }
        }
      }
    }
  },
};

function dragCollect(connect, monitor) {
  return {
    connectDragPreview: connect.dragPreview(),
    connectDragSource: connect.dragSource(),
    isDragging: monitor.sourceId === monitor.getSourceId(),
  };
}

const uploadDirContent = (dndItem, props, mutationData, fileSizeData) => {
  let path;
  dndItem.dirContent.then((fileList) => {
    if (fileList.length) {
      const key = props.fileData ? props.fileData.edge.node.key : props.fileKey ? props.fileKey : '';
      path = key === '' ? '' : key.substr(0, key.lastIndexOf('/') || key.length);

      CreateFiles.createFiles(fileList.flat(), `${path}/`, mutationData, props, fileSizeData);
    } else if (dndItem.files && dndItem.files.length) {
      // handle dragged files
      const key = props.newKey || props.fileKey;
      path = key.substr(0, key.lastIndexOf('/') || key.length);
      const item = monitor.getItem();

      if (item && item.files && props.browserProps.createFiles) {
        CreateFiles.createFiles(item.files, `${path}/`, mutationData, props, fileSizeData);
      }
      newPath = null;
      fileKey = null;
    }
  });
};

const targetSource = {
  canDrop(props, monitor) {
    const item = monitor.getItem()
    const { uploading } = store.getState().fileBrowser;
    const mouseoverAllowed = !uploading && !(props.section === 'data' && !item.isLocal);
    return monitor.isOver({ shallow: true }) && mouseoverAllowed;
  },
  drop(props, monitor, component, comp) {
    // TODO: clean up this code, some of this logic is being duplicated. make better use of functions
    const dndItem = monitor.getItem();
    const promptType = props.section ? props.section : ((props.mutationData) && (props.mutationData.section)) ? props.mutationData.section : '';
    let newPath;


    let fileKey;


    let path;


    let files;
    // non root folder drop
    if (dndItem && props.fileData) {
      if (!dndItem.dirContent) {
        fileKey = props.fileData.edge.node.key;

        const fileNameParts = fileKey.split('/');
        const fileName = fileNameParts[fileNameParts.length - 1];
        const newKey = props.newKey || props.fileKey;
        newPath = newKey + fileName;
        fileKey = props.fileKey;
      } else {
        // check if user needs to be prompted to accept some files in upload
        const fileSizeData = checkFileSize(dndItem.files, promptType);
        if (fileSizeData.fileSizePrompt.length === 0) {
          uploadDirContent(dndItem, props, props.mutationData, fileSizeData);
        } else {
          props.codeDirUpload(dndItem, props, props.mutationData, uploadDirContent, fileSizeData);
        }
      }
    } else {
      // root folder upload
      const {
        parentId,
        connection,
        favoriteConnection,
        section,
      } = props;
      const { owner, labbookName } = store.getState().routes;

      const mutationData = {
        owner,
        labbookName,
        parentId,
        connection,
        favoriteConnection,
        section,
      };
      // uploads to root directory
      const item = monitor.getItem();
      // check to see if it is an upload
      if (item.files) {
        // check to see if user needs to be prompted for upload
        const fileSizeData = checkFileSize(item.files, promptType);
        if (fileSizeData.fileSizePrompt.length === 0) {
          if (dndItem.dirContent) {
            uploadDirContent(dndItem, props, mutationData, fileSizeData);
          } else {
            CreateFiles.createFiles(item.files, '', component.state.mutationData, props, fileSizeData);
          }
        } else if (dndItem.dirContent) {
          component._codeDirUpload(dndItem, props, mutationData, uploadDirContent, fileSizeData);
        } else {
          component._codeFileUpload(item.files, props, component.state.mutationData, CreateFiles.createFiles, fileSizeData);
        }
      } else { // else it's a move
        const dropResult = monitor.getDropResult();
        const currentKey = item.fileData.edge.node.key;
        const splitKey = currentKey.split('/');
        const newKeyTemp = (splitKey[splitKey.length - 1] !== '') ? splitKey[splitKey.length - 1] : splitKey[splitKey.length - 2];
        const splitFolder = dropResult && dropResult.fileData ? dropResult.fileData.edge.node.key.split('/') : [''];
        if (splitFolder !== '') {
          splitFolder.pop();
        }

        const dropFolderKey = splitFolder.join('/');

        let newKey = item.fileData && item.fileData.edge.node.isDir ? `${dropFolderKey}/${newKeyTemp}/` : `${dropFolderKey}/${newKeyTemp}`;
        newKey = dropResult && dropResult.fileData ? newKey : `${newKeyTemp}`;

        if ((newKey !== item.fileData.edge.node.key) && ((`${newKey}/`) !== item.fileData.edge.node.key)) {
          const removeIds = [item.fileData.edge.node.id];
          const currentHead = item.fileData;

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
          const moveLabbookFileData = {
            newKey,
            edge: item.fileData.edge,
            removeIds,
          };

          if (props.mutations) {
            if (props.section !== 'data') {
              props.mutations.moveLabbookFile(moveLabbookFileData, (response) => {});
            } else {
              props.mutations.moveDatasetFile(moveLabbookFileData, (response) => {});
            }
          } else {
            const {
              parentId,
              connection,
              favoriteConnection,
              section,
            } = props;
            const { owner, labbookName } = store.getState().routes;

            const mutationData = {
              owner,
              labbookName,
              parentId,
              connection,
              favoriteConnection,
              section,
            };

            const mutations = new FileBrowserMutations(mutationData);

            if (props.section !== 'data') {
              mutations.moveLabbookFile(moveLabbookFileData, (response) => {});
            } else {
              mutations.moveDatasetFile(moveLabbookFileData, (response) => {});
            }
          }
        }
      }
    }

    return {
      fileData: props.fileData,
    };
  },
};

function targetCollect(connect, monitor) {
  // TODO: clean up this code, removal of file drop containers removes the need for some of this logic.
  // decide if drop zone should appear;
  const item = monitor.getItem();
  const currentTargetId = monitor.targetId;
  const isOverCurrent = monitor.isOver({ shallow: true });
  let isOver = monitor.isOver({});
  let canDrop = monitor.canDrop();
  const currentTarget = monitor.internalMonitor.registry.dropTargets.get(currentTargetId);

  let newLastTarget;
  // get a list of drop target ids
  const targetIds = monitor.internalMonitor.getTargetIds();
  const targets = targetIds.map(id => monitor.internalMonitor.registry.dropTargets.get(id));
  // if targets found
  if (targets.length > 0) {
    // get the last target
    const lastTarget = targets[targets.length - 1];

    // if last target is a file remove it
    if (lastTarget.props.fileData && !lastTarget.props.fileData.edge.node.isDir) {
      targets.pop();
    }
    newLastTarget = targets[targets.length - 1];
    // check if current targe is over last target
    isOver = (currentTargetId === newLastTarget.monitor.targetId);
  } else {
    isOver = false;
  }
  // check if item is dragging
  let dragItem;
  monitor.internalMonitor.registry.dragSources.forEach((item) => {
    if (item.ref && item.ref.current && item.ref.current.props.isDragging) {
      dragItem = item.ref.current;
    }
  });
  // compare dragItem and lastTarget
  if (dragItem && newLastTarget) {
    const dragKeyArray = dragItem.props.fileData.edge.node.key.split('/');
    dragKeyArray.pop();
    // check if file drag key is the same
    const dragKeyPruned = dragKeyArray.join('/') === '' ? '' : `${dragKeyArray.join('/')}/`;
    const dropKey = newLastTarget.props.files ? '' : newLastTarget.props.fileData.edge.node.key;
    canDrop = (dragKeyPruned !== dropKey);
    isOver = isOver && canDrop;
  }
  const { uploading } = store.getState().fileBrowser;
  isOver = isOver && !uploading;
  if (item && ((item.section === 'data') && !item.isLocal)) {
    // empty object expected for collect
    return {};
  }
  return {
    connectDropTarget: connect.dropTarget(),
    canDrop,
    isOver,
    isOverCurrent,
  };
}

const Connectors = {
  dragSource,
  dragCollect,
  targetSource,
  targetCollect,
};

export default Connectors;

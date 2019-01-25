import React from 'react';
import { DragSource } from 'react-dnd';
import uuidv4 from 'uuid/v4';
import FileBrowserMutations from './FileBrowserMutations';
// utilities
import CreateFiles from './../utilities/CreateFiles';
// store
import store from 'JS/redux/store';
// config
import config from 'JS/config';


/**
* @param {Array:[Object]} files
* @param {Boolean} prompt
*
* @return {number} totalFiles
*/
const checkFileSize = (files, prompt) => {
  const tenMB = 10 * 1000 * 1000;
  const oneHundredMB = 100 * 1000 * 1000;
  const eighteenHundredMB = oneHundredMB * 18;
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
        if (prompt) {
          if (file.size > oneHundredMB) {
            fileSizeNotAllowed.push(file);
          }

          if ((file.size > tenMB) && (file.size < oneHundredMB)) {
            fileSizePrompt.push(file);
          }
        } else if (file.size > eighteenHundredMB) {
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
  };
 },

  endDrag(props, monitor, component) {
    if (!monitor.didDrop()) {
      return;
    }

    const item = monitor.getItem();
    const dropResult = monitor.getDropResult();

    let fileNameParts = props.fileData.edge.node.key.split('/');

    let fileName = fileNameParts[fileNameParts.length - 1];

    if (dropResult.fileData) {
      let pathArray = dropResult.fileData.edge.node.key.split('/');
      // remove filename or empty string
      pathArray.pop();
      let path = pathArray.join('/');

      let newKey = path ? `${path}/${fileName}` : `${fileName}`;

      let newKeyArray = dropResult.fileData.edge.node.key.split('/');
      let fileKeyArray = props.fileData.edge.node.key.split('/');

      newKeyArray.pop();
      fileKeyArray.pop();

      let newKeyPath = newKeyArray.join('/');
      let fileKeyPath = fileKeyArray.join('/');
      newKeyPath = newKeyPath.replace(/\/\/\/g/, '/');
      const trimmedFilePath = (fileKeyPath + (fileName.length ? `/${fileName}` : '')).split('/').slice(0, -1).join('/');

      if ((newKeyPath !== fileKeyPath) && (trimmedFilePath !== newKeyPath)) {
        if (newKey !== props.fileData.edge.node.key) {
          let removeIds = [props.fileData.edge.node.id];
          let currentHead = props.fileData;
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
        let key = props.fileData ? props.fileData.edge.node.key : props.fileKey ? props.fileKey : '';
        path = key === '' ? '' : key.substr(0, key.lastIndexOf('/') || key.length);

        CreateFiles.createFiles(fileList.flat(), `${path}/`, mutationData, props, fileSizeData);
      } else if (dndItem.files && dndItem.files.length) {
           // handle dragged files
           let key = props.newKey || props.fileKey;
           path = key.substr(0, key.lastIndexOf('/') || key.length);
           let item = monitor.getItem();

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
     const { uploading } = store.getState().fileBrowser;
     return monitor.isOver({ shallow: true }) && !uploading;
  },
  drop(props, monitor, component) {
    // TODO: clean up this code, some of this logic is being duplicated. make better use of functions
    const dndItem = monitor.getItem();
    const prompt = (props.section === 'code') || (props.mutationData && (props.mutationData.section === 'code'));

    let newPath,
        fileKey,
        path,
        files;
    // non root folder drop
    if (dndItem && props.fileData) {
          if (!dndItem.dirContent) {
              fileKey = props.fileData.edge.node.key;

              const fileNameParts = fileKey.split('/');
              const fileName = fileNameParts[fileNameParts.length - 1];
              let newKey = props.newKey || props.fileKey;
              newPath = newKey + fileName;
              fileKey = props.fileKey;
          } else {
            // check if user needs to be prompted to accept some files in upload
            let fileSizeData = checkFileSize(dndItem.files, prompt);
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
          let item = monitor.getItem();
          // check to see if it is an upload
          if (item.files) {
            // check to see if user needs to be prompted for upload
            let fileSizeData = checkFileSize(item.files, prompt);
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
            let currentKey = item.fileData.edge.node.key;
            let splitKey = currentKey.split('/');
            let newKeyTemp = (splitKey[splitKey.length - 1] !== '') ? splitKey[splitKey.length - 1] : splitKey[splitKey.length - 2];
            let splitFolder = dropResult && dropResult.fileData ? dropResult.fileData.edge.node.key.split('/') : [''];
            if (splitFolder !== '') {
              splitFolder.pop();
            }

            let dropFolderKey = splitFolder.join('/');

            let newKey = item.fileData && item.fileData.edge.node.isDir ? `${dropFolderKey}/${newKeyTemp}/` : `${dropFolderKey}/${newKeyTemp}`;
            newKey = dropResult && dropResult.fileData ? newKey : `${newKeyTemp}`;

            if ((newKey !== item.fileData.edge.node.key) && ((`${newKey}/`) !== item.fileData.edge.node.key)) {
              let removeIds = [item.fileData.edge.node.id];
              let currentHead = item.fileData;

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
                props.mutations.moveLabbookFile(moveLabbookFileData, (response) => {});
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

                mutations.moveLabbookFile(moveLabbookFileData, (response) => {});
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
  let currentTargetId = monitor.targetId;
  let isOverCurrent = monitor.isOver({ shallow: true });
  let isOver = monitor.isOver({});
  let canDrop = monitor.canDrop();
  let currentTarget = monitor.internalMonitor.registry.dropTargets.get(currentTargetId);

  let newLastTarget;
  // get a list of drop target ids
  let targetIds = monitor.internalMonitor.getTargetIds();
  let targets = targetIds.map(id => monitor.internalMonitor.registry.dropTargets.get(id));
  // if targets found
  if (targets.length > 0) {
    // get the last target
    let lastTarget = targets[targets.length - 1];

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
    let dragKeyArray = dragItem.props.fileData.edge.node.key.split('/');
    dragKeyArray.pop();
    // check if file drag key is the same
    let dragKeyPruned = dragKeyArray.join('/') === '' ? '' : `${dragKeyArray.join('/')}/`;
    let dropKey = newLastTarget.props.files ? '' : newLastTarget.props.fileData.edge.node.key;
    canDrop = (dragKeyPruned !== dropKey);
    isOver = isOver && canDrop;
  }
  const { uploading } = store.getState().fileBrowser;
  isOver = isOver && !uploading;

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

// mutations
import DeleteLabbookFilesMutation from 'Mutations/fileBrowser/DeleteLabbookFilesMutation';
import DeleteDatasetFilesMutation from 'Mutations/fileBrowser/DeleteDatasetFilesMutation';
import MakeLabbookDirectoryMutation from 'Mutations/fileBrowser/MakeLabbookDirectoryMutation';
import MakeDatasetDirectoryMutation from 'Mutations/fileBrowser/MakeDatasetDirectoryMutation';
import MoveLabbookFileMutation from 'Mutations/fileBrowser/MoveLabbookFileMutation';
import MoveDatasetFileMutation from 'Mutations/fileBrowser/MoveDatasetFileMutation';
import AddFavoriteMutation from 'Mutations/fileBrowser/AddFavoriteMutation';
import RemoveFavoriteMutation from 'Mutations/fileBrowser/RemoveFavoriteMutation';
import DownloadDatasetFilesMutation from 'Mutations/DownloadDatasetFilesMutation';
import CompleteBatchUploadTransactionMutation from 'Mutations/fileBrowser/CompleteBatchUploadTransactionMutation';
import UpdateUnmanagedDatasetMutation from 'Mutations/UpdateUnmanagedDatasetMutation';
import VerifyDatasetMutation from 'Mutations/VerifyDatasetMutation';
// store
import store from 'JS/redux/store';
import { setErrorMessage } from 'JS/redux/actions/footer';
import { setIsProcessing } from 'JS/redux/actions/dataset/dataset';

class FileBrowserMutations {
  /**
    * @param {Object} props
    *        {string} props.owner
    *        {string} props.labbookName
    *        {string} props.section
    *        {string} props.connection
    *        {string} props.favoriteConnection
    *        {string} props.parentId
    * pass above props to state
    */
  constructor(props) {
    this.state = props;
  }

  downloadDatasetFiles(data, callback) {
    const {
      keys,
      allKeys,
      owner,
      datasetName,
      labbookName,
      labbookOwner,
      successCall,
      failureCall,
    } = data;

    DownloadDatasetFilesMutation(
      owner,
      datasetName,
      labbookName,
      labbookOwner,
      successCall,
      failureCall,
      keys,
      allKeys,
      callback,
    );
  }

  /**
   *  @param {Object} data
   *         {string} data.key
   *  @param {function} callback
   *  creates a dirctory using MakeLabbookDirectoryMutation
   */
  makeLabbookDirectory(data, callback) {
    const {
      key,
    } = data;

    const {
      connection,
      owner,
      labbookName,
      parentId,
      section,
    } = this.state;
    if (section !== 'data') {
      MakeLabbookDirectoryMutation(
        connection,
        owner,
        labbookName,
        parentId,
        key,
        section,
        (response, error) => {
          if (error) {
            console.error(error);
            setErrorMessage(`ERROR: could not create ${key}`, error);
          }
          callback(response, error);
        },
      );
    } else {
      setIsProcessing(true);
      MakeDatasetDirectoryMutation(
        connection,
        owner,
        labbookName,
        parentId,
        `${key}/`,
        (response, error) => {
          if (error) {
            console.error(error);
            setErrorMessage(`ERROR: could not create ${key}`, error);
          }
          setTimeout(() => setIsProcessing(false), 1100);
          callback(response, error);
        },
      );
    }
  }

  /**
   *  @param {Object} data
   *         {string} data.newKey
   *         {Object} data.edge
   *         {Array[string]} data.removeIds
   *  @param {function} callback
   *  moves file from old folder to a new folder
   */
  moveDatasetFile(data, callback) {
    const {
      edge,
      newKey,
      removeIds,
    } = data;

    const {
      connection,
      owner,
      labbookName,
      section,
      parentId,
    } = this.state;

    const { key } = edge.node;

    setIsProcessing(true);
    MoveDatasetFileMutation(
      connection,
      owner,
      labbookName,
      parentId,
      edge,
      key,
      newKey,
      section,
      removeIds,
      (response, error) => {
        setTimeout(() => setIsProcessing(false), 1100);
        callback(response, error);
      },
    );
  }

  /**
   *  @param {Object} data
   *         {string} data.newKey
   *         {Object} data.edge
   *         {Array[string]} data.removeIds
   *  @param {function} callback
   *  moves file from old folder to a new folder
   */
  moveLabbookFile(data, callback) {
    const {
      edge,
      newKey,
      removeIds,
    } = data;

    const {
      connection,
      owner,
      labbookName,
      section,
      parentId,
    } = this.state;

    const { key } = edge.node;

    MoveLabbookFileMutation(
      connection,
      owner,
      labbookName,
      parentId,
      edge,
      key,
      newKey,
      section,
      removeIds,
      (response, error) => {
        callback(response, error);
      },
    );
  }

  /**
  *  @param {Object} data
  *         {string} data.key
  *         {Object} data.edge
  *  @param {function} callback
  *  add file favorite to appear in favorite section
  */
  addFavorite(data, callback) {
    const {
      key,
      edge,
    } = data;

    const {
      connection,
      favoriteConnection,
      owner,
      labbookName,
      section,
      parentId,
    } = this.state;

    AddFavoriteMutation(
      favoriteConnection,
      connection,
      parentId,
      owner,
      labbookName,
      key,
      '',
      edge.node.isDir,
      edge,
      section,
      (response, error) => {
        if (error) {
          console.error(error);
          setErrorMessage(`ERROR: could not add favorite ${key}`, error);
        }
      },
    );
  }

  /**
  *  @param {Object} data
  *         {string} data.key
  *         {Object} data.edge
  *  @param {function} callback
  *  remove file from favorite section
  */
  removeFavorite(data, callback) {
    const {
      key,
      edge,
    } = data;


    const edgeId = edge.node.id;
    const {
      favoriteConnection,
      owner,
      labbookName,
      section,
      parentId,
    } = this.state;

    RemoveFavoriteMutation(
      favoriteConnection,
      parentId,
      owner,
      labbookName,
      section,
      key,
      edgeId,
      edge,
      (response, error) => {
        if (error) {
          console.error(error);
          setErrorMessage(`ERROR: could not remove favorite ${key}`, error);
        } else {
          let tempKey = key;
          if (tempKey[0] === '/') {
            tempKey = tempKey.slice(1);
          }

          callback(tempKey);
        }
      },
    );
  }

  /**
  *  @param {Object} data
  *         {Array[string]} data.filePaths
  *         {Array[Object]} data.edges
  *  @param {function} callback
  *  remove file or folder from directory
  */
  deleteLabbookFiles(data, callback) {
    const {
      filePaths,
      edges,
    } = data;
    const {
      connection,
      owner,
      labbookName,
      parentId,
      section,
    } = this.state;

    if (section !== 'data') {
      edges.forEach((edge) => {
        if (edge && edge.node && edge.node.isFavorite) {
          const data = {
            key: edge.node.key,
            edge,
          };
          this.removeFavorite(data, () => {});
        }
      });
    }
    if (section !== 'data') {
      DeleteLabbookFilesMutation(
        connection,
        owner,
        labbookName,
        parentId,
        filePaths,
        section,
        edges,
        (response, error) => {
          if (error) {
            console.error(error);
            const keys = filePaths.join(' ');
            setErrorMessage(`ERROR: could not delete folders ${keys}`, error);
          }
        },
      );
    } else {
      setIsProcessing(true);

      DeleteDatasetFilesMutation(
        connection,
        owner,
        labbookName,
        parentId,
        filePaths,
        section,
        edges,
        (response, error) => {
          if (error) {
            console.error(error);
            const keys = filePaths.join(' ');
            setErrorMessage(`ERROR: could not delete folders ${keys}`, error);
          }
          setTimeout(() => setIsProcessing(false), 1100);
        },
      );
    }
  }

  /**
  *  @param {undefined} data
  *  @param {function} callback
  *  remove file from favorite section
  */
  completeBatchUploadTransaction(data, callback) {
    const {
      connection,
      owner,
      labbookName,
      section,
    } = this.state;
    const { transactionId } = store.getState().fileBrowser;

    CompleteBatchUploadTransactionMutation(
      connection,
      owner,
      labbookName,
      true,
      false,
      transactionId,
      (response, error) => {

      },
    );
  }


  /**
  *  @param {undefined} data
  *  @param {function} callback
  *  updates unmanaged dataset
  */
  updateUnmanagedDataset(data, callback) {
    const {
      owner,
      labbookName,
    } = this.state;

    const {
      fromLocal,
      fromRemote,
    } = data;

    UpdateUnmanagedDatasetMutation(
      owner,
      labbookName,
      fromLocal,
      fromRemote,
      callback,
    );
  }

  /**
  *  @param {undefined} data
  *  @param {function} callback
  *  verifies unmanaged dataset
  */
  verifyDataset(data, callback) {
    const {
      owner,
      labbookName,
    } = this.state;

    const {
      fromLocal,
      fromRemote,
    } = data;

    VerifyDatasetMutation(
      owner,
      labbookName,
      (response, error) => {

      },
    );
  }
}

export default FileBrowserMutations;

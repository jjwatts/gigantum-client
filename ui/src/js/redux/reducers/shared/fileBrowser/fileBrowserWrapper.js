import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    uploading: false,
    pause: false,
    pauseUploadModalOpen: false,
    files: [],
    count: 0,
    transactionId: '',
    prefix: '',
    totalFiles: 0,
    chunkUploadData: {},
  },
  action,
) => {
  if (action.type === types.STARTED_UPLOADING) {
    return {
      ...state,
      uploading: true,
    };
  } if (action.type === types.FINISHED_UPLOADING) {
    return {
      ...state,
      uploading: false,
    };
  } if (action.type === types.PAUSE_UPLOAD) {
    return {
      ...state,
      pause: action.payload.pause,
    };
  } if (action.type === types.PAUSE_UPLOAD_DATA) {
    return {
      ...state,
      files: action.payload.files,
      count: action.payload.count,
      transactionId: action.payload.transactionId,
      prefix: action.payload.prefix,
      totalFiles: action.payload.totalFiles,
    };
  } if (action.type === types.PAUSE_CHUNK_UPLOAD) {
    const {
      data,
      chunkData,
      section,
      username,
    } = action.payload;

    const chunkUploadData = {
      data,
      chunkData,
      section,
      username,
    };
    return {
      ...state,
      chunkUploadData,
    };
  } if (action.type === types.RESET_CHUNK_UPLOAD) {
    return {
      ...state,
      chunkUploadData: {},
    };
  }

  return state;
};

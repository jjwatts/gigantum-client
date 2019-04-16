import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setFinishedUploading = () => dispatcher(
  types.FINISHED_UPLOADING,
  {},
);

export const setPauseChunkUpload = (
  data,
  chunkData,
  section,
  username,
) => dispatcher(
  types.PAUSE_CHUNK_UPLOAD,
  {
    data,
    chunkData,
    section,
    username,
  },
);

export const setPauseUpload = pause => dispatcher(
  types.PAUSE_UPLOAD,
  { pause },
);

export const setPauseUploadData = (
  files,
  count,
  transactionId,
  prefix,
  totalFiles,
) => dispatcher(
  types.PAUSE_UPLOAD_DATA,
  {
    files,
    count,
    transactionId,
    prefix,
    totalFiles,
  },
);

export const setStartedUploading = () => dispatcher(
  types.STARTED_UPLOADING,
  {},
);
export const setResetChunkUpload = () => dispatcher(
  types.RESET_CHUNK_UPLOAD,
  {},
);

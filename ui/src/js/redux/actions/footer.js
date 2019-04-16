import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setErrorMessage = (
  message,
  messageBody,
) => dispatcher(types.ERROR_MESSAGE, { message, messageBody });

export const setWarningMessage = message => dispatcher(types.WARNING_MESSAGE, { message });
export const setInfoMessage = message => dispatcher(types.INFO_MESSAGE, { message });

export const setMultiInfoMessage = (
  id,
  message,
  isLast,
  error,
  messageBody,
) => dispatcher(
  types.MULTIPART_INFO_MESSAGE,
  {
    id,
    message,
    isLast,
    error,
    messageBody,
  },
);
// upload bar
export const setUploadMessageSetter = (
  uploadMessage,
  id,
  totalFiles,
) => dispatcher(
  types.UPLOAD_MESSAGE_SETTER,
  {
    uploadMessage,
    id,
    totalFiles,
  },
);

export const setUploadMessageUpdate = (
  uploadMessage,
  fileCount,
  progessBarPercentage,
  uploadError,
) => dispatcher(
  types.UPLOAD_MESSAGE_UPDATE,
  {
    uploadMessage,
    fileCount,
    progessBarPercentage,
    uploadError,
  },
);

export const setUploadMessageRemove = (
  uploadMessage,
  id,
  progessBarPercentage,
) => dispatcher(
  types.UPLOAD_MESSAGE_REMOVE,
  {
    uploadMessage,
    id,
    progessBarPercentage,
  },
);


export const setUpdateHistoryView = () => dispatcher(
  types.UPDATE_HISTORY_VIEW,
  {},
);

export const setResizeFooter = () => dispatcher(
  types.RESIZE_FOOTER,
  {},
);

export const setResetFooter = () => dispatcher(
  types.RESET_FOOTER_STORE,
  {},
);
export const setRemoveMessage = id => dispatcher(
  types.REMOVE_MESSAGE,
  { id },
);

// visibility toggles
export const setHelperVisible = helperVisible => dispatcher(
  types.HELPER_VISIBLE,
  { helperVisible },
);

export const setToggleMessageList = (
  messageListOpen,
  viewHistory,
) => dispatcher(
  types.TOGGLE_MESSAGE_LIST,
  {
    messageListOpen,
    viewHistory,
  },
);

export const setUpdateMessageStackItemVisibility = index => dispatcher(
  types.UPDATE_MESSAGE_STACK_ITEM_VISIBILITY,
  { index },
);
export const setUpdateHistoryStackItemVisibility = index => dispatcher(
  types.UPDATE_HISTORY_STACK_ITEM_VISIBILITY,
  { index },
);

import uuidv4 from 'uuid/v4';
import * as types from 'JS/redux/constants/constants';

let tempId = 0;
const messageStackHistory = window.sessionStorage.getItem('messageStackHistory') ? JSON.parse(window.sessionStorage.getItem('messageStackHistory')) : [];

export default (state = {
  open: false,
  uploadOpen: false,
  currentMessage: '',
  uploadMessage: '',
  currentId: '',
  currentUploadId: '',
  uploadError: false,
  success: false,
  labbookName: '',
  messageStackHistory,
  messageStack: [],
  uploadStack: [],
  fileCount: 0,
  totalFiles: 0,
  totalBytes: 0,
  labbookSuccess: false,
  messageListOpen: false,
  viewHistory: false,
  helperVisible: false,
  uuid: '',
  buildProgress: false,
}, action) => {
  const checkHistoryStackLength = (messageStackHistory) => {
    if (messageStackHistory.length > 50) {
      messageStackHistory.pop();
    }

    return messageStackHistory;
  };
  const date = new Date();
  if (action.type === types.ERROR_MESSAGE) {
    const id = types.ERROR_MESSAGE + tempId++;
    const messageStack = state.messageStack;
    let messageStackHistory = state.messageStackHistory;


    const message = {
      message: action.payload.message,
      id,
      error: true,
      date,
      messageBodyOpen: false,
      className: 'Footer__message--error',
      messageBody: action.payload.messageBody
        ? action.payload.messageBody
        : [],
    };

    messageStack.unshift(message);
    messageStackHistory.unshift(message);

    messageStackHistory = checkHistoryStackLength(messageStackHistory);

    window.sessionStorage.setItem('messageStackHistory', JSON.stringify(messageStackHistory));

    return {
      ...state,
      messageStack,
      messageStackHistory,
      currentId: id,
      showProgressBar: false,
      open: true,
      success: false,
      messageListOpen: true,
      viewHistory: false,
    };
  } if (action.type === types.INFO_MESSAGE) { // this is for only updating a single message
    const id = types.INFO_MESSAGE + tempId++;
    const messageStack = state.messageStack;
    let messageStackHistory = state.messageStackHistory;


    const message = {
      message: action.payload.message,
      id,
      error: false,
      className: 'Footer__message',
      messageBody: action.payload.messageBody
        ? action.payload.messageBody
        : [],
      isMultiPart: false,
      messageBodyOpen: false,
      date,
    };

    messageStack.unshift(message);
    messageStackHistory.unshift(message);

    messageStackHistory = checkHistoryStackLength(messageStackHistory);

    window.sessionStorage.setItem('messageStackHistory', JSON.stringify(messageStackHistory));

    return {
      ...state,
      messageStack,
      messageStackHistory,
      currentMessage: action.payload.message,
      currentId: id,
      open: true,
      success: true,
      showProgressBar: false,
      messageListOpen: true,
      viewHistory: false,
    };
  } if (action.type === types.WARNING_MESSAGE) { // this is for only updating a single message
    const id = types.INFO_MESSAGE + tempId++;
    const messageStack = state.messageStack;
    let messageStackHistory = state.messageStackHistory;

    const message = {
      message: action.payload.message,
      id,
      error: false,
      className: 'Footer__message--warning',
      messageBody: action.payload.messageBody
        ? action.payload.messageBody
        : [],
      messageBodyOpen: false,
      date,
    };

    messageStack.unshift(message);

    messageStackHistory.unshift(message);
    messageStackHistory = checkHistoryStackLength(messageStackHistory);

    window.sessionStorage.setItem('messageStackHistory', JSON.stringify(messageStackHistory));

    return {
      ...state,
      currentMessage: action.payload.message,
      currentId: id,
      messageStack,
      messageStackHistory,
      open: true,
      success: true,
      showProgressBar: false,
      messageListOpen: true,
      viewHistory: false,
    };
  } if (action.type === types.REMOVE_MESSAGE) { // this is for only updating a single message
    const messageStack = [];

    state.messageStack.forEach((messageItem) => {
      if (messageItem.id !== action.payload.id) {
        messageStack.push(messageItem);
      }
    });

    const messageListOpen = (state.viewHistory && state.messageListOpen) || (!state.viewHistory && (messageStack.length > 0));
    const lastIndex = messageStack.length - 1;

    return {
      ...state,
      currentMessage: messageStack[lastIndex],
      currentId: messageStack[lastIndex],
      messageStack,
      open: messageStack.length > 0,
      success: true,
      showProgressBar: false,
      messageListOpen,

    };
  } if (action.type === types.UPLOAD_MESSAGE_SETTER) {
    const message = {
      message: action.payload.currentMessage,
      id: action.payload.id,
      progessBarPercentage: action.payload.percentage,
    };

    const uploadStack = state.uploadStack;
    uploadStack.push(message);

    return {
      ...state,
      uploadStack,
      uploadMessage: action.payload.uploadMessage,
      currentUploadId: message.id,
      uploadOpen: true,
      success: false,
      uploadError: false,
      fileCount: 0,
      totalBytes: action.payload.totalBytes
        ? action.payload.totalBytes
        : 0,
      totalFiles: action.payload.totalFiles
        ? action.payload.totalFiles
        : 0,
      viewHistory: false,
    };
  } if (action.type === types.UPLOAD_MESSAGE_UPDATE) {
    const message = {
      message: action.payload.uploadMessage,
      id: action.payload.id,
      progessBarPercentage: action.payload.progessBarPercentage,
    };

    const uploadStack = state.uploadStack.map((messageItem) => {
      if (message.id === messageItem.id) {
        return message;
      }
      return messageItem;
    });

    const uploadError = action.payload.uploadError
      ? action.payload.uploadError
      : false;

    const uploadMessage = action.payload.uploadError
      ? 'Error Uploading'
      : action.payload.uploadMessage;

    return {
      ...state,
      uploadMessage,
      currentUploadId: action.payload.id,
      progessBarPercentage: action.payload.progessBarPercentage,
      fileCount: action.payload.fileCount,
      uploadStack,
      uploadOpen: true,
      uploadError,
      success: false,
    };
  } if (action.type === types.UPLOAD_MESSAGE_REMOVE) {
    const message = {
      message: action.payload.uploadMessage,
      id: action.payload.id,
      progessBarPercentage: action.payload.progessBarPercentage,
    };

    const uploadStack = [];

    state.uploadStack.forEach((messageItem) => {
      if (message.id !== messageItem.id) {
        uploadStack.push(messageItem);
      }
    });

    return {
      ...state,
      uploadMessage: '',
      currentUploadId: message.id,
      uploadStack,
      progessBarPercentage: 0,
      fileCount: 0,
      totalFiles: 0,
      uploadOpen: false,
      success: true,
      labbookName: '',
      labbookSuccess: false,
    };
  } if (action.type === types.IMPORT_MESSAGE_SUCCESS) {
    const message = {
      message: action.payload.uploadMessage,
      id: action.payload.id,
      progessBarPercentage: 100,
    };

    const uploadStack = [];

    state.uploadStack.forEach((messageItem) => {
      if (message.id !== messageItem.id) {
        uploadStack.push(messageItem);
      }
    });

    return {
      ...state,
      uploadMessage: action.payload.uploadMessage,
      labbookName: action.payload.labbookName,
      currentUploadId: message.id,
      uploadStack,
      progessBarPercentage: 100,
      uploadOpen: true,
      success: true,
      labbookSuccess: true,
    };
  } if (action.type === types.TOGGLE_MESSAGE_LIST) {
    const messageStack = [];

    const messageStackHistory = state.messageStackHistory.map((message) => {
      message.dismissed = true;
      return message;
    });

    return {
      ...state,
      messageListOpen: action.payload.messageListOpen,
      viewHistory: action.payload.viewHistory,
      messageStack,
      messageStackHistory,
    };
  } if (action.type === types.HIDE_MESSAGE_LIST) {
    return {
      ...state,
      messageListOpen: false,
    };
  } if (action.type === types.MULTIPART_INFO_MESSAGE) {
    let messageStackHistory = state.messageStackHistory;
    const messageStack = state.messageStack;
    let previousHistoryIndex = 0;
    let previousIndex = 0;
    let messageBodyOpen = false;
    let messageListOpen = state.messageListOpen;

    const doesMessageExist = messageStack.filter((message, index) => {
      if (message.id === action.payload.id) {
        previousIndex = index;
        messageBodyOpen = message.messageBodyOpen;
      }

      return message.id === action.payload.id;
    });

    const doesHistoryMessageExist = messageStackHistory.filter((message, index) => {
      if (message.id === action.payload.id) {
        previousHistoryIndex = index;

        if (doesMessageExist.length === 0) {
          messageBodyOpen = message.messageBodyOpen;
        }
      }

      return message.id === action.payload.id;
    });

    if ((doesHistoryMessageExist.length > 0) && doesHistoryMessageExist[0].dismissed) {
      if (state.messageListOpen && state.viewHistory) {
        messageListOpen = true;
      } else {
        messageListOpen = false;
      }
    } else {
      messageListOpen = action.payload.messageListOpen === undefined || action.payload.messageListOpen;
    }

    const buildProgress = action.payload.buildProgress && (action.payload.message.indexOf('Using cached image') === -1);
    const message = {
      message: action.payload.message,
      id: action.payload.id,
      className: action.payload.error
        ? 'Footer__message--error'
        : 'Footer__message',
      isLast: action.payload.isLast,
      isMultiPart: true,
      messageBody: action.payload.messageBody
        ? action.payload.messageBody
        : [],
      error: action.payload.error,
      messageBodyOpen,
      buildProgress,
      dismissed: (doesHistoryMessageExist.length > 0) ? doesHistoryMessageExist[0].dismissed : false,
      date,
    };


    if (doesMessageExist.length > 0) {
      messageStack.splice(previousIndex, 1, message);
    } else {
      messageStack.unshift(message);
    }

    if (doesHistoryMessageExist.length > 0) {
      messageStackHistory.splice(previousHistoryIndex, 1, message);
    } else {
      messageStackHistory.unshift(message);
    }

    messageStackHistory = checkHistoryStackLength(messageStackHistory);
    window.sessionStorage.setItem('messageStackHistory', JSON.stringify(messageStackHistory));

    return {
      ...state,
      id: action.payload.id,
      message: action.payload.message,
      isLast: action.payload.isLast,
      messageStack,
      messageStackHistory,
      open: true,
      success: true,
      error: action.payload.error,
      messageListOpen,
      viewHistory: ((doesHistoryMessageExist.length > 0) && doesHistoryMessageExist[0].dismissed && state.viewHistory),
    };
  } if (action.type === types.RESET_FOOTER_STORE) {
    return {
      ...state,
      open: false,
      uploadOpen: false,
      showProgressBar: true,
      currentMessage: '',
      currentId: '',
      uploadError: false,
      success: false,
      labbookName: '',
      messageListOpen: false,
      viewHistory: false,
    };
  } if (action.type === types.UPDATE_MESSAGE_STACK_ITEM_VISIBILITY) {
    const messageStack = state.messageStack;
    messageStack[action.payload.index].messageBodyOpen = !messageStack[action.payload.index].messageBodyOpen;

    return {
      ...state,
      messageStack,
      uuid: uuidv4(),
    };
  } if (action.type === types.UPDATE_HISTORY_STACK_ITEM_VISIBILITY) {
    let newMessageStackHistory = state.messageStackHistory;
    const messageStackItem = newMessageStackHistory[action.payload.index];

    messageStackItem.messageBodyOpen = !messageStackItem.messageBodyOpen;
    newMessageStackHistory[action.payload.index] = messageStackItem;
    newMessageStackHistory = newMessageStackHistory.map((message, index) => {
      if (index === action.payload.index) {
        return message;
      }
      const newMessage = message;
      newMessage.messageBodyOpen = false;
      return newMessage;
    });

    return {
      ...state,
      messageStackHistory,
      uuid: uuidv4(),
    };
  } if (action.type === types.RESIZE_FOOTER) {
    return {
      ...state,
      resize: uuidv4(),
    };
  } if (action.type === types.UPDATE_HISTORY_VIEW) {
    const messageStack = [];
    const messageStackHistory = state.messageStackHistory.map((message) => {
      message.dismissed = true;
      return message;
    });

    return {
      ...state,
      viewHistory: true,
      messageStack,
      messageStackHistory,
    };
  } if (action.type === types.HELPER_VISIBLE) {
    return {
      ...state,
      helperVisible: action.payload.helperVisible,
    };
  }

  return state;
};

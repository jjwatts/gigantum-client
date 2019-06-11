import * as types from 'JS/redux/constants/constants';


export default (
  state = {
    isSticky: false,
    isProcessing: false,
    isUploading: false,
  },
  action,
) => {
  if (action.type === types.UPDATE_STICKY_STATE) {
    // preventing detail mode from opening until feature has been fully implemented
    return {
      ...state,
      isSticky: action.payload.isSticky,
    };
  } if (action.type === types.IS_UPLOADING) {
    return {
      ...state,
      isUploading: action.payload.isUploading,
    };
  } if (action.type === types.SET_IS_PROCESSING) {
    return {
      ...state,
      isProcessing: action.payload.isProcessing,
    };
  }

  return state;
};

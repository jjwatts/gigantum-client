import dispatcher from 'JS/redux/dispatcher';

/**
 * constants
 */
export const UPDATE_STICKY_STATE = 'UPDATE_STICKY_STATE';
export const SET_IS_PROCESSING = 'SET_IS_PROCESSING';


/**
 * actions
 */

export const setStickyState = isSticky => dispatcher(UPDATE_STICKY_STATE, { isSticky });
export const setIsProcessing = isProcessing => dispatcher(SET_IS_PROCESSING, { isProcessing });


export default (
  state = {
    isSticky: false,
    isProcessing: false,
  },
  action,
) => {
  if (action.type === UPDATE_STICKY_STATE) {
    // preventing detail mode from opening until feature has been fully implemented
    return {
      ...state,
      isSticky: action.payload.isSticky,
    };
  } if (action.type === SET_IS_PROCESSING) {
    return {
      ...state,
      isProcessing: action.payload.isProcessing,
    };
  }

  return state;
};

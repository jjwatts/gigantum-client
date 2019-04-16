import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';
/**
 * actions
 */

export const setStickyState = isSticky => dispatcher(
  types.UPDATE_STICKY_STATE,
  { isSticky },
);
export const setIsProcessing = isProcessing => dispatcher(
  types.SET_IS_PROCESSING,
  { isProcessing },
);

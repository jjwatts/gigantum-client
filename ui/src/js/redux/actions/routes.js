import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setCallbackRoute = callbackRoute => dispatcher(
  types.UPDATE_CALLBACK_ROUTE,
  { callbackRoute },
);
export const setUpdateAll = (owner, labbookName) => dispatcher(
  types.UPDATE_ALL,
  { owner, labbookName },
);

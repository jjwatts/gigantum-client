import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */

export const setContainerState = (labbookId, containerState) => dispatcher(
  types.UPDATE_CONTAINER_STATE,
  { labbookId, containerState },
);

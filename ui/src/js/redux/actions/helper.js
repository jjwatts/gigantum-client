import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setHelperVisibility = isVisible => dispatcher(types.UPDATE_HELPER_VISIBILITY, { isVisible });
export const setResizeHelper = () => dispatcher(types.RESIZE_HELPER, {});

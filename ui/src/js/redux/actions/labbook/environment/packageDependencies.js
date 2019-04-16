import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setPackageMenuVisible = packageMenuVisible => dispatcher(
  types.TOGGLE_PACKAGE_MENU,
  { packageMenuVisible },
);

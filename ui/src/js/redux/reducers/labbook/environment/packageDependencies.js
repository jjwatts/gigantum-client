import * as types from 'JS/redux/constants/constants';

export default (
  state = { packageMenuVisible: false },
  action,
) => {
  if (action.type === types.TOGGLE_PACKAGE_MENU) {
    return {
      ...state,
      packageMenuVisible: action.payload.packageMenuVisible,
    };
  }
  return state;
};

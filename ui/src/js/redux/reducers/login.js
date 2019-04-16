import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    error: false,
    logout: false,
  },
  action,
) => {
  if (action.type === types.LOGIN_ERROR) {
    return {
      ...state,
      error: action.payload.error,
    };
  } if (action.type === types.LOGIN_CLEAR) {
    return {
      ...state,
      error: false,
    };
  } if (action.type === types.LOGOUT) {
    return {
      ...state,
      logout: action.payload.logout,
    };
  }

  return state;
};

import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    currentRoute: '',
    owner: '',
    labbookName: '',
    callbackRoute: '',
  },
  action,
) => {
  if (action.type === types.UPDATE_OWNER) {
    return {
      ...state,
      owner: action.payload.owner,
    };
  } if (action.type === types.UPDATE_LABBOOKNAME) {
    return {
      ...state,
      labbookName: action.payload.labbookName,
    };
  } if (action.type === types.UPDATE_CALLBACK_ROUTE) {
    window.sessionStorage.setItem('CALLBACK_ROUTE', action.payload.callbackRoute);
    return {
      ...state,
      callbackRoute: action.payload.callbackRoute,
    };
  } if (action.type === types.UPDATE_ALL) {
    return {
      ...state,
      labbookName: action.payload.labbookName,
      owner: action.payload.owner,
    };
  }

  return state;
};

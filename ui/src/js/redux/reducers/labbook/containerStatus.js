import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    status: '',
    containerMenuOpen: false,
    isLookingUpPackages: false,
  },
  action,
) => {
  if (action.type === types.UPDATE_CONTAINER_STATUS) {
    return {
      ...state,
      status: action.payload.status,
    };
  } if (action.type === types.UPDATE_CONTAINER_MENU_VISIBILITY) {
    return {
      ...state,
      containerMenuOpen: action.payload.containerMenuOpen,
    };
  } if (action.type === types.RESET_DETAIL_STORE) {
    return {
      ...state,
      detailMode: false,
    };
  } if (action.type === types.IS_LOOKING_UP_PACKAGES) {
    return {
      ...state,
      isLookingUpPackages: action.payload.isLookingUpPackages,
    };
  }

  return state;
};

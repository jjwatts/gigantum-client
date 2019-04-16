import uuidv4 from 'uuid/v4';
import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    isVisible: false,
    resize: '',
    footerVisible: false,
  },
  action,
) => {
  if (action.type === types.UPDATE_HELPER_VISIBILITY) {
    return {
      ...state,
      isVisible: action.payload.isVisible,
    };
  } if (action.type === types.RESIZE_HELPER) {
    return {
      ...state,
      resize: uuidv4(),
    };
  }

  return state;
};

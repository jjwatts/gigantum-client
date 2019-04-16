import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    filterText: '',
  },
  action,
) => {
  if (action.type === types.SET_FILTER_TEXT) {
    return {
      ...state,
      filterText: action.payload.filterText,
    };
  }

  return state;
};

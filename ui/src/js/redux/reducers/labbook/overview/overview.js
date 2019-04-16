import * as types from 'JS/redux/constants/constants';

export default (
  state = {
    containerStates: {},
  },
  action,
) => {
  if (action.type === types.UPDATE_CONTAINER_STATE) {
    const { containerStates } = state;
    containerStates[action.payload.labbookId] = action.payload.containerState;
    return {
      ...state,
      containerStates,
    };
  } if (action.type === types.RESET_OVERVIEW_STORE) {
    return {
      ...state,
      containerStates: {},
    };
  }

  return state;
};

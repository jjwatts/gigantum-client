import * as types from 'JS/redux/constants/constants';


export default (
  state = {
    collaborators: null,
    canManageCollaborators: null,
  },
  action,
) => {
  if (action.type === types.SET_COLLABORATORS) {
    return {
      ...state,
      collaborators: action.payload.collaborators,
    };
  } if (action.type === types.SET_CANMANAGECOLLABORATORS) {
    return {
      ...state,
      canManageCollaborators: action.payload.canManageCollaborators,
    };
  }
  return state;
};

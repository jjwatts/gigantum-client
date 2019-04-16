import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';


/**
 * actions
*/
export const setCollaborators = collaborators => dispatcher(
  types.SET_COLLABORATORS,
  { collaborators },
);

export const setCanManageCollaborators = canManageCollaborators => dispatcher(
  types.SET_CANMANAGECOLLABORATORS,
  { canManageCollaborators },
);

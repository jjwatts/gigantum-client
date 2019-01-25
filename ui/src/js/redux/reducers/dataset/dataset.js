import dispatcher from 'JS/redux/dispatcher';

/**
 * constants
 */
export const UPDATE_STICKY_STATE = 'UPDATE_STICKY_STATE';


/**
 * actions
 */

export const setStickyState = isSticky => dispatcher(UPDATE_STICKY_STATE, { isSticky });


export default (
  state = {
    isSticky: false,
  },
  action,
) => {
  if (action.type === UPDATE_STICKY_STATE) {
    // preventing detail mode from opening until feature has been fully implemented
    return {
      ...state,
      isSticky: action.payload.isSticky,
    };
  }

  return state;
};

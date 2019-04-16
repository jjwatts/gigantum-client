import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';


/**
 * actions
 */

export const setContainerStatus = status => dispatcher(
  types.UPDATE_CONTAINER_STATUS,
  { status },
);

export const setContainerMenuVisibility = containerMenuOpen => dispatcher(
  types.UPDATE_CONTAINER_MENU_VISIBILITY,
  { containerMenuOpen },
);

export const setLookingUpPackagesState = isLookingUpPackages => dispatcher(
  types.IS_LOOKING_UP_PACKAGES,
  { isLookingUpPackages },
);

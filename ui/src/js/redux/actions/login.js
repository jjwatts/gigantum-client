import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setLogout = logout => dispatcher(types.LOGOUT, { logout });
export const setLoginError = error => dispatcher(types.LOGIN_ERROR, { error });

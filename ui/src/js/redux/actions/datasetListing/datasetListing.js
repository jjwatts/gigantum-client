import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */
export const setFilterText = filterText => dispatcher(
  types.SET_FILTER_TEXT,
  { filterText },
);

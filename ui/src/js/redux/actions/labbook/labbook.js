import dispatcher from 'JS/redux/dispatcher';
import * as types from 'JS/redux/constants/constants';

/**
 * actions
 */

export const setBuildingState = isBuilding => dispatcher(
  types.IS_BUILDING,
  { isBuilding },
);

export const setMergeMode = (branchesOpen, mergeFilter) => dispatcher(
  types.MERGE_MODE,
  {
    branchesOpen,
    mergeFilter,
  },
);

export const setSyncingState = isSyncing => dispatcher(
  types.IS_SYNCING,
  { isSyncing },
);

export const setPublishingState = isPublishing => dispatcher(
  types.IS_PUBLISHING,
  { isPublishing },
);

export const setExportingState = isExporting => dispatcher(
  types.IS_EXPORTING,
  { isExporting },
);

export const setModalVisible = modalVisible => dispatcher(
  types.MODAL_VISIBLE,
  { modalVisible },
);

export const setStickyDate = isSticky => dispatcher(
  types.UPDATE_STICKY_STATE,
  { isSticky },
);

export const setSidepanelVisible = sidePanelVisible => dispatcher(
  types.UPDATE_SIDEPANEL_VISIBLE,
  { sidePanelVisible },
);

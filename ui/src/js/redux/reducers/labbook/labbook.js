import dispatcher from 'JS/redux/dispatcher';

/**
 * constants
 */
export const INITIALIZE = 'INITIALIZE';
export const UPDATE_DETAIL_VIEW = 'UPDATE_DETAIL_VIEW';
export const RESET_LABBOOK_STORE = 'RESET_LABBOOK_STORE';
export const IS_BUILDING = 'IS_BUILDING';
export const IS_SYNCING = 'IS_SYNCING';
export const IS_EXPORTING = 'IS_EXPORTING';
export const IS_PUBLISHING = 'IS_PUBLISHING';
export const MODAL_VISIBLE = 'MODAL_VISIBLE';
export const SELECTED_COMPONENT = 'SELECTED_COMPONENT';
export const UPDATE_BRANCHES_VIEW = 'UPDATE_BRANCHES_VIEW';
export const UPDATE_ALL = 'UPDATE_ALL';
export const UPDATE_STICKY_STATE = 'UPDATE_STICKY_STATE';
export const UPDATE_SIDEPANEL_VISIBLE = 'UPDATE_SIDEPANEL_VISIBLE';
export const MERGE_MODE = 'MERGE_MODE';


/**
 * actions
 */

export const setBuildingState = isBuilding => dispatcher(IS_BUILDING, { isBuilding });
export const setMergeMode = (branchesOpen, mergeFilter) => dispatcher(MERGE_MODE, { branchesOpen, mergeFilter });
export const setSyncingState = isSyncing => dispatcher(IS_SYNCING, { isSyncing });
export const setPublishingState = isPublishing => dispatcher(IS_PUBLISHING, { isPublishing });
export const setExportingState = isExporting => dispatcher(IS_EXPORTING, { isExporting });
export const setModalVisible = modalVisible => dispatcher(MODAL_VISIBLE, { modalVisible });
export const setUpdateDetailView = detailMode => dispatcher(UPDATE_DETAIL_VIEW, { detailMode });
export const setStickyDate = isSticky => dispatcher(UPDATE_STICKY_STATE, { isSticky });
export const setSidepanelVisible = sidePanelVisible => dispatcher(UPDATE_SIDEPANEL_VISIBLE, { sidePanelVisible });


export default (
  state = {
    selectedComponent: '',
    containerState: '',
    imageStatus: '',
    isBuilding: false,
    isSyncing: false,
    isExporting: false,
    isPublishing: false,
    containerStatus: '',
    modalVisible: '',
    detailMode: false,
    previousDetailMode: false,
    branchesOpen: false,
    isSticky: false,
    mergeFilter: false,
    sidePanelVisible: false,
  },
  action,
) => {
  if (action.type === UPDATE_DETAIL_VIEW) {
    // preventing detail mode from opening until feature has been fully implemented
    return {
      ...state,
      previousDetailMode: false, // state.detailMode,
      detailMode: false, // action.payload.detailMode
    };
  } if (action.type === UPDATE_STICKY_STATE) {
    // preventing detail mode from opening until feature has been fully implemented
    return {
      ...state,
      isSticky: action.payload.isSticky,
    };
  } if (action.type === MERGE_MODE) {
    return {
      ...state,
      mergeFilter: action.payload.mergeFilter,
      branchesOpen: action.payload.branchesOpen,
    };
  } if (action.type === INITIALIZE) {
    return {
      ...state,
      selectedComponent: action.payload.selectedComponent,
      containerState: action.payload.containerState,
      imageStatus: action.payload.imageStatus,
    };
  } if (action.type === IS_BUILDING) {
    return {
      ...state,
      isBuilding: action.payload.isBuilding,
    };
  } if (action.type === IS_SYNCING) {
    return {
      ...state,
      isSyncing: action.payload.isSyncing,
    };
  } if (action.type === IS_EXPORTING) {
    return {
      ...state,
      isExporting: action.payload.isExporting,
    };
  } if (action.type === IS_PUBLISHING) {
    return {
      ...state,
      isPublishing: action.payload.isPublishing,
    };
  } if (action.type === SELECTED_COMPONENT) {
    return {
      ...state,
      selectedComponent: action.payload.selectedComponent,
    };
  } if (action.type === MODAL_VISIBLE) {
    return {
      ...state,
      modalVisible: action.payload.modalVisible,
    };
  } if (action.type === UPDATE_BRANCHES_VIEW) {
    return {
      ...state,
      branchesOpen: action.payload.branchesOpen,
    };
  } if (action.type === RESET_LABBOOK_STORE) {
    return {
      ...state,
      selectedComponent: '',
      containerState: '',
      imageStatus: '',
      isBuilding: false,
      isPublushing: false,
      isSyncing: false,
      isExporting: false,
      containerStatus: '',
      modalVisible: '',
      detailMode: false,
      previousDetailMode: false,
    };
  } if (action.type === UPDATE_ALL) {
    return {
      ...state,
      labbookName: action.payload.labbookName,
      owner: action.payload.owner,
    };
  } if (action.type === UPDATE_SIDEPANEL_VISIBLE) {
    return {
      ...state,
      sidePanelVisible: action.payload.sidePanelVisible,
    };
  }

  return state;
};

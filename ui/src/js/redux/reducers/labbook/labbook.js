import * as types from 'JS/redux/constants/constants';

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
  if (action.type === types.UPDATE_STICKY_STATE) {
    // preventing detail mode from opening until feature has been fully implemented
    return {
      ...state,
      isSticky: action.payload.isSticky,
    };
  } if (action.type === types.MERGE_MODE) {
    return {
      ...state,
      mergeFilter: action.payload.mergeFilter,
      branchesOpen: action.payload.branchesOpen,
    };
  } if (action.type === types.INITIALIZE) {
    return {
      ...state,
      selectedComponent: action.payload.selectedComponent,
      containerState: action.payload.containerState,
      imageStatus: action.payload.imageStatus,
    };
  } if (action.type === types.IS_BUILDING) {
    return {
      ...state,
      isBuilding: action.payload.isBuilding,
    };
  } if (action.type === types.IS_SYNCING) {
    return {
      ...state,
      isSyncing: action.payload.isSyncing,
    };
  } if (action.type === types.IS_EXPORTING) {
    return {
      ...state,
      isExporting: action.payload.isExporting,
    };
  } if (action.type === types.IS_PUBLISHING) {
    return {
      ...state,
      isPublishing: action.payload.isPublishing,
    };
  } if (action.type === types.SELECTED_COMPONENT) {
    return {
      ...state,
      selectedComponent: action.payload.selectedComponent,
    };
  } if (action.type === types.MODAL_VISIBLE) {
    return {
      ...state,
      modalVisible: action.payload.modalVisible,
    };
  } if (action.type === types.UPDATE_BRANCHES_VIEW) {
    return {
      ...state,
      branchesOpen: action.payload.branchesOpen,
    };
  } if (action.type === types.RESET_LABBOOK_STORE) {
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
  } if (action.type === types.UPDATE_ALL) {
    return {
      ...state,
      labbookName: action.payload.labbookName,
      owner: action.payload.owner,
    };
  } if (action.type === types.UPDATE_SIDEPANEL_VISIBLE) {
    return {
      ...state,
      sidePanelVisible: action.payload.sidePanelVisible,
    };
  }

  return state;
};

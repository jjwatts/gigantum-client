export const persistPreferences = (state) => {
  const stateString = JSON.stringify(state);

  localStorage.setItem(stateString);
};

export const getPreferences = state => state.preferences;

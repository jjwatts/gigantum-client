// vendor
import React from 'react';
import classNames from 'classnames';
// assets
import './TrackingToggle.scss';

export default class TrackingToggle extends React.Component {
  state = {
    isTrackingOn: true,
  };

  /**
    @param {evt}
    updates trackingOn state
    updates parents state via setTracking prop
  */
  _toggleTrackingState(evt) {
    if ((evt.type === 'click') || (evt.key === 'Enter')) {
      const { props, state } = this;

      this.setState((prevState) => {
        return { isTrackingOn: !prevState.isTrackingOn };
      });

      props.setTracking(!state.isTrackingOn);
    }
  }

  render() {
    const { state } = this;
    const toggleCondition = classNames({
      TrackingToggle__label: true,
      'TrackingToggle__label--on': state.isTrackingOn,
      'TrackingToggle__label--off': !state.isTrackingOn,
    });

    const toggleCheckboxCondition = classNames({
      TrackingToggle__checkbox: true,
      'TrackingToggle__checkbox--on': state.isTrackingOn,
      'TrackingToggle__checkbox--off': !state.isTrackingOn,
    });

    const trackingState = state.isTrackingOn ? 'Enabled' : 'Disabled';

    return (
      <div
        className="TrackingToggle"
        onClick={evt => this._toggleTrackingState(evt)}
        onKeyUp={evt => this._toggleTrackingState(evt)}
        tabIndex="0"
        role="button"
      >
        <div className="TrackingToggle__text">
          Input/Output Version Tracking
          {` ${trackingState}`}
        </div>
        <span className={toggleCheckboxCondition}>

          <label
            className={toggleCondition}
            htmlFor="TrackingToggle__input"
          >
            <input
              data-on="&#x2714;"
              data-off="&#x2718;"
              id="TrackingToggle__input"
              className="TrackingToggle__input"
              type="checkbox"
              checked={state.isTrackingOn}
              onChange={() => state.isTrackingOn}
            />
          </label>
        </span>
      </div>
    );
  }
}

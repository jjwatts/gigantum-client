// vendor
import React from 'react';
import classNames from 'classnames';
// assets
import './TrackingToggle.scss';

export default class TrackingToggle extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isTrackingOn: true,
    };
  }

  /**
    @param {}
    updates trackingOn state
    updates parents state via setTracking prop
  */
  _toggleTrackingState() {
    const { state } = this;

    this.setState({ isTrackingOn: !state.isTrackingOn });

    this.props.setTracking(!state.isTrackingOn);
  }

  render() {
    const toggleCondition = classNames({
      TrackingToggle__label: true,
      'TrackingToggle__label--on': this.state.isTrackingOn,
      'TrackingToggle__label--off': !this.state.isTrackingOn,
    });

    const toggleCheckboxCondition = classNames({
      TrackingToggle__checkbox: true,
      'TrackingToggle__checkbox--on': this.state.isTrackingOn,
      'TrackingToggle__checkbox--off': !this.state.isTrackingOn,
    });

    const trackingState = this.state.isTrackingOn ? 'Enabled' : 'Disabled';
    return (
      <div
        className="TrackingToggle"
        onClick={() => this._toggleTrackingState()}
      >
        <div className="TrackingToggle__text">
          Input/Output Version Tracking
          {trackingState}
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
              checked={this.state.isTrackingOn}
              onChange={() => this.state.isTrackingOn}
            />
          </label>
        </span>
      </div>
    );
  }
}

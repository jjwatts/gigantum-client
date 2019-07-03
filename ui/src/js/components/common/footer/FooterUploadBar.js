// vendor
import React, { PureComponent } from 'react';
import classNames from 'classnames';
// assets
import './FooterUploadBar.scss';

export default class FooterUploadBar extends PureComponent {
  render() {
    const { props } = this;
    const footerUploadClass = classNames({
      hidden: !props.parentState.uploadOpen,
      'FooterUploadBar--status': props.parentState.uploadOpen,
      'FooterUploadBar--error': props.parentState.uploadError,
    });

    const isNotZero = props.parentState.progessBarPercentage !== 0;
    const footerUploadBarClass = classNames({
      FooterUploadBar__progressBar: true,
      'FooterUploadBar__progressBar--animation': isNotZero,
    });

    return (
      <div className={footerUploadClass}>
        <div className="FooterUploadBar__message">
          {props.parentState.uploadMessage}
        </div>

        <div
          id="footerProgressBar"
          style={{ width: `${props.parentState.progessBarPercentage}%` }}
          className={footerUploadBarClass}
        />

        {
          props.parentState.uploadError
          && (
          <div
            onClick={() => { props.closeFooter(); }}
            className="Footer__close"
          />
          )
        }
        {
          props.parentState.labbookSuccess
          && (
          <button onClick={() => props.openLabbook()}>
              Open Project
          </button>
          )
        }
      </div>
    );
  }
}

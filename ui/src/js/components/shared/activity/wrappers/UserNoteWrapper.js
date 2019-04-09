// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import Tooltip from 'Components/common/Tooltip';
import UserNote from '../UserNote';
// assets
import './UserNoteWrapper.scss';

export default class UserNoteWrapper extends Component {
  constructor(props) {
  	super(props);
    this.state = {
      userNoteVisible: false,
    };

    this._toggleUserNote = this._toggleUserNote.bind(this);
  }

  /**
  *   @param {boolean} value
  *   sets state to show hide usernote
  *   @return {}
  */
  _toggleUserNote(userNoteVisible) {
    this.setState({ userNoteVisible });
  }

  render() {
    const { props, state } = this;


    const userActivityContainerCSS = classNames({
      UserNote__container: true,
      'UserNote__container--open': state.userNoteVisible,
      fullscreen: props.editorFullscreen,
    });


    const userNoteCardCSS = classNames({
      'UserNote__add UserNote__card column-1-span-10': true,
      hidden: !state.userNoteVisible,
    });


    const buttonCSS = classNames({
      'Btn Btn--feature Btn--feature--expanded--paddingLeft relative UserNote__button': true,
      'UserNote__button--close': state.userNoteVisible,
    });
    return (
      <div className={userActivityContainerCSS}>
        <Tooltip section="userNote" />
        <button
          className={buttonCSS}
          onClick={() => this._toggleUserNote(!state.userNoteVisible)}
          type="submit"
        >
          Add Note
        </button>
        <div className={userNoteCardCSS}>
          { state.userNoteVisible
            && (
            <UserNote
              toggleUserNote={this._toggleUserNote}
              key="UserNote"
              {...props}
            />
            )
          }
        </div>
      </div>
    );
  }
}

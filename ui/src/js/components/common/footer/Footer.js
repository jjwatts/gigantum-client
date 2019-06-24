// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
import { connect } from 'react-redux';
import { boundMethod } from 'autobind-decorator';
// store
import {
  setUpdateMessageStackItemVisibility,
  setUpdateHistoryStackItemVisibility,
  setResizeFooter,
  setUploadMessageRemove,
  setResetFooter,
  setRemoveMessage,
  setToggleMessageList,
} from 'JS/redux/actions/footer';
import { setPauseUpload } from 'JS/redux/actions/shared/fileBrowser/fileBrowserWrapper';
// // components
import FooterNotificationList from './FooterNotificationList';
import FooterUploadBar from './FooterUploadBar';
// assets
import './Footer.scss';

class Footer extends Component {
  /**
    subscribe to store to update state
  */
  componentDidMount() {
    window.addEventListener('resize', this._resize);
  }

  /**
   hides messages in stack after 15 seconds
  */
  componentDidUpdate() {
    const { props } = this;
    props.messageStack.forEach((messageItem) => {
      const timeInSeconds = 15 * 1000;
      if (!messageItem.error) {
        if (!messageItem.isMultiPart || (messageItem.isMultiPart && messageItem.isLast)) {
          setTimeout(() => {
            this._removeMessage(messageItem);
          }, timeInSeconds);
        }
      }
    });
  }

  /**
    unsubscribe from event listeners
  */
  componentWillUnmount() {
    window.removeEventListener('resize', this._resize);
  }

  /**
    @param {} -
    opens project in view
  */
  @boundMethod
  _openLabbook() {
    const { props } = this;
    this._clearState();
    props.history.replace(`/projects/${props.labbookName}`);
  }

  /**
    @param {}
    add scroll listener to pop up footer
  */
  @boundMethod
  _clearState() {
    const { props } = this;
    document.getElementById('footerProgressBar').style.opacity = 0;
    props.setResetFooter();

    setTimeout(() => {
      document.getElementById('footerProgressBar').style.width = '0%';
      setTimeout(() => {
        document.getElementById('footerProgressBar').style.opacity = 1;
      }, 1000);
    }, 1000);
  }

  /**
   @param {}
   stops user and pops a modal prompting them to cancel continue or save changes
  */
  _pauseUpload() {
    setPauseUpload(true);
  }

  /**
    @param {}
    gets upload message which tracks progess
  */
  _closeFooter() {
    setUploadMessageRemove('', '', 0);
  }

  /**
    @param {object} messageItem
    gets upload message which tracks progess
  */
  _removeMessage(messageItem) {
    setRemoveMessage(messageItem.id);
  }

  /**
    @param {}
    toggles messages list to collapsed or expanded
    updates redux store
    @return {}
  */
  @boundMethod
  _toggleMessageList() {
    const { props } = this;
    props.setToggleMessageList(!props.messageListOpen, true);
  }

  /**
    @param {number}
    toggles view of message body for a stack item
    updates redux store
    @return {}
   */
   @boundMethod
  _showMessageBody(index) {
    const { props } = this;
    if (!props.viewHistory) {
      props.setUpdateMessageStackItemVisibility(index);
    } else {
      props.setUpdateHistoryStackItemVisibility(index);
    }
  }

  /**
    * @param {}
    * update store to risize component
  */
  @boundMethod
  _resize() {
    const { props } = this;
    props.setResizeFooter();
  }

  render() {
    const { props, state } = this;
    const bodyWidth = document.body.clientWidth;

    const footerClass = classNames({
      Footer: true,
      'Footer--uploading': props.uploadOpen,
      'Footer--expand': (props.open) || props.uploadOpen,
      'Footer--expand-extra': (props.open && props.uploadOpen),

    });
    const footerButtonClass = classNames({
      'Footer__disc-button': true,
      'Footer__disc-button--open': props.messageListOpen,
      'Footer__dist-button--side-view': bodyWidth < 1600,
      'Footer__disc-button--helper-open': props.helperVisible,
      'Footer__disc-button--bottom': !props.messageListOpen && props.uploadOpen,
    });

    return (
      <div className="Footer__container">
        <div id="footer" className={footerClass}>

          <FooterNotificationList
            showMessageBody={this._showMessageBody}
            parentState={this.props}
            toggleMessageList={this._toggleMessageList}
          />

          <FooterUploadBar
            closeFooter={this._closeFooter}
            openLabbook={this._openLabbook}
            parentState={this.props}
          />

          <div
            onClick={() => this._toggleMessageList()}
            className={footerButtonClass}
          />

        </div>
      </div>
    );
  }
}

const mapStateToProps = state => state.footer;

const mapDispatchToProps = dispatch => ({
  setUpdateMessageStackItemVisibility,
  setUpdateHistoryStackItemVisibility,
  setResizeFooter,
  setUploadMessageRemove,
  setResetFooter,
  setRemoveMessage,
  setToggleMessageList,
});

export default connect(mapStateToProps, mapDispatchToProps)(Footer);

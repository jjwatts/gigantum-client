// vendor
import React from 'react';
import uuidv4 from 'uuid/v4';
// utilities
import validation from 'JS/utils/Validation';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// store
import { setMultiInfoMessage } from 'JS/redux/reducers/footer';
// components
import LoginPrompt from 'Components/shared/modals/LoginPrompt';
// assets
import './CreateLabbook.scss';

export default class CreateLabbook extends React.Component {
  constructor(props) {
  	super(props);

  	this.state = {
      name: '',
      description: '',
      showError: false,
      errorType: '',
      remoteURL: '',
      textWarning: 'CreateLabbook__warning--green',
      textLength: 80,
      isUserValid: false,
      showLoginPrompt: false,
    };

    this.continueSave = this.continueSave.bind(this);
    this._updateTextState = this._updateTextState.bind(this);
    this._updateRemoteUrl = this._updateRemoteUrl.bind(this);
    this._closeLoginPromptModal = this._closeLoginPromptModal.bind(this);
  }

  /**
  *   @param {Object} evt
  *   takes an event input
  *   creates a labbook mutation sets labbook name on parent component
  *   triggers setComponent to proceed to next view
  * */
  continueSave = (evt) => {
    const { name, description } = this.state;
    if (this.state.remoteURL.length > 0) {
    } else {
      this.props.createLabbookCallback(name, description);
    }
  }

  /**
  *  @param {}
  *  closes login prompt modal
  *  @return {}
  */
  _closeLoginPromptModal() {
    this.setState({
      showLoginPrompt: false,
    });
  }

  /**
    @param {Object, string} evt,field
    updates text in a state object and passes object to setState method
  */
  _updateTextState = (evt, field) => {
    const state = {};

    state[field] = evt.target.value;
    if (field === 'name') {
      const isMatch = validation.labbookName(evt.target.value);
      this.setState({
        showError: ((isMatch === false) && (evt.target.value.length > 0)),
        errorType: '',
      });

      this.props.toggleDisabledContinue((evt.target.value === '') || (isMatch === false));
    } else {
      const textLength = 80 - evt.target.value.length;
      if (textLength > 21) {
        state.textWarning = 'CreateLabbook__warning--green';
      } else if ((textLength <= 21)) {
        state.textWarning = 'CreateLabbook__warning--orange';
      }
      state.textLength = textLength;
    }

    this.setState(state);
  }


  /**
    @param {}
    returns error message
    @return {string} errorMessage
  */
  _getErrorText() {
    return this.state.errorType === 'send' ? 'Error: Last character cannot be a hyphen.' : 'Error: Title may only contain lowercase alphanumeric and `-`. (e.g. lab-book-title)';
  }

  /**
    @param {event} evt
    updates remote url state
  */
  _updateRemoteUrl(evt) {
    this.setState({
      remoteURL: evt.target.value,
    });
    if (evt.target.value.length > 0) {
      this.props.toggleDisabledContinue(false);
    } else {
      this.props.toggleDisabledContinue(true);
    }
  }

  render() {
    return (
      <div className="CreateLabbook">
        {
          this.state.showLoginPrompt
          && <LoginPrompt closeModal={this._closeLoginPromptModal} />
        }
        <div>
          <div className="CreateLabbook__name">
            <label htmlFor="CreateLabbookName">
              Title
              <input
                id="CreateLabbookName"
                type="text"
                maxLength="36"
                className={this.state.showError ? 'invalid' : ''}
                onChange={evt => this._updateTextState(evt, 'name')}
                placeholder="Enter a unique, descriptive title"
              />
            </label>
            <span className={this.state.showError ? 'error' : 'hidden'}>{this._getErrorText()}</span>
          </div>

          <div className="CreateLabbook__description">
            <label htmlFor="CreateLabbookDescription">
              Description
              <textarea
                id="CreateLabbookDescription"
                maxLength="80"
                className="CreateLabbook__description-input"
                type="text"
                onChange={evt => this._updateTextState(evt, 'description')}

                placeholder={`Briefly describe this ${this.props.datasets ? 'Dataset' : 'Project'}, its purpose and any other key details.`}
              />
            </label>

            <p className={`CreateLabbook__warning ${this.state.textWarning}`}>{`${this.state.textLength} characters remaining`}</p>
          </div>

        </div>
      </div>
    );
  }
}

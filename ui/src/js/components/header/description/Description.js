// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import ToolTip from 'Components/shared/ToolTip';
// mutations
import SetLabbookDescriptionMutation from 'Mutations/SetLabbookDescriptionMutation';
// store
import store from 'JS/redux/store';
// assets
import './Description.scss';

export default class Description extends Component {
  constructor(props) {
    super(props);
    this.state = {
      editingDescription: false,
      descriptionText: this.props.description ? this.props.description.replace(/\n/g, ' ') : '',
      lastSavedDescription: this.props.description ? this.props.description.replace(/\n/g, ' ') : '',
      savingDescription: false,
      hovered: false,
      textareaWidth: '270px',
      textareaHeight: '66px',
    };
    this._handleClick = this._handleClick.bind(this);
    this._saveDescription = this._saveDescription.bind(this);
    this._cancelDescription = this._cancelDescription.bind(this);
  }
  /*
    adds event listeners
  */
  componentDidMount() {
    window.addEventListener('click', this._handleClick);
  }
  /*
    removes event listeners
  */
  componentWillUnmount() {
    window.removeEventListener('click', this._handleClick);
  }
  /**
    *  @param {event} evt
    handles click outside description
  */
  _handleClick(evt) {
    if (evt.target.className.indexOf('Description') === -1 && this.state.editingDescription) {
      this._cancelDescription();
    }
  }
  /**
    *  @param {}
    *  fires setlabbookdescription mutation
  */
  _saveDescription() {
    const { owner, labbookName } = store.getState().routes;
    this.setState({ savingDescription: true });
    SetLabbookDescriptionMutation(
      owner,
      labbookName,
      this.state.descriptionText.replace(/\n/g, ' '),
      (res, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('Description was not set: ', error);
        } else {
          this.setState({ editingDescription: false, savingDescription: false, lastSavedDescription: this.state.descriptionText.replace(/\n/g, ' ') });
        }
      },
    );
  }
  /**
    *  @param {}
    *  reverts description back to last save
  */
  _cancelDescription() {
    this.setState({ editingDescription: false, descriptionText: this.state.lastSavedDescription });
  }
  /**
    *  @param {}
    *  handles enabling description editing and sets textareaCSS
  */
  _editingDescription() {
    if (!this.state.editingDescription) {
      let element = document.getElementsByClassName('Description__container')[0];
      let width = element.offsetWidth - 30;
      let height = element.offsetHeight - 4;
      this.setState({ editingDescription: true, textareaWidth: `${width}px`, textareaHeight: `${height}px` });
    }
  }

  render() {
    const descriptionCSS = classNames({
      Description__text: true,
      empty: !this.state.descriptionText,
    });

    const descriptionContainerCSS = classNames({
      Description__container: true,
      'Description__container--hovered': this.state.hovered && !this.state.editingDescription,
      'visibility-hidden': this.props.hovered,
    });
    const displayedText = this.state.descriptionText && this.state.descriptionText.length ? this.state.descriptionText : 'Add description...';
    const defaultText = this.state.descriptionText ? this.state.descriptionText : '';
    const textareaStyle = {
      height: this.state.textareaHeight,
      width: this.state.textareaWidth,
    };

    return (
     <div className="Description">

            <div className={descriptionContainerCSS}
                onMouseEnter={() => this.setState({ hovered: true })}
                onMouseLeave={() => this.setState({ hovered: false })}
                onClick={() => this._editingDescription()}
            >

            {
                this.state.editingDescription ?
                  <Fragment>
                    <textarea
                        maxLength="260"
                        className="Description__input"
                        type="text"
                        style={textareaStyle}
                        onChange={(evt) => { this.setState({ descriptionText: evt.target.value.replace(/\n/g, ' ') }); }}
                        onKeyDown={(evt) => {
                            if (evt.key === 'Enter') {
                                this.setState({ editingDescription: false });
                                this._saveDescription();
                            }
                        }}
                        placeholder="Short description of Project"
                        defaultValue={defaultText}
                    />
                    <div
                      className="Description__input-buttons"
                      style={{ height: this.state.textareaHeight }}
                    >
                        <button
                          onClick={this._cancelDescription}
                          className="Description__input-cancel"
                        />
                        <button
                          onClick={this._saveDescription}
                          className="Description__input-save"
                        />
                    </div>
                  </Fragment>
                :
                    <p className={descriptionCSS}>
                        {displayedText}
                        {
                            this.state.hovered &&
                            <button
                                className="Description__edit-button"
                            />
                        }
                    </p>
            }
            </div>
        <ToolTip section="descriptionOverview" />
     </div>
    );
  }
}

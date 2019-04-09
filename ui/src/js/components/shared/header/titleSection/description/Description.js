// vendor
import React, { Component, Fragment } from 'react';
import classNames from 'classnames';
// components
import Tooltip from 'Components/common/Tooltip';
// mutations
import SetLabbookDescriptionMutation from 'Mutations/SetLabbookDescriptionMutation';
import SetDatasetDescriptionMutation from 'Mutations/SetDatasetDescriptionMutation';
// store
import store from 'JS/redux/store';
// assets
import './Description.scss';

export default class Description extends Component {
  constructor(props) {
    super(props);
    this.state = {
      editingDescription: false,
      descriptionEdited: false,
      descriptionText: props.description ? props.description.replace(/\n/g, ' ') : '',
      lastSavedDescription: props.description ? props.description.replace(/\n/g, ' ') : '',
      savingDescription: false,
      hovered: false,
      textareaWidth: '270px',
      textareaHeight: '66px',
    };
    this._handleClick = this._handleClick.bind(this);
    this._saveDescription = this._saveDescription.bind(this);
    this._cancelDescription = this._cancelDescription.bind(this);
  }

  static getDerivedStateFromProps(nextProps, state) {
    return {
      ...state,
      descriptionText: state.descriptionEdited ? state.descriptionText : nextProps.description,
    };
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
    const { state } = this;
    if ((evt.target.className.indexOf('Description') === -1) && state.editingDescription) {
      this._cancelDescription();
    }
  }

  /**
   @param {String} owner
   @param {String} labbookName
   calls mutation to save labbook description
   */
  _saveLabbookDescription(owner, labbookName) {
    const { props, state } = this;
    const sectionId = props[props.sectionType].id;
    SetLabbookDescriptionMutation(
      owner,
      labbookName,
      state.descriptionText,
      sectionId,
      (res, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('Description was not set: ', error);
        } else {
          this.setState({
            descriptionEdited: false,
            editingDescription: false,
            savingDescription: false,
            lastSavedDescription: state.descriptionText.replace(/\n/g, ' '),
          });
        }
      },
    );
  }

  /**
   @param {String} owner
   @param {String} labbookName
   calls mutation to save dataset description
   */
  _saveDatasetDescription(owner, labbookName) {
    const { props, state } = this;
    const sectionId = props[props.sectionType].id;
    SetDatasetDescriptionMutation(
      owner,
      labbookName,
      state.descriptionText,
      sectionId,
      (res, error) => {
        if (error) {
          console.log(error);
          setErrorMessage('Description was not set: ', error);
        } else {
          this.setState({
            descriptionEdited: false,
            editingDescription: false,
            savingDescription: false,
            lastSavedDescription: state.descriptionText.replace(/\n/g, ' '),
          });
        }
      },
    );
  }

  /**
    *  @param {}
    *  fires setlabbookdescription mutation
  */
  _saveDescription() {
    const { props } = this;
    const { owner, labbookName } = store.getState().routes;
    this.setState({ savingDescription: true });
    if (props.sectionType === 'labbook') {
      this._saveLabbookDescription(owner, labbookName);
    } else {
      this._saveDatasetDescription(owner, labbookName);
    }
  }

  /**
    *  @param {}
    *  reverts description back to last save
  */
  _cancelDescription() {
    const { state } = this;
    this.setState({
      descriptionEdited: false,
      editingDescription: false,
      descriptionText: state.lastSavedDescription,
    });
  }

  /**
    *  @param {}
    *  handles enabling description editing and sets textareaCSS
  */
  _editingDescription() {
    const { state } = this;
    if (!state.editingDescription) {
      const element = document.getElementsByClassName('Description__container')[0];
      const width = element.offsetWidth - 30;
      const height = element.offsetHeight - 4;
      this.setState({ editingDescription: true, textareaWidth: `${width}px`, textareaHeight: `${height}px` }, () => {
        this.descriptionInput.focus();
      });
    }
  }

  /**
    *  @param {}
    *  handles enabling description editing and sets textareaCSS
  */
  _updateDescrtipionText(evt) {
    this.setState({
      descriptionText: evt.target.value.replace(/\n/g, ' '),
      descriptionEdited: true,
    });
  }

  render() {
    const { props, state } = this;


    const descriptionCSS = classNames({
      Description__text: true,
      empty: !state.descriptionText,
    });


    const descriptionContainerCSS = classNames({
      Description__container: true,
      'Description__container--hovered': state.hovered && !state.editingDescription,
      'visibility-hidden': props.hovered,
    });


    const displayedText = state.descriptionText && state.descriptionText.length ? state.descriptionText : 'Add description...';


    const defaultText = state.descriptionText ? state.descriptionText : '';

    return (
      <div className="Description">

        <div
          className={descriptionContainerCSS}
          onMouseEnter={() => this.setState({ hovered: true })}
          onMouseLeave={() => this.setState({ hovered: false })}
          onClick={() => this._editingDescription()}
        >

          {
                state.editingDescription
                  ? (
                    <Fragment>
                      <textarea
                        ref={(input) => { this.descriptionInput = input; }}
                        maxLength="80"
                        className="Description__input"
                        type="text"
                        onChange={(evt) => { this._updateDescrtipionText(evt); }}
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
                        style={{ height: state.textareaHeight }}
                      >
                        <button
                          onClick={this._cancelDescription}
                          className="Description__input-cancel Btn Btn--noMargin"
                        />
                        <button
                          onClick={this._saveDescription}
                          className="Description__input-save Btn Btn--noMargin"
                        />
                      </div>
                    </Fragment>
                  )
                  : (
                    <p className={descriptionCSS}>
                      {displayedText}
                      { state.hovered
                          && <button className="Description__edit-button" />
                        }
                    </p>
                  )
            }
        </div>
        <Tooltip section="descriptionOverview" />
      </div>
    );
  }
}

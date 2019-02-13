// vendor
import React, { Component } from 'react';
import { WithContext as ReactTags } from 'react-tag-input';
// mutations
import CreateUserNoteMutation from 'Mutations/CreateUserNoteMutation';
// store
import store from 'JS/redux/store';
// assets
import './UserNote.scss';

let simple;

export default class UserNote extends Component {
  constructor(props) {
  	super(props);
    this.state = {
      tags: [],
      userSummaryText: '',
      addNoteDisabled: true,
      editorFullscreen: false,
    };

    this._addNote = this._addNote.bind(this);
    this._handleDelete = this._handleDelete.bind(this);
    this._handleAddition = this._handleAddition.bind(this);
    this._handleDrag = this._handleDrag.bind(this);
  }

  /**
    @param {}
    after component mounts apply simplemde to the dom element id:markdown
  */
  componentDidMount() {
    const { props } = this;

    import('simplemde').then((comp) => {
      if (document.getElementById('markDown')) {
        const Simple = comp.default;
        simple = new Simple({
          element: document.getElementById('markDown'),
          spellChecker: true,
        });
        const fullscreenButton = document.getElementsByClassName('fa-arrows-alt')[0];
        fullscreenButton && fullscreenButton.addEventListener('click', () => props.changeFullScreenState());
        const sideBySideButton = document.getElementsByClassName('fa-columns')[0];
        sideBySideButton && sideBySideButton.addEventListener('click', () => props.changeFullScreenState(true));
      }
    });
  }

  /**
    @param {}
    calls CreateUserNoteMutation adds note to activity feed
  */
  _addNote = () => {
    const { props, state } = this;
    const tags = state.tags.map(tag => (tag.text));
    const { labbookName, owner } = store.getState().routes;
    const { labbookId } = props;

    this.setState({ addNoteDisabled: true });
    CreateUserNoteMutation(
      props.sectionType,
      labbookName,
      state.userSummaryText,
      simple.value(),
      owner,
      [],
      tags,
      labbookId || props.datasetId,
      (response, error) => {
        props.toggleUserNote(false);
        this.setState({
          tags: [],
          userSummaryText: '',
          addNoteDisabled: false,
        });
      },
    );
  }

  /**
    @param {object} event
    calls updates state for summary text
    and enables addNote button if > 0
  */
  _setUserSummaryText(evt) {
    const summaryText = evt.target.value;
    this.setState({
      userSummaryText: summaryText,
      addNoteDisabled: (summaryText.length === 0),
    });
  }

  /**
    @param {number} i
    removes tag from list
  */
   _handleDelete = (i) => {
     const { tags } = this.state;

     tags.splice(i, 1);

     this.setState({ tags });
   }

   /**
     @param {number} i
     add tag to list
   */
   _handleAddition = (tag) => {
     const { tags } = this.state;
     tags.push(tag);
     this.setState(tags);
   }

   /**
     @param {number} i
     drags tag to new position.
   */
   _handleDrag = (tag, currPos, newPos) => {
     const { tags } = this.state;

     // mutate array
     tags.splice(currPos, 1);
     tags.splice(newPos, 0, tag);

     // re-render
     this.setState({ tags });
   }


   render() {
     const { state } = this;
     const { tags } = state;
     return (
       <div className="UserNote flex flex--column">
         <input
           type="text"
           placeholder="Add a summary title"
           onKeyUp={evt => this._setUserSummaryText(evt)}
           className="UserNote__title"
         />

         <textarea
           ref="markdown"
           className="UserNote__summary"
           id="markDown"
         />

         <ReactTags
           id="TagsInput"
           tags={tags}
           handleDelete={(index) => { this._handleDelete(index); }}
           handleAddition={(tag) => { this._handleAddition(tag); }}
           handleDrag={(tag, currPos, newPos) => { this._handleDrag(tag, currPos, newPos); }}
         />

         <button
          type="submit"
           className="UserNote__add-note"
           disabled={state.addNoteDisabled}
           onClick={() => { this._addNote(); }}>
           Add Note
         </button>
       </div>
     );
   }
}

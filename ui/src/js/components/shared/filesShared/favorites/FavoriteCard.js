// vendor
import React, { Component } from 'react';
import { DragSource, DropTarget } from 'react-dnd';
import { findDOMNode } from 'react-dom';
import classNames from 'classnames';
import TextTruncate from 'react-text-truncate';
// Mutations
import RemoveFavoriteMutation from 'Mutations/fileBrowser/RemoveFavoriteMutation';
import UpdateFavoriteMutation from 'Mutations/fileBrowser/UpdateFavoriteMutation';
// store
import store from 'JS/redux/store';
// assets
import '../FileCard.scss';


const cardSource = {
  beginDrag(props, monitor, component) {
    return {
      id: props.id,
      index: props.index,
    };
  },
};

const cardTarget = {
  hover(props, monitor, component) {
    const dragIndex = monitor.getItem().index;
    const hoverIndex = props.index;

    // Don't replace items with themselves
    if (dragIndex === hoverIndex) {
      return;
    }

    // Determine rectangle on screen
    const hoverBoundingRect = findDOMNode(component).getBoundingClientRect();

    // Get vertical middle
    const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;

    // Determine mouse position
    const clientOffset = monitor.getClientOffset();

    // Get pixels to the top
    const hoverClientY = clientOffset.y - hoverBoundingRect.top;

    // Only perform the move when the mouse has crossed half of the items height
    // When dragging downwards, only move when the cursor is below 50%
    // When dragging upwards, only move when the cursor is above 50%

    // Dragging downwards
    if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
      return;
    }

    // Dragging upwards
    if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
      return;
    }

    // Time to actually perform the action
    props.moveCard(dragIndex, hoverIndex);

    // Note: we're mutating the monitor item here!
    // Generally it's better to avoid mutations,
    // but it's good here for the sake of performance
    // to avoid expensive index searches.
    monitor.getItem().index = hoverIndex;
  },
  drop(props, monitor, component) {
    const newIndex = props.index;
    component._updateIndexMutation(newIndex);
  },
};

function collect(connect, monitor) {
  return {
    connectDragSource: connect.dragSource(),
  };
}
function collectDropTarget(connect, monitor) {
  return {
    connectDropTarget: connect.dropTarget(),
    isOverCurrent: monitor.isOver({ shallow: true }),
  };
}

class FavoriteCard extends Component {
  constructor(props) {
  	super(props);

    const { owner, labbookName } = store.getState().routes;

    this.state = {
      editMode: false,
      newDescription: '',
      owner,
      labbookName,
    };

    this._updateIndexMutation = this._updateIndexMutation.bind(this);
    this._removeFavorite = this._removeFavorite.bind(this);
  }

  /**
		@param {number} newIndex
		sets editMode to true or false
		displays textarea if true
	*/
  _updateIndexMutation(newIndex) {
    const { props, state } = this;
    UpdateFavoriteMutation(
      props.connection,
      props.parentId,
      state.owner,
      state.labbookName,
      props.favorite.id,
      props.favorite.key,
      props.favorite.description,
      newIndex,
      props.favorite,
      props.section,
      (response, error) => {
        if (error) {
          console.error(error);
        }
      },
    );
  }

  /**
    @param {boolean} value
    sets editMode to true or false
    displays textarea if true
  */
  _editDescription(value) {
    this.setState({ editMode: value });
  }

  /**
    @param {event, string} evt,key
    triggers add favorite mutation on key ENTER
    hides editMode
  */
  _updateDescription(evt, favorite) {
    const { props, state } = this;
    const filepath = favorite.key.replace(`${this.props.section}/`, '');

    if (evt.type === 'keyup') {
      this.setState({ newDescription: evt.target.value });
    }

    if (evt.keyCode === 13 || evt.type === 'click') {
      UpdateFavoriteMutation(
        props.connection,
        props.parentId,
        state.owner,
        state.labbookName,
        favorite.id,
        filepath,
        state.newDescription,
        favorite.index,
        favorite,
        props.section,
        (response, error) => {
          if (error) {
            console.error(error);
          }
        },
      );
      this._editDescription(false);
    }
  }

  /**
    @param {Object} node
    triggers remove favorite mutation
  */
  _removeFavorite(node) {
    const { props, state } = this;
    RemoveFavoriteMutation(
      props.connection,
      props.parentId,
      state.owner,
      state.labbookName,
      props.section,
      node.key,
      node.id,
      node,
      (response, error) => {
        if (error) {
          console.error(error);
        }
      },
    );
  }

  /**
    @param {}
    sets description to edit mode on double click
  */
  _handleClickDescription() {
    this._editDescription(true);
  }

  render() {
    const { props, state } = this;
    const fileDirectories = props.favorite.key.split('/');
    const filename = fileDirectories[fileDirectories.length - 1];
    const path = `${props.section}/${props.favorite.key.replace(filename, '')}`;

    const {
	    connectDragSource,
      connectDropTarget,
      isDragging,
  	} = props;

    const favoriteCardCSS = classNames({
      'FileCard Card': true,
      'FileCard--opaque Card': !(props.favorite.index !== undefined),
      'column-3-span-4--shrink': true,
      'FileCard-hidden': props.isOverCurrent,
      'FileCard--isDragging': isDragging,
    });

    const favoriteMaskCSS = classNames({
      FileCard__mask: true,
      hidden: (props.favorite.index !== undefined),
    });
    return (
      connectDragSource(connectDropTarget(<div className={favoriteCardCSS}>
        <div
          onClick={() => { this._removeFavorite(props.favorite); }}
          className="FileCard__star"
        />
        <h6 className="FileCard__header">
          <TextTruncate
            className="FileCard__header"
            line={1}
            truncateText="…"
            text={filename}
          />
        </h6>

        <p className="FileCard__path">{path}</p>


        { !state.editMode && (props.favorite.description.length > 0)
          && (
          <p className="FileCard__description">
            {props.favorite.description}
            <button
              onClick={() => this._editDescription(true)}
              className="FileCard__edit-button"
            />
          </p>
          )
        }

        { (!state.editMode && (props.favorite.description.length < 1))
          && (
          <p
            onDoubleClick={() => this._handleClickDescription()}
            className="FileCard__description-filler"
          >
            Enter a short description
            <button
              onClick={() => this._editDescription(true)}
              className="FileCard__edit-button"
            />
          </p>
          )
        }

        { state.editMode
            && (
            <div className="flex justify--space-between">
              <textarea
                maxLength="140"
                className="FileCard__description-editor"
                onKeyUp={evt => this._updateDescription(evt, props.favorite)}
                placeholder={props.favorite.description}
              >
                {props.favorite.description}
              </textarea>

              <div className="flex flex--column-reverse justify--space-around align-items--center">
                <button
                  onClick={() => this._editDescription(false)}
                  className="Btn Btn--round Btn--medium Btn__close"
                />
                <button
                  onClick={(evt) => { this._updateDescription(evt, props.favorite); }}
                  className="Btn Btn--round Btn--medium Btn__check"
                />
              </div>
            </div>
            )
	        }

        <div className={favoriteMaskCSS} />

      </div>))
    );
  }
}
const DropTargetContainer = DropTarget('Card', cardTarget, collectDropTarget)(FavoriteCard);

export default DragSource('Card', cardSource, collect)(DropTargetContainer);

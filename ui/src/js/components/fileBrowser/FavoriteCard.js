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

  /*
		@param {number} newIndex
		sets editMode to true or false
		displays textarea if true
	*/
  _updateIndexMutation(newIndex) {
    UpdateFavoriteMutation(
      this.props.connection,
      this.props.parentId,
      this.state.owner,
      this.state.labbookName,
      this.props.favorite.id,
      this.props.favorite.key,
      this.props.favorite.description,
      newIndex,
      this.props.favorite,
      this.props.section,
      (response, error) => {
        if (error) {
          console.error(error);
        }
      },
    );
  }

  /*
    @param {boolean} value
    sets editMode to true or false
    displays textarea if true
  */
  _editDescription(value) {
    this.setState({ editMode: value });
  }
  /*
    @param {event, string} evt,key
    triggers add favorite mutation on key ENTER
    hides editMode
  */
  _updateDescription(evt, favorite) {
    const filepath = favorite.key.replace(`${this.props.section}/`, '');

    if (evt.type === 'keyup') {
      this.setState({ newDescription: evt.target.value });
    }

    if (evt.keyCode === 13 || evt.type === 'click') {
      UpdateFavoriteMutation(
        this.props.connection,
        this.props.parentId,
        this.state.owner,
        this.state.labbookName,
        favorite.id,
        filepath,
        this.state.newDescription,
        favorite.index,
        favorite,
        this.props.section,
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
    RemoveFavoriteMutation(
      this.props.connection,
      this.props.parentId,
      this.state.owner,
      this.state.labbookName,
      this.props.section,
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
    const fileDirectories = this.props.favorite.key.split('/');
    const filename = fileDirectories[fileDirectories.length - 1];
    const path = `${this.props.section}/${this.props.favorite.key.replace(filename, '')}`;

    const {
	    connectDragSource,
      connectDropTarget,
      isDragging,
  	} = this.props;

    const favoriteCardCSS = classNames({
      'Favorite__card Card': (this.props.favorite.index !== undefined),
      'Favorite__card--opaque Card': !(this.props.favorite.index !== undefined),
      'column-3-span-4': true,
      'Favorite__card--hidden': this.props.isOverCurrent,
      'Favorite__card--isDragging': isDragging,
    });
    return (
      connectDragSource(connectDropTarget(<div
        className={favoriteCardCSS}>
        <div
          onClick={() => { this._removeFavorite(this.props.favorite); }}
          className="Favorite__star"
        />
        <div className="Favorite__header-section">
          <h6 className="Favorite__card-header">
            <TextTruncate
                className="Favorite__card-header"
                line={1}
                truncateText="…"
                text={filename}
            />
          </h6>
        </div>

        <div className="Favorite__path-section">
          <p className="Favorite__path">{path}</p>
        </div>

        <div className="Favorite__description-section">

          { !this.state.editMode && (this.props.favorite.description.length > 0) &&

          <p className="Favorite__description">{this.props.favorite.description} <button
                                                                                   onClick={() => this._editDescription(true)}
                                                                                   className="Favorite__edit-button" />
          </p>
	            }

          { !this.state.editMode && (this.props.favorite.description.length < 1) &&

          <p
            onDoubleClick={() => this._handleClickDescription()}
            className="Favorite__description-filler">
            Enter a short description <button
                                        onClick={() => this._editDescription(true)}
                                        className="Favorite__edit-button" />
          </p>
	            }

          {
	              this.state.editMode &&
                <div className="Favorite__edit flex justify--space-between">
  	              <textarea
                    maxLength="140"
                    className="Favorite__description-editor"
                    onKeyUp={evt => this._updateDescription(evt, this.props.favorite)}
                    placeholder={this.props.favorite.description}>
                    {this.props.favorite.description}
  	              </textarea>

                  <div className="flex justify--space-around align-items--center">
                    <button
                      onClick={() => this._editDescription(false)}
                      className="Btn Btn--round Btn--close" />
                    <button
                      onClick={(evt) => { this._updateDescription(evt, this.props.favorite); }}
                      className="Btn Btn--round Btn--check" />
                  </div>
                </div>
	            }

          <div className={(this.props.favorite.index !== undefined) ? 'Favorite__mask hidden' : 'Favorite__mask'} />

        </div>

      </div>))
    );
  }
}
const DropTargetContainer = DropTarget('Card', cardTarget, collectDropTarget)(FavoriteCard);

export default DragSource('Card', cardSource, collect)(DropTargetContainer);

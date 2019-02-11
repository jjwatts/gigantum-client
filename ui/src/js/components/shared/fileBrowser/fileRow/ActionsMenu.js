// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './ActionsMenu.scss';

export default class ActionsMenu extends Component {
  constructor(props) {
  	super(props);
  	this._closePopup = this._closePopup.bind(this);
    this._setWrapperRef = this._setWrapperRef.bind(this);
  }

  state = {
    popupVisible: false,
  }
  /**
  *  LIFECYCLE MEHTODS START
  */
  componentDidMount() {
    window.addEventListener('click', this._closePopup);
  }

  componentWillMount() {
    window.removeEventListener('click', this._closePopup);
  }
  /**
  *  LIFECYCLE MEHTODS END
  */

  /**
  *  @param {}
  *  triggers favoirte unfavorite mutation
  *  @return{ }
  */
  _triggerFavoriteMutation() {
     const data = {
      key: this.props.edge.node.key,
      edge: this.props.edge,
     };

     if (this.props.edge.node.isFavorite) {
       this.props.mutations.removeFavorite(data, (response) => {
       });
     } else {
       this.props.mutations.addFavorite(data, (response) => {
       });
     }
  }

  /**
  *  @param {Object} event
  *  closes popup when clicking
  *  @return {}
  */
  _closePopup(evt) {
    if (this.state.popupVisible && this[this.props.edge.node.id] && !this[this.props.edge.node.id].contains(evt.target)) {
      this.setState({ popupVisible: false });
    }
  }

  /**
  *  @param {Obect} evt
  *  @param {boolean} popupVisible - boolean value for hiding and showing popup state
  *  triggers favoirte unfavorite mutation
  *  @return {}
  */
  _togglePopup(evt, popupVisible) {
    if (!popupVisible) {
      evt.stopPropagation(); // only stop propagation when closing popup, other menus won't close on click if propagation is stopped
    }
    this.setState({ popupVisible });
  }
  /**
  *  @param {Object} data - event from clicking delete button
  *  triggers DeleteLabbookFileMutation
  *  @return {}
  */
  _getEdges(data) {
    let edges = [data.edge];
    function getEdges(data) {
      Object.keys(data).forEach((name) => {
        edges.push(data[name].edge);
        if (data[name].children) {
          getEdges(data[name].children);
        }
      });
      return edges;
    }
    if (data.children) {
      getEdges(data.children);
    }
    return edges;
  }
  /**
  *  @param {event} evt - event from clicking delete button
  *  triggers DeleteLabbookFileMutation
  *  @return {}
  */
  _triggerDeleteMutation(evt) {
    const edges = this.props.fileData ? this._getEdges(this.props.fileData) : [this.props.edge];
    const deleteFileData = {
      filePaths: [this.props.edge.node.key],
      edges,
    };

    this.props.mutations.deleteLabbookFiles(deleteFileData, (reponse) => {});

    this._togglePopup(evt, false);
  }

  /**
  *  @param {Object} node - Dom object to be assigned as a ref
  *  set wrapper ref
  *  @return {}
  */
   _setWrapperRef(node) {
     this[this.props.edge.node.id] = node;
   }

  render() {
    const favoriteCSS = classNames({
            ActionsMenu__item: true,
            'ActionsMenu__item--favorite-on': this.props.edge.node.isFavorite,
            'ActionsMenu__item--favorite-off': !this.props.edge.node.isFavorite,
          }),
          popupCSS = classNames({
            ActionsMenu__popup: true,
            hidden: !this.state.popupVisible,
            ToolTip__message: true,
          }),

          deleteCSS = classNames({
            'ActionsMenu__item ActionsMenu__item--delete': true,
            'ActionsMenu__popup-visible': this.state.popupVisible,
          }),
          folderCSS = classNames({
            ActionsMenu__item: true,
            'ActionsMenu__item--AddSubfolder': true,
            'visibility-hidden': !this.props.folder,
          });

    return (
        <div
          className="ActionsMenu"
          key={`${this.props.edge.node.id}-action-menu}`}
          ref={this._setWrapperRef}>
          <div
            onClick={() => { this.props.folder && this.props.addFolderVisible(true); }}
            className={folderCSS}
            name="Add Subfolder">
          </div>
          <div
            className={deleteCSS}
            name="Delete"
            onClick={(evt) => { this._togglePopup(evt, true); }} >

            <div className={popupCSS}>
              <div className="ToolTip__pointer"></div>
              <p>Are you sure?</p>
              <div className="flex justify--space-around">
                <button
                  className="File__btn--round File__btn--cancel"
                  onClick={(evt) => { this._togglePopup(evt, false); }} />
                <button
                  className="File__btn--round File__btn--add"
                  onClick={(evt) => { this._triggerDeleteMutation(evt); }}
                />
              </div>
            </div>
          </div>
          <div
            onClick={() => { this.props.renameEditMode(true); }}
            className="ActionsMenu__item ActionsMenu__item--rename"
            name="Rename">
          </div>
          {
            this.props.section !== 'data' &&
            <div
              onClick={ () => { this._triggerFavoriteMutation(); }}
              className={favoriteCSS}
              name="Favorite">
            </div>
          }
        </div>
    );
  }
}

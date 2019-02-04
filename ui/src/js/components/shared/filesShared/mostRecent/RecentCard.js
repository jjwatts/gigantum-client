// vendor
import React, { Component } from 'react';
import Moment from 'moment';
import TextTruncate from 'react-text-truncate';
// Mutations
import RemoveFavoriteMutation from 'Mutations/fileBrowser/RemoveFavoriteMutation';
import AddFavoriteMutation from 'Mutations/fileBrowser/AddFavoriteMutation';
// store
import { setErrorMessage } from 'JS/redux/reducers/footer';
import store from 'JS/redux/store';
// config
import config from 'JS/config';

export default class RecentCard extends Component {
  constructor(props) {
    super(props);

    const { owner, labbookName } = store.getState().routes;

    this.state = {
      editMode: false,
      owner,
      labbookName,
    };

    this._handleFileFavoriting = this._handleFileFavoriting.bind(this);
  }

  _handleFileFavoriting(evt, file) {
    if (!file.node.isFavorite) {
      AddFavoriteMutation(
        this.props.favoriteConnection,
        this.props.connection,
        this.props.parentId,
        this.state.owner,
        this.state.labbookName,
        file.node.key,
        '',
        file.node.isDir,
        file,
        this.props.section,
        (response, error) => {
          if (error) {
            console.error(error);
            setErrorMessage(`ERROR: could not add favorite ${this.props.key}`, error);
          }
        },
      );
    } else {
      RemoveFavoriteMutation(
        this.props.favoriteConnection,
        this.props.parentId,
        this.state.owner,
        this.state.labbookName,
        this.props.section,
        file.node.key,
        file.node.id,
        file,
        (response, error) => {
          if (error) {
            console.error(error);
          }
        },
      );
    }
  }

  render() {
    const fileDirectories = this.props.file.node.key.split('/');
    const filename = fileDirectories[fileDirectories.length - 1];
    const path = `${this.props.section}/${this.props.file.node.key.replace(filename, '')}`;
    return (
      <div
        className="Recent__card-wrapper"
      >
        <div
          className="Recent__card Card"
        >
          <div
            onClick={evt => this._handleFileFavoriting(evt, this.props.file)}
            className={this.props.file.node.isFavorite ? 'Favorite__star' : 'Favorite__star--off'}
          />
          <div className="Recent__header-section">
            <h6 className="Recent__card-header">
              <TextTruncate
                 className="Favorite__card-header"
                 line={1}
                 truncateText="…"
                 text={filename}
               />
              </h6>
          </div>

          <div className="Recent__path-section">
            <p className="Recent__path">{path}</p>
          </div>

          <div className="Recent__description-section">
            <p>Last Modified: {Moment(this.props.file.node.modifiedAt * 1000).fromNow()}</p>
            <p>Size: {config.humanFileSize(this.props.file.node.size)} </p>
          </div>
        </div>
      </div>
    );
  }
}

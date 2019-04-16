// vendor
import React, { Component } from 'react';
import Moment from 'moment';
import TextTruncate from 'react-text-truncate';
// config
import config from 'JS/config';
// store
import { setErrorMessage } from 'JS/redux/actions/footer';
import store from 'JS/redux/store';
// Mutations
import RemoveFavoriteMutation from 'Mutations/fileBrowser/RemoveFavoriteMutation';
import AddFavoriteMutation from 'Mutations/fileBrowser/AddFavoriteMutation';
// assets
import '../FileCard.scss';


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

  /**
    @param {Object} file
    handles favoriting of files
    @return {}
  */
  _handleFileFavoriting(file) {
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
      <div className="FileCard Card column-3-span-4--shrink">
        <div
          onClick={() => this._handleFileFavoriting(this.props.file)}
          className={this.props.file.node.isFavorite ? 'FileCard__star' : 'FileCard__star FileCard__star--off'}
        />
        <h6 className="FileCard__header">{filename}</h6>

        <div className="FileCard__path">{path}</div>

        <div className="FileCard__description">
          <p>{`Last Modified: ${Moment(this.props.file.node.modifiedAt * 1000).fromNow()}`}</p>
          <p>{`Size: ${config.humanFileSize(this.props.file.node.size)}`}</p>
        </div>
      </div>
    );
  }
}

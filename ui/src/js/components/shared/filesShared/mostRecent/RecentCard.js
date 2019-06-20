// vendor
import React, { Component } from 'react';
import Moment from 'moment';
import TextTruncate from 'react-text-truncate';
import classNames from 'classnames';
// config
import config from 'JS/config';
// store
import { setErrorMessage } from 'JS/redux/actions/footer';
import store from 'JS/redux/store';
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
  }

  render() {
    const fileDirectories = this.props.file.node.key.split('/');
    const filename = fileDirectories[fileDirectories.length - 1];
    const path = `${this.props.section}/${this.props.file.node.key.replace(filename, '')}`;
    return (
      <div className="FileCard Card column-3-span-4--shrink">
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

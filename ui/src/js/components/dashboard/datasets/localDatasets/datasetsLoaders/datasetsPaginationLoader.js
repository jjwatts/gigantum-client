// vendor
import React, { Component } from 'react';
import classNames from 'classnames';
// assets
import './datasetsPaginationLoader.scss';

export default class DatasetPaginationLoader extends Component {
  render() {
    const PaginationLoaderCSS = classNames({
      [`Card Card--300 column-4-span-3 flex flex--column justify--space-between DatasetPaginationLoader DatasetPaginationLoader--${this.props.index}`]: this.props.isLoadingMore,
      'DatasetPaginationLoader--hidden': !this.props.isLoadingMore,
    });

    return (
      <div
        key="Datasets-loader-card"
        className={PaginationLoaderCSS}
      >
        <div />
      </div>
    );
  }
}

// vendor
import React, { Component } from 'react';
// mutations
import FileBrowser from 'Components/fileBrowser/FileBrowser';

export default class SectionBrowser extends Component {
  constructor(props) {
  	super(props);

    this.state = {
      rootFolder: '',
      moreLoading: false,
    };

    this._setRootFolder = this._setRootFolder.bind(this);
    this._loadMore = this._loadMore.bind(this);
  }

  /*
    loads more if branches are switched
  */
  componentDidUpdate() {
    this.props.loadStatus(this.state.moreLoading);
    if (!this.state.moreLoading && this.props[this.props.section].allFiles && this.props[this.props.section].allFiles.edges.length < 3 && this.props[this.props.section].allFiles.pageInfo.hasNextPage) {
      this._loadMore();
    }
  }

  /*
    handle state and addd listeners when component mounts
  */
  componentDidMount() {
    this.props.loadStatus(this.state.moreLoading);
    if (this.props[this.props.section].allFiles &&
      this.props[this.props.section].allFiles.pageInfo.hasNextPage) {
      this._loadMore(); // routes query only loads 2, call loadMore
    } else {
      this.setState({ moreLoading: false });
    }
  }
  /*
    @param {}
    triggers relay pagination function loadMore
    increments by 100
    logs callback
  */
  _loadMore() {
    this.setState({ moreLoading: true });
    const self = this;
    this.props.relay.loadMore(
      100, // Fetch the next 100 feed items
      (response, error) => {
        if (error) {
          console.error(error);
        }

        if (self.props[this.props.section].allFiles &&
         self.props[this.props.section].allFiles.pageInfo.hasNextPage) {
          self._loadMore();
        } else {
          this.setState({ moreLoading: false });
        }
      },
    );
  }
  /*
    @param
    sets root folder by key
    loads more files
  */
  _setRootFolder(key) {
    this.setState({ rootFolder: key });
  }

  render() {
    if (this.props[this.props.section] && this.props[this.props.section].allFiles) {
      const capitalSection = this.props.section[0].toUpperCase() + this.props.section.slice(1);
      let files = this.props[this.props.section].allFiles;
      if (this.props[this.props.section].allFiles.edges.length === 0) {
        files = {
          edges: [],
          pageInfo: this.props[this.props.section].allFiles.pageInfo,
        };
      }
      return (
        <FileBrowser
          ref={`${this.props.section}Browser`}
          section={this.props.section}
          selectedFiles={this.props.selectedFiles}
          clearSelectedFiles={this.props.clearSelectedFiles}
          setRootFolder={this._setRootFolder}
          files={files}
          parentId={this.props.sectionId}
          connection={`${capitalSection}Browser_allFiles`}
          favoriteConnection={`${capitalSection}Favorites_favorites`}
          favorites={this.props.favorites}
          isLocked={this.props.isLocked}
          {...this.props}
        />
      );
    }
    return (<div>No Files Found</div>);
  }
}

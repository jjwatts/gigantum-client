// vendor
import React, { Component } from 'react';
// componenets
import FileEmpty from 'Components/labbook/overview/FileEmpty';
import MostRecentList from './MostRecentList';
// store
import store from 'JS/redux/store';
// assets
import './MostRecent.scss';

export default class MostRecent extends Component {
  constructor(props) {
    super(props);

    const pathArray = store.getState().routes.callbackRoute.split('/');

    let selectedPath = (pathArray.length > 4) ? pathArray[pathArray.length - 1] : 'overview';
    const fullPathName = selectedPath;

    if (selectedPath === 'inputData' || selectedPath === 'outputData') {
      selectedPath = selectedPath.substring(0, selectedPath.length - 4);
    }

    this.state = {
      loading: false,
      showAmount: 3,
      files: this.props[selectedPath],
      selectedPath,
      fullPathName,
    };
  }

  static getDerivedStateFromProps(nextProps, state) {
    return {
      ...state,
      files: nextProps[state.selectedPath],
    };
  }

  /**
    handle state and addd listeners when component mounts
  */
  componentDidMount() {
    if (this.state.files.allFiles &&
        this.state.files.allFiles.pageInfo.hasNextPage) {
      this._loadMore(); // routes query only loads 2, call loadMore
    }
  }

  /**
    @param {}
    triggers relay pagination function loadMore
    increments by 10
    logs callback
  */
  _loadMore() {
    const self = this;

    this.setState({ loading: true });
    this.props.relay.loadMore(
      100, // Fetch the next 100 feed items
      (response, error) => {
        const files = self.props[this.state.selectedPath];

        if (files.allFiles &&
        files.allFiles.pageInfo.hasNextPage) {
          self._loadMore();
        } else {
          self.setState({ loading: false });
        }
        if (error) {
          console.error(error);
        }
      },
    );
  }
  /**
  *  @param {}
  *  sets state for more
  *  @return {}
  */
  _showMore() {
    this.setState({ showAmount: this.state.showAmount + 3 });
  }
  /**
  *  @param {Array:[Object]} files
  *  sorts by modified date
  *  @return {}
  */
  _sortFiles(files) {
    return files.sort((a, b) => b.node.modifiedAt - a.node.modifiedAt);
  }

  render() {
    if (this.state.files && this.state.files.allFiles) {
      let loadingClass = (this.state.showAmount < this.state.files.allFiles.edges.length) ? 'Recent__action-bar' : 'hidden';
      loadingClass = (this.state.loading) ? 'Recent__action-bar--loading' : loadingClass;

      if (this.state.files.allFiles.edges.length > 0) {
        let allFiles = this.state.files.allFiles.edges.filter(edge => edge && edge.node && (edge.node !== undefined) && !edge.node.isDir);
        allFiles = this._sortFiles(allFiles);
        return (
          <div className="Recent">
            <MostRecentList
              allFiles={allFiles}
              showAmount={this.state.showAmount}
              edgeId={this.props.edgeId}
            />
          </div>

        );
      }
      return (
        <FileEmpty
          section={this.state.fullPathName}
          mainText="This Project has No Recent Files"
        />
      );
    }
    return (<div>No Files Found</div>);
  }
}

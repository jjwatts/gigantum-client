// vendor
import React, { Component } from 'react';
import {
  createPaginationContainer,
  graphql,
} from 'react-relay';
// components
import RemoteDatasetPanel from 'Components/dashboard/datasets/remoteDatasets/RemoteDatasetsPanel';
// import DeleteDataset from 'Components/shared/header/branchMenu/modals/DeleteDataset';
import DatasetsPaginationLoader from '../datasetsLoaders/datasetsPaginationLoader';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// store
import store from 'JS/redux/store';
// assets
import './RemoteDatasets.scss';

class RemoteDatasets extends Component {
  constructor(props) {
    super(props);
    this.state = {
      deleteData: {
        remoteId: null,
        remoteOwner: null,
        remoteDatasetName: null,
        existsLocally: null,
      },
      deleteModalVisible: false,
      isPaginating: false,
    };
    this._toggleDeleteModal = this._toggleDeleteModal.bind(this);
    this._loadMore = this._loadMore.bind(this);
  }
  /*
    loads more remote datasets on mount
  */
  componentDidMount() {
    if (this.props.remoteDatasets.remoteDatasets && this.props.remoteDatasets.remoteDatasets.pageInfo.hasNextPage) {
      this._loadMore();
    }
  }

  /*
    loads more remote datasets if available
  */
  UNSAFE_componentWillReceiveProps(nextProps) {
    if (nextProps.remoteDatasets.remoteDatasets && nextProps.remoteDatasets.remoteDatasets.pageInfo.hasNextPage) {
      this._loadMore();
    }
  }

  /**
    *  @param {}
    *  loads more datasets using the relay pagination container
  */
  _loadMore = () => {
    const self = this;
    UserIdentity.getUserIdentity().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (response.data.userIdentity.isSessionValid) {
            this.setState({
              isPaginating: true,
            });

            if (this.props.remoteDatasets.remoteDatasets.pageInfo.hasNextPage) {
              this.props.relay.loadMore(
                8, // Fetch the next 8 items
                (ev) => {
                  this.setState({
                    isPaginating: false,
                  });
                },
              );
            }
          } else {
            this.props.auth.renewToken(true, () => {
              this.props.forceLocalView();
            }, () => {
              self._loadMore();
            });
          }
        }
      } else {
        this.props.forceLocalView();
      }
    });
  }

  /**
    *  @param {object} deleteData
    *  changes the delete modal's visibility and changes the data passed to it
  */

  _toggleDeleteModal(deleteData) {
    if (deleteData) {
      this.setState({
        deleteData,
        deleteModalVisible: true,
      });
    } else {
      this.setState({
        deleteData: {
          remoteId: null,
          remoteOwner: null,
          remoteDatasetName: null,
          existsLocally: null,
        },
        deleteModalVisible: false,
      });
    }
  }

  render() {
    if (this.props.remoteDatasets && this.props.remoteDatasets.remoteDatasets !== null) {
      const datasets = this.props.filterDatasets(this.props.remoteDatasets, this.props.filterState);

      return (
        <div className="Datasets__listing">
          <div className="grid">
            {
            datasets.length ?
            datasets.map(edge => (
              <RemoteDatasetPanel
                toggleDeleteModal={this._toggleDeleteModal}
                datasetListId={this.props.remoteDatasetsId}
                key={edge.node.owner + edge.node.name}
                ref={`RemoteDatasetPanel${edge.node.name}`}
                edge={edge}
                history={this.props.history}
                existsLocally={edge.node.isLocal}
                auth={this.props.auth}
              />
              ))
            :
            !this.state.isPaginating &&
            store.getState().datasetListing.filterText &&

            <div className="Datasets__no-results">

              <h3 className="Datasets__h3">No Results Found</h3>

              <p>Edit your filters above or <span
                className="Datasets__span"
                onClick={() => this.props.setFilterValue({ target: { value: '' } })}
              >clear
                                            </span> to try again.
              </p>

            </div>
          }
            {
            Array(5).fill(1).map((value, index) => (
              <DatasetsPaginationLoader
                key={`RemoteDatasets_paginationLoader${index}`}
                index={index}
                isLoadingMore={this.state.isPaginating}
              />
              ))
          }
          </div>
        </div>
      );
    }
    UserIdentity.getUserIdentity().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (!response.data.userIdentity.isSessionValid) {
            this.props.auth.renewToken();
          }
        }
      } else {
        this.props.forceLocalView();
      }
    });

    return (<div />);
  }
}

export default createPaginationContainer(
  RemoteDatasets,
  graphql`
    fragment RemoteDatasets_remoteDatasets on DatasetList{
      remoteDatasets(first: $first, after: $cursor, orderBy: $orderBy, sort: $sort)@connection(key: "RemoteDatasets_remoteDatasets", filters: []){
        edges {
          node {
            name
            description
            visibility
            owner
            id
            isLocal
            creationDateUtc
            modifiedDateUtc
          }
          cursor
        }
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
      }
    }
  `,
  {
    direction: 'forward',
    getConnectionFromProps(props, error) {
      return props.remoteDatasets.remoteDatasets;
    },
    getFragmentVariables(prevVars, first, cursor) {
      return {
        ...prevVars,
        first,
      };
    },
    getVariables(props, {
      first, cursor, orderBy, sort,
    }, fragmentVariables) {
      first = 20;
      cursor = props.remoteDatasets.remoteDatasets.pageInfo.endCursor;
      orderBy = fragmentVariables.orderBy;
      sort = fragmentVariables.sort;
      return {
        first,
        cursor,
        orderBy,
        sort,
        // in most cases, for variables other than connection filters like
        // `first`, `after`, etc. you may want to use the previous values.
      };
    },
    query: graphql`
      query RemoteDatasetsPaginationQuery(
        $first: Int!
        $cursor: String
        $orderBy: String
        $sort: String
      ) {
        datasetList{
          ...RemoteDatasets_remoteDatasets
        }
      }
    `,
  },
);

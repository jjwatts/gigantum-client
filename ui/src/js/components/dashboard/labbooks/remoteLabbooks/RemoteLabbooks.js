// vendor
import React, { Component } from 'react';
import {
  createPaginationContainer,
  graphql,
} from 'react-relay';
import { boundMethod } from 'autobind-decorator';
// components
import RemoteLabbookPanel from 'Components/dashboard/labbooks/remoteLabbooks/RemoteLabbookPanel';
import DeleteLabbook from 'Components/shared/modals/DeleteLabbook';
import CardLoader from 'Components/dashboard/shared/loaders/CardLoader';
import NoResults from 'Components/dashboard/shared/NoResults';
// queries
import UserIdentity from 'JS/Auth/UserIdentity';
// store
import store from 'JS/redux/store';
// assets
import './RemoteLabbooks.scss';

class RemoteLabbooks extends Component {
  constructor(props) {
    super(props);
    this.state = {
      deleteData: {
        remoteId: null,
        remoteOwner: null,
        remoteLabbookName: null,
        existsLocally: null,
      },
      deleteModalVisible: false,
      isPaginating: false,
    };
    this._toggleDeleteModal = this._toggleDeleteModal.bind(this);
    this._loadMore = this._loadMore.bind(this);
  }

  /*
    loads more remote labbooks on mount
  */
  componentDidMount() {
    const { props } = this;
    if (props.remoteLabbooks.remoteLabbooks
      && props.remoteLabbooks.remoteLabbooks.pageInfo.hasNextPage) {
      this._loadMore();
    }

    UserIdentity.getUserIdentity().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (!response.data.userIdentity.isSessionValid) {
            props.auth.renewToken();
          }
        }
      } else {
        props.forceLocalView();
      }
    });
  }

  /*
    loads more remote labbooks if available
  */
  UNSAFE_componentWillReceiveProps(nextProps) {
    if (nextProps.remoteLabbooks.remoteLabbooks
      && nextProps.remoteLabbooks.remoteLabbooks.pageInfo.hasNextPage) {
      this._loadMore();
    }
  }

  /**
    *  @param {}
    *  loads more labbooks using the relay pagination container
  */
  @boundMethod
  _loadMore() {
    const { props } = this;
    const self = this;

    UserIdentity.getUserIdentity().then((response) => {
      if (navigator.onLine) {
        if (response.data) {
          if (response.data.userIdentity.isSessionValid) {
            this.setState({
              isPaginating: true,
            });

            if (props.remoteLabbooks.remoteLabbooks.pageInfo.hasNextPage) {
              props.relay.loadMore(
                8, // Fetch the next 8 items
                () => {
                  this.setState({
                    isPaginating: false,
                  });
                },
              );
            }
          } else {
            props.auth.renewToken(true, () => {
              props.forceLocalView();
            }, () => {
              self._loadMore();
            });
          }
        }
      } else {
        props.forceLocalView();
      }
    });
  }

  /**
    *  @param {object} deleteData
    *  changes the delete modal's visibility and changes the data passed to it
  */
  @boundMethod
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
          remoteLabbookName: null,
          existsLocally: null,
        },
        deleteModalVisible: false,
      });
    }
  }

  render() {
    const { props, state } = this;
    if (props.remoteLabbooks && props.remoteLabbooks.remoteLabbooks !== null) {
      const labbooks = props.filterLabbooks(
        props.remoteLabbooks.remoteLabbooks.edges,
        props.filterState,
      );

      return (
        <div className="Labbooks__listing">
          <div className="grid">
            {
            labbooks.length
              ? labbooks.map(edge => (
                <RemoteLabbookPanel
                  toggleDeleteModal={this._toggleDeleteModal}
                  labbookListId={props.remoteLabbooksId}
                  key={edge.node.owner + edge.node.name}
                  ref={`RemoteLabbookPanel${edge.node.name}`}
                  edge={edge}
                  history={props.history}
                  existsLocally={edge.node.isLocal}
                  auth={props.auth}
                />
              ))
              : !state.isPaginating
            && store.getState().labbookListing.filterText
            && <NoResults />
          }
            {
            Array(5).fill(1).map((value, index) => (
              <CardLoader
                key={`RemoteLabbooks_paginationLoader${index}`}
                index={index}
                isLoadingMore={state.isPaginating}
              />
            ))
          }
          </div>
          { state.deleteModalVisible
            && (
              <DeleteLabbook
                handleClose={() => { this._toggleDeleteModal(); }}
                labbookListId={props.labbookListId}
                remoteId={state.deleteData.remoteId}
                remoteConnection="RemoteLabbooks_remoteLabbooks"
                toggleModal={this._toggleDeleteModal}
                remoteOwner={state.deleteData.remoteOwner}
                remoteLabbookName={state.deleteData.remoteLabbookName}
                existsLocally={state.deleteData.existsLocally}
                remoteDelete
                history={props.history}
              />
            )
        }
        </div>
      );
    }

    return (<div />);
  }
}

export default createPaginationContainer(
  RemoteLabbooks,
  graphql`
    fragment RemoteLabbooks_remoteLabbooks on LabbookList{
      remoteLabbooks(first: $first, after: $cursor, orderBy: $orderBy, sort: $sort)@connection(key: "RemoteLabbooks_remoteLabbooks", filters: []){
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
      return props.remoteLabbooks.remoteLabbooks;
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
      cursor = props.remoteLabbooks.remoteLabbooks.pageInfo.endCursor;
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
      query RemoteLabbooksPaginationQuery(
        $first: Int!
        $cursor: String
        $orderBy: String
        $sort: String
      ) {
        labbookList{
          ...RemoteLabbooks_remoteLabbooks
        }
      }
    `,
  },
);

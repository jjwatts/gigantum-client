// vendor
import React, { Component } from 'react';
import {
  createPaginationContainer,
  graphql,
} from 'react-relay';
// components
import LocalDatasetPanel from 'Components/dashboard/datasets/localDatasets/LocalDatasetsPanel';
import CardLoader from 'Components/dashboard/loaders/CardLoader';
import ImportModule from 'Components/dashboard/import/ImportModule';
// helpers
import DatasetVisibilityLookup from './lookups/DatasetVisibilityLookup';
// assets
import './LocalDatasets.scss';


export class LocalDatasets extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isPaginating: false,
      visibilityList: new Map(),
    };

    this._captureScroll = this._captureScroll.bind(this);
    this._loadMore = this._loadMore.bind(this);
    this._fetchDemo = this._fetchDemo.bind(this);
    this._visibilityLookup = this._visibilityLookup.bind(this);
  }

  /** *
  * @param {}
  * adds event listener for pagination and fetches container status
  */
  componentDidMount() {
    this.mounted = true;
    if (!this.props.loading) {
      this._visibilityLookup();
      if (this.props.datasetList
         && this.props.localDatasets.localDatasets
         && this.props.localDatasets.localDatasets.edges
         && this.props.localDatasets.localDatasets.edges.length === 0) {
        this._fetchDemo();
      }
    }
  }

  /** *
  * @param {}
  * removes event listener for pagination and removes timeout for container status
  */
  componentWillUnmount() {
    this.mounted = false;

    window.removeEventListener('scroll', this._captureScroll);
  }

  /** *
    * @param {integer} count
    * attempts to fetch a demo if no datasets are present, 3 times
  */
  _fetchDemo(count = 0) {
    if (count < 3) {
      const self = this;
      const relay = this.props.relay;
      setTimeout(() => {
        relay.refetchConnection(20, (response, error) => {
          if (self.props.localDatasets.localDatasets.edges.length > 0) {

          } else {
            self._fetchDemo(count + 1);
          }
        });
      }, 3000);
    }
  }

  /**
    *  @param {}
    *  fires when user scrolls
    *  if nextPage exists and user is scrolled down, it will cause loadmore to fire
  */
  _captureScroll = () => {
    const root = document.getElementById('root');


    const distanceY = window.innerHeight + document.documentElement.scrollTop + 200;


    const expandOn = root.offsetHeight;

    if (this.props.localDatasets.localDatasets) {
      if ((distanceY > expandOn) && !this.state.isPaginating

      && this.props.localDatasets.localDatasets.pageInfo.hasNextPage) {
        this._loadMore();
      }
    }
  }

  /**
    *  @param {}
    *  loads more datasets using the relay pagination container
  */
  _loadMore = () => {
    this.setState({
      isPaginating: true,
    });

    if (this.props.localDatasets.localDatasets.pageInfo.hasNextPage) {
      this.props.relay.loadMore(
        10, // Fetch the next 10 items
        (ev) => {
          this.setState({
            isPaginating: false,
          });
          this._visibilityLookup();
        },
      );
    }
  }

  /** *
    * @param {}
    * calls VisibilityLookup query and attaches the returned data to the state
    */
  _visibilityLookup() {
    const self = this;

    const idArr = this.props.localDatasets.localDatasets.edges.map(edges => edges.node.id);

    const index = 0;

    function query(ids, index) {
      const subsetIds = idArr.slice(index, index + 10);

      DatasetVisibilityLookup.query(subsetIds).then((res) => {
        if (res && res.data
          && res.data.datasetList
          && res.data.datasetList.localById) {
          const visibilityListCopy = new Map(self.state.visibilityList);

          res.data.datasetList.localById.forEach((node) => {
            visibilityListCopy.set(node.id, node);
          });


          if (index < idArr.length) {
            index += 10;

            query(ids, index);
          }
          if (self.mounted) {
            self.setState({ visibilityList: visibilityListCopy });
          }
        }
      });
    }

    query(idArr, index);
  }

  render() {
    const datasetList = this.props.localDatasets;// datasetList is passed as localDatasets
    if ((datasetList && datasetList.localDatasets && datasetList.localDatasets.edges) || this.props.loading) {
      const datasets = this.props.filterDatasets(datasetList, this.props.filterState, this.props.loading);
      const importVisible = (this.props.section === 'local' || !this.props.loading) && !this.props.filterText;

      return (

        <div className="Datasets__listing">

          <div className="grid">
            {
              importVisible

                && (
                <ImportModule
                  ref="ImportModule_localLabooks"
                  {...this.props}
                  section="dataset"
                  title="Add Dataset"
                  showModal={this.props.showModal}
                  history={this.props.history}
                />
                )

            }
            {
              datasets.length ? datasets.map((edge, index) => {
                const visibility = this.state.visibilityList.has(edge.node.id) ? this.state.visibilityList.get(edge.node.id).visibility : 'loading';
                return (<LocalDatasetPanel
                  key={`${edge.node.owner}/${edge.node.name}`}
                  ref={`LocalDatasetPanel${edge.node.name}`}
                  className="LocalDatasets__panel"
                  edge={edge}
                  visibility={visibility}
                  history={this.props.history}
                  filterText={this.props.filterText}
                  goToDataset={this.props.goToDataset}
                />
                );
              })
                : !this.props.loading && this.props.filterText

                && (
                <div className="Datasets__no-results">

                  <h3 className="Datasets__h3">No Results Found</h3>

                  <p className="Datasets__paragraph--margin">
                    Edit your filters above or
                    <span
                      className="Datasets__span"
                      onClick={() => this.props.setFilterValue({ target: { value: '' } })}
                    >
                    clear
                    </span>
                    to try again.
                  </p>

                </div>
                )
            }

            {
              Array(5).fill(1).map((value, index) => (
                <CardLoader
                  key={`LocalDatasets_paginationLoader${index}`}
                  index={index}
                  isLoadingMore={this.state.isPaginating || this.props.loading}
                />
              ))
            }

          </div>
        </div>
      );
    }
    return (<div />);
  }
}

export default createPaginationContainer(
  LocalDatasets,
  graphql`
    fragment LocalDatasets_localDatasets on DatasetList{
      localDatasets(first: $first, after: $cursor, orderBy: $orderBy, sort: $sort)@connection(key: "LocalDatasets_localDatasets", filters: []){
        edges {
          node {
            id
            name
            description
            owner
            createdOnUtc
            modifiedOnUtc
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
      return props.localDatasets.localDatasets;
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
      first = 10;
      cursor = props.localDatasets.localDatasets.pageInfo.endCursor;
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
      query LocalDatasetsPaginationQuery(
        $first: Int!
        $cursor: String
        $orderBy: String
        $sort: String
      ) {
        datasetList{
          ...LocalDatasets_localDatasets
        }
      }
    `,
  },
);

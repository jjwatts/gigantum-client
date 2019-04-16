import React, { Component } from 'react';
import { graphql, QueryRenderer } from 'react-relay';
import queryString from 'querystring';
// redux
import { setCallbackRoute } from 'JS/redux/actions/routes';
// components
import environment from 'JS/createRelayEnvironment';
import Loader from 'Components/common/Loader';
import LocalLabbooksContainer from './labbooks/localLabbooks/LocalLabbooksContainer';
import LocalDatasetsContainer from './datasets/localDatasets/LocalDatasetsContainer';
import RemoteDatasetsContainer from './datasets/remoteDatasets/RemoteDatasetsContainer';
import RemoteLabbooksContainer from './labbooks/remoteLabbooks/RemoteLabbooksContainer';
// assets
import './Dashboard.scss';


const LocalListingQuery = graphql`query DashboardLocalQuery($first: Int!, $cursor: String, $orderBy: String $sort: String){
  ...LocalLabbooksContainer_labbookList
}`;

const LocalDatasetListingQuery = graphql`query DashboardDatasetLocalQuery($first: Int!, $cursor: String, $orderBy: String $sort: String){
  ...LocalDatasetsContainer_datasetList
}`;
const RemoteDatasetListingQuery = graphql`query DashboardDatasetRemoteQuery($first: Int!, $cursor: String, $orderBy: String $sort: String){
  ...RemoteDatasetsContainer_datasetList
}`;

const RemoteListingQuery = graphql`query DashboardRemoteQuery($first: Int!, $cursor: String, $orderBy: String $sort: String){
  ...RemoteLabbooksContainer_labbookList
}`;

export default class DashboardContainer extends Component {
  constructor(props) {
    super(props);

    const { orderBy, sort } = queryString.parse(this.props.history.location.search.slice(1));

    this.state = {
      selectedComponent: props.match.path,
      orderBy: orderBy || 'modified_on',
      sort: sort || 'desc',
    };
    setCallbackRoute(props.history.location.pathname);
    this._refetchSort = this._refetchSort.bind(this);
  }

  /**
  *  @param {Object} nextProps
  *  update select component before component renders
  */
  UNSAFE_componentWillReceiveProps(nextProps) {
    this.setState({
      selectedComponent: nextProps.match.path,
    });
    setCallbackRoute(nextProps.history.location.pathname);
  }

  /**
    * @param {string, string} orderBy, sort
    * sets state of orderBy and sort, passed to child components
  */
  _refetchSort(orderBy, sort) {
    if (this.state.orderBy !== orderBy || this.state.sort !== sort) {
      this.setState({ orderBy, sort });
    }
  }


  /**
  *  @param {}
  *  returns jsx of selected component
  *  @return {jsx}
  */
  _displaySelectedComponent() {
    const { state, props } = this;
    const paths = props.history.location.pathname.split('/');
    const sectionRoute = paths.length > 2 ? paths[2] : 'local';

    if (paths[2] !== 'cloud' && paths[2] !== 'local') {
      props.history.replace('../../../../projects/local');
    }


    let query;
    if (state.selectedComponent === '/datasets/:labbookSection') {
      query = sectionRoute === 'cloud' ? RemoteDatasetListingQuery : LocalDatasetListingQuery;
    } else if (sectionRoute === 'cloud') {
      query = RemoteListingQuery;
    } else {
      query = LocalListingQuery;
    }

    return (
      <QueryRenderer
        environment={environment}
        query={query}
        variables={{
          first: sectionRoute === 'cloud' ? 8 : 100,
          cursor: null,
          orderBy: state.orderBy,
          sort: state.sort,
        }}
        render={(response) => {
          const { error } = response;
          const renderProps = response.props;
          if (error) {
            console.log(error);
          } else if (renderProps) {
            if (state.selectedComponent === '/datasets/:labbookSection') {
              if (sectionRoute === 'cloud') {
                return (
                  <RemoteDatasetsContainer
                    auth={props.auth}
                    datasetList={renderProps}
                    history={props.history}
                    section={sectionRoute}
                    refetchSort={this._refetchSort}
                    diskLow={props.diskLow}
                  />
                );
              }
              return (
                <LocalDatasetsContainer
                  auth={props.auth}
                  datasetList={renderProps}
                  history={props.history}
                  section={sectionRoute}
                  refetchSort={this._refetchSort}
                  diskLow={props.diskLow}
                />
              );
            }
            if (sectionRoute === 'cloud') {
              return (
                <RemoteLabbooksContainer
                  auth={props.auth}
                  labbookList={renderProps}
                  history={props.history}
                  refetchSort={this._refetchSort}
                  diskLow={props.diskLow}
                />
              );
            }

            return (
              <LocalLabbooksContainer
                auth={props.auth}
                labbookList={renderProps}
                history={props.history}
                refetchSort={this._refetchSort}
                diskLow={props.diskLow}
              />
            );
          } else {
            if (state.selectedComponent === '/datasets/:labbookSection') {
              return (
                <LocalDatasetsContainer
                  auth={props.auth}
                  datasetList={renderProps}
                  history={props.history}
                  section={sectionRoute}
                  refetchSort={this._refetchSort}
                  loading
                  diskLow={props.diskLow}
                />
              );
            }

            return (
              <LocalLabbooksContainer
                auth={props.auth}
                labbookList={renderProps}
                history={props.history}
                section={sectionRoute}
                refetchSort={this._refetchSort}
                loading
                diskLow={props.diskLow}
              />
            );
          }
        }}
      />
    );
  }

  render() {
    return (
      <div className="Dashboard flex flex-column">

        <div className="Dashboard__view flex-1-0-auto">
          <div id="dashboard__cover" className="Dashboard__cover hidden">
            <Loader />
          </div>
          {
            this._displaySelectedComponent()
          }
        </div>
      </div>
    );
  }
}

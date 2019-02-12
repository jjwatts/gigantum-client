// vendor
import React, { Component } from 'react';
import {
  QueryRenderer,
  graphql,
} from 'react-relay';
import { Link } from 'react-router-dom';
// components
import Loader from 'Components/common/Loader';
import FileCard from './FileCard';
import ToolTip from 'Components/common/ToolTip';
// utilites
import environment from 'JS/createRelayEnvironment';
// store
import store from 'JS/redux/store';
// assets
import './FilePreview.scss';

const filePreviewQuery = graphql`query FilePreviewQuery($name: String!, $owner: String!, $first: Int!){
  labbook(name: $name, owner: $owner){
    code{
      favorites(first: $first){
        edges{
          node{
            id
            owner
            name
            section
            key
            description
            isDir
          }
        }
      }
    }
    input{
      favorites(first: $first){
        edges{
          node{
            id
            owner
            name
            section
            key
            description
            isDir
          }
        }
      }
    }
    output{
      favorites(first: $first){
        edges{
          node{
            id
            owner
            name
            section
            key
            description
            isDir
          }
        }
      }
    }
  }
}
`;

export default class FilePreview extends Component {
  /**
    @param {String} section
    handles redirect and scrolling to top
  */
  _handleRedirect(section) {
    const { owner, labbookName } = store.getState().routes;
    const { props } = this;
    props.scrollToTop();
    props.history.push(`/projects/${owner}/${labbookName}/${section}`);
  }

  render() {
    const { owner, labbookName } = store.getState().routes;
    const { props } = this;
    return (
      <QueryRenderer
        variables={{
        name: labbookName,
        owner,
        first: 3,
      }}
        query={filePreviewQuery}
        environment={environment}
        render={(response) => {
        const queryProps = response.props;
        const error = response.error;
        if (queryProps) {
          return (
            <div className="FilePreview">
              <div className="FilePreview__section">
                <div className="FilePreview__container">
                  <h5>
                    Code
                    &nbsp;
                    &nbsp;
                    <ToolTip section="codeOverview" />
                  </h5>
                </div>
                <div className="FilePreview__list grid">
                  {
                    queryProps.labbook.code.favorites && queryProps.labbook.code.favorites.edges.length ?
                    queryProps.labbook.code.favorites.edges.map(edge => <FileCard key={edge.node.id} edge={edge} />) :
                      <div className="FilePreview__empty">
                        <button
                          className="Btn--redirect"
                          onClick={() => this._handleRedirect('code')}
                        >
                          <span>View Code Files</span>
                        </button>
                        <div className="FilePreview__empty-content">
                          <p className="FilePreview__empty-header">This Project has No Code Favorites</p>
                          <Link
                            className="FilePreview__empty-action"
                            to={{ pathname: `/projects/${owner}/${labbookName}/code` }}
                          >
                            View and manage Code Files
                          </Link>
                        </div>
                      </div>
                  }
                </div>
              </div>
              <div className="FilePreview__section">
                <div className="FilePreview__container">
                  <h5>
                    Input Data
                    <ToolTip section="inputDataOverview" />
                  </h5>
                </div>
                <div className="FilePreview__list grid">
                  {
                    queryProps.labbook.input.favorites &&
                    queryProps.labbook.input.favorites.edges.length ? queryProps.labbook.input.favorites.edges.map(edge => <FileCard key={edge.node.id} edge={edge} />) :
                    <div className="FilePreview__empty">
                    <button
                      className="Btn--redirect"
                      onClick={() => this._handleRedirect('inputData')}
                      >
                      <span>View Input Files</span>
                    </button>
                    <div className="FilePreview__empty-content">
                      <p className="FilePreview__empty-header">This Project has No Input Favorites</p>
                      <Link
                        className="FilePreview__empty-action"
                        to={{ pathname: `/projects/${owner}/${labbookName}/inputData` }}
                      >
                        View and manage Input Files
                      </Link>
                    </div>
                  </div>
                  }
                </div>
              </div>
              <div className="FilePreview__section">
                <div className="FilePreview__container">
                  <h5>
                    Output Data
                    <ToolTip section="outputDataOverview" />
                  </h5>
                </div>
                <div className="FilePreview__list grid">
                  {
                    queryProps.labbook.output.favorites &&
                    queryProps.labbook.output.favorites.edges.length ? queryProps.labbook.output.favorites.edges.map(edge => <FileCard key={edge.node.id} edge={edge} />) :
                    <div className="FilePreview__empty">
                    <button
                      className="Btn--redirect"
                      onClick={() => this._handleRedirect('outputData')}
                      >
                      <span>View Output Files</span>
                    </button>
                    <div className="FilePreview__empty-content">
                      <p className="FilePreview__empty-header">This Project has No Output Favorites</p>
                      <Link
                        className="FilePreview__empty-action"
                        to={{ pathname: `/projects/${owner}/${labbookName}/outputData` }}
                      >
                        View and manage Output Files
                      </Link>
                    </div>
                  </div>
                  }
                </div>
              </div>
            </div>
          );
        } else if (error) {
          return (<div>{error.message}</div>);
        }
          return (<Loader />);
      }}
      />);
  }
}

// vendor
import React, { Component } from 'react';
import {
  QueryRenderer,
  graphql,
} from 'react-relay';
import { Link } from 'react-router-dom';
import { boundMethod } from 'autobind-decorator'
// utilites
import environment from 'JS/createRelayEnvironment';
// store
import store from 'JS/redux/store';
// components
import Loader from 'Components/common/Loader';
import Tooltip from 'Components/common/Tooltip';
import FileCard from './FileCard';
import FileEmpty from './FileEmpty';
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
  @boundMethod
  _handleRedirect(section) {
    const { owner, labbookName } = store.getState().routes;
    const { props } = this;
    window.scrollTo(0, 0);
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

                <FilePreviewSection
                  self={this}
                  owner={owner}
                  name={labbookName}
                  sectionData={{
                    section: queryProps.labbook.code,
                    sectionType: 'code',
                    sectionLink: 'Code',
                    sectionTitle: 'Code',
                    sectionTooltip: 'codeOverview',
                  }}
                />

                <FilePreviewSection
                  self={this}
                  owner={owner}
                  name={labbookName}
                  sectionData={{
                    section: queryProps.labbook.input,
                    sectionType: 'input',
                    sectionLink: 'InputData',
                    sectionTitle: 'Input Data',
                    sectionTooltip: 'inputDataOverview',
                  }}
                />

                <FilePreviewSection
                  self={this}
                  owner={owner}
                  name={labbookName}
                  sectionData={{
                    section: queryProps.labbook.output,
                    sectionType: 'output',
                    sectionLink: 'OutputData',
                    sectionTitle: 'Output Data',
                    sectionTooltip: 'outputDataOverview',
                  }}
                />
              </div>
            );
          } if (error) {
            return (<div>{error.message}</div>);
          }
          return (<Loader />);
        }}
      />);
  }
}


const FilePreviewSection = ({
  self,
  owner,
  name,
  sectionData,
}) => {
  const {
    section,
    sectionType,
    sectionLink,
    sectionTitle,
    sectionTooltip,
  } = sectionData;


  const hasFavorites = section.favorites && section.favorites.edges.length;
  return (
    <div className="FilePreview__section">
      <div className="FilePreview__container">
        <h2>
          {sectionTitle}
          <Tooltip section={sectionTooltip} />
        </h2>
      </div>
      <div className="FilePreview__list grid">
        {
          hasFavorites
            ? section.favorites.edges.map(edge => (
              <FileCard
                key={edge.node.id}
                edge={edge}
              />
            ))
            : (
              <FileEmpty
                owner={owner}
                name={name}
                sectionType={sectionType}
                sectionTitle={sectionTitle}
                sectionLink={sectionLink}
                handleRedirect={self._handleRedirect}
              />
            )
        }
      </div>
    </div>
  );
};

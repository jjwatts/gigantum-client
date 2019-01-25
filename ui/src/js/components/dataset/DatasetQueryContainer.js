// vendor
import React, { Component } from 'react';
import { QueryRenderer, graphql } from 'react-relay';
// environment
import environment from 'JS/createRelayEnvironment';

// components
import Dataset from './Dataset';
import Loader from 'Components/shared/Loader';
// store
import { setUpdateAll } from 'JS/redux/reducers/routes';
// dataset query with notes fragment
export const DatasetQuery = graphql`
  query DatasetQueryContainerQuery($name: String!, $owner: String!, $first: Int!, $cursor: String){
    dataset(name: $name, owner: $owner){
      id
      description
      ...Dataset_dataset
    }
  }`;

class DatasetQueryContainer extends Component {
  componentDidMount() {
    setUpdateAll(this.props.owner, this.props.datasetName);
  }

  render() {
    const parentProps = this.props;
    return (<QueryRenderer
      environment={environment}
      query={DatasetQuery}
      variables={
          {
            name: parentProps.datasetName,
            owner: parentProps.owner,
            first: 2,
            // hasNext: false,
          }
        }
      render={({ error, props }) => {
          if (error) {
            console.log(error);

            return (<div>{error.message}</div>);
          } else if (props) {
            if (props.errors) {
              return (<div>{props.errors[0].message}</div>);
            }


              return (
                <Dataset
                  key={parentProps.datasetName}
                  auth={parentProps.auth}
                  datasetName={parentProps.datasetName}
                  query={props.query}
                  dataset={props.dataset}
                  owner={parentProps.owner}
                  history={parentProps.history}
                  {...parentProps}
                />);
          }

            return (<Loader />);
        }
      }
    />);
  }
}

export default DatasetQueryContainer;

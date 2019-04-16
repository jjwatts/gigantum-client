// vendor
import React, { Component } from 'react';
import { QueryRenderer, graphql } from 'react-relay';
// environment
import environment from 'JS/createRelayEnvironment';
// store
import { setUpdateAll } from 'JS/redux/actions/routes';
// components
import Loader from 'Components/common/Loader';
import Dataset from './Dataset';

class DatasetQueryContainer extends Component {
  componentDidMount() {
    setUpdateAll(this.props.owner, this.props.datasetName);
  }

  render() {
    const parentProps = this.props;
    return (
      <QueryRenderer
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
          } if (props) {
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
                diskLow={props.diskLow}
                {...parentProps}
              />);
          }

          return (<Loader />);
        }
      }
      />
    );
  }
}

// dataset query with notes fragment
export const DatasetQuery = graphql`
  query DatasetQueryContainerQuery($name: String!, $owner: String!, $first: Int!, $cursor: String){
    dataset(name: $name, owner: $owner){
      id
      description
      ...Dataset_dataset
    }
}`;

export default DatasetQueryContainer;

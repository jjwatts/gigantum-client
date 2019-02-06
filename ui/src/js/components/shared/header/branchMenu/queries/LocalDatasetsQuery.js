// vendor
import { graphql } from 'react-relay';
// environment
import { fetchQuery } from 'JS/createRelayEnvironment';

const LocalDatasetsQuery = graphql`
  query LocalDatasetsQuery($owner: String!, $name: String!){
    dataset(owner: $owner, name: $name){
        owner
        name
        defaultRemote
    }
  }
`;

const LocalDatasets = {
  getLocalDatasets: variables => new Promise((resolve, reject) => {
    const fetchData = function () {
      fetchQuery(LocalDatasetsQuery(), variables).then((response, error) => {
        if (response) {
            console.log(response);
          resolve(response);
        } else {
          reject(response);
        }
      }).catch((error) => {
        reject(error);
      });
    };

    fetchData();
  }),
};

export default LocalDatasets;

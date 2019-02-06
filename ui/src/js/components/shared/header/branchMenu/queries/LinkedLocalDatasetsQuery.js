// vendor
import { graphql } from 'react-relay';
// environment
import { fetchQuery } from 'JS/createRelayEnvironment';

const LinkedLocalDatasetsQuery = graphql`
  query LinkedLocalDatasetsQuery($owner: String!, $name: String!){
    labbook(owner: $owner, name: $name){
        linkedDatasets{
            owner
            name
            defaultRemote
        }
    }
  }
`;

const LocalDatasets = {
  getLocalDatasets: variables => new Promise((resolve, reject) => {
    const fetchData = function () {
      fetchQuery(LinkedLocalDatasetsQuery(), variables).then((response, error) => {
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

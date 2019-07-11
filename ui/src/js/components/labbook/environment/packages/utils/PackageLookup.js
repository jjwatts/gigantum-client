// vendor
import { graphql } from 'react-relay';
// environment
import { fetchQuery } from 'JS/createRelayEnvironment';

const PackageLookupQuery = graphql`
  query PackageLookupQuery($owner: String!, $name: String!, $input: [PackageComponentInput]!){
    labbook(owner: $owner, name: $name){
      checkPackages(packageInput: $input){
        id,
        schema
        manager
        package
        version
        description
        latestVersion
        fromBase
        isValid
      }
    }
  }
`;


const PackageLookup = {
  query: (name, owner, input) => {
    const variables = { name, owner, input };

    return new Promise((resolve, reject) => {
      const fetchData = () => {
        fetchQuery(PackageLookupQuery(), variables).then((response) => {
          resolve(response);
        }).catch((error) => {
          console.log(error);
          reject(error);
        });
      };

      fetchData();
    });
  },
};

export default PackageLookup;

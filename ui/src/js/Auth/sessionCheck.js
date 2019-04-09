// vendor
import { graphql } from 'react-relay';
// environment
import { fetchQuery } from 'JS/createRelayEnvironment';

const sessionCheckQuery = graphql`
  query sessionCheckQuery{
    userIdentity{
      isSessionValid
    }
  }
`;

const UserIdentity = {
  /*
    fetches session information from useridentity field in api
  */
  getUserIdentity: () => new Promise((resolve, reject) => {
    const fetchData = () => {
      fetchQuery(sessionCheckQuery(), {}).then((response, error) => {
        if (response) {
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

export default UserIdentity;

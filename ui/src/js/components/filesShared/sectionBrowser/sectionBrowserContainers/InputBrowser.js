// vendor
import { createPaginationContainer, graphql } from 'react-relay';
// component
import SectionBrowser from '../SectionBrowser';
// store
import store from 'JS/redux/store';

export default createPaginationContainer(
  SectionBrowser,
    {

      input: graphql`
        fragment InputBrowser_input on LabbookSection{
          allFiles(after: $cursor, first: $first)@connection(key: "InputBrowser_allFiles", filters: []){
            edges{
              node{
                id
                isDir
                isFavorite
                modifiedAt
                key
                size
              }
              cursor
            }
            pageInfo{
              hasNextPage
              hasPreviousPage
              startCursor
              endCursor
            }
          }

        }`,
    },
    {
      direction: 'forward',
      getConnectionFromProps(props) {
        return props.input && props.input.allFiles;
      },
      getFragmentVariables(prevVars, totalCount) {
        return {
          ...prevVars,
          count: totalCount,
        };
      },
      getVariables(props, { count, cursor }, fragmentVariables) {
        const { owner, labbookName } = store.getState().routes;

        return {
          first: count,
          cursor,
          owner,
          name: labbookName,
        };
      },
      query: graphql`
        query InputBrowserPaginationQuery(
          $first: Int
          $cursor: String
          $owner: String!
          $name: String!
        ) {
          labbook(name: $name, owner: $owner){
            input{
              # You could reference the fragment defined previously.
              ...InputBrowser_input
            }
          }
        }
      `,
    },
  );

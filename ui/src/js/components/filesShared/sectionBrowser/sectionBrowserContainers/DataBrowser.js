// vendor
import { createPaginationContainer, graphql } from 'react-relay';
// component
import SectionBrowser from '../SectionBrowser';
// store
import store from 'JS/redux/store';

export default createPaginationContainer(
    SectionBrowser,
    {

      data: graphql`
        fragment DataBrowser_data on Dataset{
          allFiles(after: $cursor, first: $first)@connection(key: "DataBrowser_allFiles", filters: []){
            edges{
              node{
                id
                isDir
                isLocal
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
        return props.data && props.data.allFiles;
      },
      getFragmentVariables(prevVars, totalCount) {
        return {
          ...prevVars,
          first: totalCount,
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
        query DataBrowserPaginationQuery(
          $first: Int
          $cursor: String
          $owner: String!
          $name: String!
        ) {
          dataset(name: $name, owner: $owner){
             id
             description
             ...DataBrowser_data
          }
        }
      `,
    },

  );

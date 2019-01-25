// vendor
import { createPaginationContainer, graphql } from 'react-relay';
// component
import SectionBrowser from '../SectionBrowser';
// store
import store from 'JS/redux/store';

export default createPaginationContainer(
    SectionBrowser,
    {

      output: graphql`
        fragment OutputBrowser_output on LabbookSection{
          allFiles(after: $cursor, first: $first)@connection(key: "OutputBrowser_allFiles", filters:[]){
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
        return props.output && props.output.allFiles;
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
        query OutputBrowserPaginationQuery(
          $first: Int
          $cursor: String
          $owner: String!
          $name: String!
        ) {
          labbook(name: $name, owner: $owner){
             id
             description
             output{
              # You could reference the fragment defined previously.
              ...OutputBrowser_output
            }
          }
        }
      `,
    },
  );

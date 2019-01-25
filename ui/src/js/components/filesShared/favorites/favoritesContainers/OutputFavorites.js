// vendor
import { createPaginationContainer, graphql } from 'react-relay';
// component
import Favorites from '../Favorites';
// store
import store from 'JS/redux/store';

export default createPaginationContainer(
    Favorites,
    {

      output: graphql`
        fragment OutputFavorites_output on LabbookSection{
          favorites(after: $cursor, first: $first)@connection(key: "OutputFavorites_favorites", filters: []){
            edges{
              node{
                id
                owner
                name
                index
                key
                description
                isDir
                associatedLabbookFileId
                section
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
        return props.output && props.output.favorites;
      },
      getFragmentVariables(prevVars, totalCount) {
        return {
          ...prevVars,
          first: totalCount,
        };
      },
      getVariables(props, { count, cursor }, fragmentVariables) {
        const { owner, labbookName } = store.getState().routes;
        const root = '';

        return {
          first: count,
          cursor,
          root,
          owner,
          name: labbookName,
        };
      },
      query: graphql`
        query OutputFavoritesPaginationQuery(
          $first: Int
          $cursor: String
          $owner: String!
          $name: String!
        ) {
          labbook(name: $name, owner: $owner){
             id
             description
             # You could reference the fragment defined previously.
             output{
               ...OutputFavorites_output
             }
          }
        }
      `,
    },

  );

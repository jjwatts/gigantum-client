// vendor
import { createPaginationContainer, graphql } from 'react-relay';
// component
import Favorites from '../Favorites';
// store
import store from 'JS/redux/store';

export default createPaginationContainer(
    Favorites,
    {

      code: graphql`
        fragment CodeFavorites_code on LabbookSection{
          favorites(after: $cursor, first: $first)@connection(key: "CodeFavorites_favorites"){
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
        return props.code && props.code.favorites;
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
        query CodeFavoritesPaginationQuery(
          $first: Int
          $cursor: String
          $owner: String!
          $name: String!
        ) {
          labbook(name: $name, owner: $owner){
             id
             description
             # You could reference the fragment defined previously.
             code{
               ...CodeFavorites_code
             }
          }
        }
      `,
    },

  );

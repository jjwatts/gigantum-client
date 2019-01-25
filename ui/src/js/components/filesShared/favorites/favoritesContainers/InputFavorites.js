// vendor
import { createPaginationContainer, graphql } from 'react-relay';
// component
import Favorites from '../Favorites';
// store
import store from 'JS/redux/store';

export default createPaginationContainer(
  Favorites,
  {

    input: graphql`
      fragment InputFavorites_input on LabbookSection{
        favorites(after: $cursor, first: $first)@connection(key: "InputFavorites_favorites", filters: []){
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
      return props.input && props.input.favorites;
    },
    getFragmentVariables(prevVars, totalCount) {
      return {
        ...prevVars,
        first: totalCount,
      };
    },
    getVariables(props, { count, cursor }, fragmentVariables) {
      const root = '';
      const { owner, labbookName } = store.getState().routes;
      return {
        first: count,
        cursor,
        root,
        owner,
        name: labbookName,
      };
    },
    query: graphql`
      query InputFavoritesPaginationQuery(
        $first: Int
        $cursor: String
        $owner: String!
        $name: String!
      ) {
        labbook(name: $name, owner: $owner){
           id
           description
           # You could reference the fragment defined previously.
           input{
             ...InputFavorites_input
           }
        }
      }
    `,
  },

);

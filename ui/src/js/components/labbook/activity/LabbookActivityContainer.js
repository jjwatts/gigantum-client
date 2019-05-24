import Activity from 'Components/shared/activity/Activity';
import {
  createPaginationContainer,
  graphql,
} from 'react-relay';

/*
  activity pagination container
  contains activity fragment and for query consumption
*/


export default createPaginationContainer(
  Activity,
  {
    labbook: graphql`
        fragment LabbookActivityContainer_labbook on Labbook{
          activityRecords(first: $first, after: $cursor) @connection(key: "LabbookActivityContainer_activityRecords", filters: [$cursor]) @skip (if: $activitySkip){
            edges{
              node{
                id
                commit
                linkedCommit
                type
                show
                importance
                tags
                message
                timestamp
                username
                detailObjects{
                  id
                  key
                  show
                  importance
                  type
                }
              }
              cursor
            }
            pageInfo{
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
        }`,
  },
  {
    direction: 'forward',
    getConnectionFromProps(props) {
      return props.labbook && props.labbook.activityRecords;
    },
    getFragmentVariables(prevVars, first) {
      return {
        ...prevVars,
        first,
      };
    },
    getVariables(props, { count, cursor }, fragmentVariables) {
      const { owner } = props.match.params;
      const name = props.match.params.labbookName;
      return {
        ...fragmentVariables,
        first: count,
        cursor,
        name,
        owner,
        activitySkip: false,
        filter: [],
        // in most cases, for variables other than connection filters like
        // `first`, `after`, etc. you may want to use the previous values.
        // orderBy: fragmentVariables.orderBy,
      };
    },
    query: graphql`
       query LabbookActivityContainerPaginationQuery($name: String!, $owner: String!, $first: Int!, $cursor: String, $activitySkip: Boolean!){
         labbook(name: $name, owner: $owner){
           id
           description
           ...LabbookActivityContainer_labbook
         }
       }`,

  },
);

import Activity, { getGlobals } from 'Components/shared/activity/Activity';
import {
  createPaginationContainer,
  graphql,
} from 'react-relay';

/*
  activity pagination container
  contains activity fragment and for query consumption
*/
const counter = 5;
const pagination = false;


export default createPaginationContainer(
  Activity,
  {
    labbook: graphql`
        fragment LabbookActivityContainer_labbook on Labbook{
          activityRecords(first: $first, after: $cursor) @connection(key: "LabbookActivityContainer_activityRecords") @skip (if: $activitySkip){
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
    getFragmentVariables(prevVars, first, cursor) {
      return {
        ...prevVars,
        first,
      };
    },
    getVariables(props, { count, cursor }, fragmentVariables) {
      const { owner } = props.match.params;
      const { counter, pagination } = getGlobals();
      const name = props.match.params.labbookName;
      const first = counter;

      cursor = pagination ? props.labbook.activityRecords.edges[props.labbook.activityRecords.edges.length - 1].cursor : null;

      return {
        first,
        cursor,
        name,
        owner,
        activitySkip: false,
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

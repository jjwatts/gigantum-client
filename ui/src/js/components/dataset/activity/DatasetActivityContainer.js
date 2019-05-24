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
    dataset: graphql`
        fragment DatasetActivityContainer_dataset on Dataset{
          activityRecords(first: $first, after: $cursor) @connection(key: "DatasetActivityContainer_activityRecords") @skip (if: $activitySkip){
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
      return props.dataset && props.dataset.activityRecords;
    },
    getFragmentVariables(prevVars, first, cursor) {
      return {
        ...prevVars,
        first,
      };
    },
    getVariables(props, { count, cursor }, fragmentVariables) {
      const { owner } = props.match.params;
      const name = props.match.params.datasetName;

      return {
        first: count,
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
       query DatasetActivityContainerPaginationQuery($name: String!, $owner: String!, $first: Int!, $cursor: String, $activitySkip: Boolean!){
         dataset(name: $name, owner: $owner){
           id
           description
           ...DatasetActivityContainer_dataset
         }
       }`,

  },
);

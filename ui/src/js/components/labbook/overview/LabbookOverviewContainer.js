// vendor
import {
    createFragmentContainer,
    graphql,
  } from 'react-relay';
// components
import Overview from 'Components/shared/overview/Overview';


export default createFragmentContainer(
    Overview,
    graphql`fragment LabbookOverviewContainer_labbook on Labbook {
      overview{
        id
        owner
        name
        readme
        numAptPackages
        numConda2Packages
        numConda3Packages
        numPipPackages
        recentActivity{
          id
          owner
          name
          message
          detailObjects {
            id
            data
          }
          type
          timestamp
          username
          email
        }
        remoteUrl
      }
      environment{
        id
        imageStatus
        containerStatus
        ...Base_environment
      }
    }`,
  );

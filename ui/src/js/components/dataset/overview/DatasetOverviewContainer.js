// vendor
import {
    createFragmentContainer,
    graphql,
  } from 'react-relay';
// components
import Overview from 'Components/shared/overview/Overview';


export default createFragmentContainer(
    Overview,
    graphql`fragment DatasetOverviewContainer_dataset on Dataset {
      overview{
        id
        owner
        name
        numFiles
        totalBytes
        localBytes
        fileTypeDistribution
        readme
      }
    }`,
  );

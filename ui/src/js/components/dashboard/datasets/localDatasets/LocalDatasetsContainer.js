// vendor
import {
  createFragmentContainer,
  graphql,
} from 'react-relay';
// components
import Datasets from '../Datasets';

export default createFragmentContainer(
  Datasets,
  graphql`
    fragment LocalDatasetsContainer_datasetList on LabbookQuery{
      datasetList{
        id
        ...LocalDatasets_localDatasets
      }
    }
  `,
);

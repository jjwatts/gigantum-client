import Datasets from '../Datasets';
import {
  createFragmentContainer,
  graphql,
} from 'react-relay';

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

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
    fragment RemoteDatasetsContainer_datasetList on LabbookQuery{
      datasetList{
        id
        ...RemoteDatasets_remoteDatasets
      }
    }
  `,
);

// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from 'Components/shared/filesShared/sectionWrapper/SectionWrapper';

export default createFragmentContainer(
  SectionWrapper,
  graphql`
      fragment Input_labbook on Labbook {
        input @skip (if: $inputSkip){
          id
          hasFiles
          hasFavorites
          ...InputBrowser_input
          ...InputFavorites_input
          ...MostRecentInput_input
          isUntracked
        }
        linkedDatasets @skip (if: $inputSkip){
          name
          owner
          commitsBehind
          allFiles{
            edges{
              node{
                id
                owner
                name
                key
                isDir
                isFavorite
                isLocal
                modifiedAt
                size
              }
            }
          }
        }
      }
    `,
);

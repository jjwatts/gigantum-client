// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from 'Components/shared/filesShared/sectionWrapper/SectionWrapper';

export default createFragmentContainer(
  SectionWrapper,
  graphql`
      fragment Input_labbook on Labbook {
        input{
          id
          hasFiles
          hasFavorites
          ...InputBrowser_input
          ...InputFavorites_input
          ...MostRecentInput_input
          isUntracked
        }
        linkedDatasets {
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

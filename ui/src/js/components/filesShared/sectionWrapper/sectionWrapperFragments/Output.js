// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from '../SectionWrapper';

export default createFragmentContainer(
    SectionWrapper,
    graphql`
      fragment Output_labbook on Labbook {
        output{
          id
          hasFiles
          hasFavorites
          ...OutputBrowser_output
          ...OutputFavorites_output
          ...MostRecentOutput_output
          isUntracked
        }
      }
    `,
  );

// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from '../SectionWrapper';

export default createFragmentContainer(
    SectionWrapper,
    graphql`
      fragment Code_labbook on Labbook{
        code{
          id
          hasFiles
          hasFavorites
          ...CodeBrowser_code
          ...CodeFavorites_code
          ...MostRecentCode_code
        }
      }
    `,
  );

// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from 'Components/shared/filesShared/sectionWrapper/SectionWrapper';

export default createFragmentContainer(
  SectionWrapper,
  graphql`
      fragment Output_labbook on Labbook {
        output @skip (if: $outputSkip){
          id
          hasFiles
          ...OutputBrowser_output
        }
      }
    `,
);

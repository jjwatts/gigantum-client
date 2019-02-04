// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from 'Components/shared/filesShared/sectionWrapper/SectionWrapper';

export default createFragmentContainer(
    SectionWrapper,
    graphql`
      fragment Data_dataset on Dataset{
        id
        ...DataBrowser_data
      }
    `,
  );

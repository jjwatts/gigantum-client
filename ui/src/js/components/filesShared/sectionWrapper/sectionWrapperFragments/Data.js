// vendor
import { createFragmentContainer, graphql } from 'react-relay';
// component
import SectionWrapper from '../SectionWrapper';

export default createFragmentContainer(
    SectionWrapper,
    graphql`
      fragment Data_dataset on Dataset{
        id
        ...DataBrowser_data
      }
    `,
  );

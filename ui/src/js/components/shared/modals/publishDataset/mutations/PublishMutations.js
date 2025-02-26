// mutations
import PublishLabbookMutation from 'Mutations/branches/PublishLabbookMutation';
import PublishDatasetMutation from 'Mutations/branches/PublishDatasetMutation';
import ModifyDatasetLinkMutation from 'Mutations/ModifyDatasetLinkMutation';
import BuildImageMutation from 'Mutations/container/BuildImageMutation';

class PublishMutations {
  /**
    * @param {Object} props
    *        {string} props.owner
    *        {string} props.name
    *        {string} props.labbookId
    *        {string} props.parentId
    * pass above props to state
    */

  constructor(props) {
    this.state = props;
  }

  /**
    * @param {Object} data
    *        {string} props.datasetNamed
    * pass above props to state
    */
  _publishLabbook(data, callback) {
    const {
      owner,
      labbookName,
      labbookId,
    } = this.state;
    const {
      setPublic,
      successCall,
      failureCall,
    } = data;

    PublishLabbookMutation(
      owner,
      labbookName,
      labbookId,
      setPublic,
      successCall,
      failureCall,
      callback,
    );
  }

  /**
    * @param {Object} data
    *        {string} props.datasetName
    * pass above props to state
    */
  _publishDataset(data, callback) {
    const { owner } = this.state;
    const {
      datasetName,
      setPublic,
      successCall,
      failureCall,
    } = data;

    PublishDatasetMutation(
      owner,
      datasetName,
      setPublic,
      successCall,
      failureCall,
      callback,
    );
  }

  /**
    * @param {Object} data
    *        {string} props.datasetOwner
    *        {string} props.datasetName
    *        {string} props.linkType
    *        {string} props.remote
    * pass above props to state
    */
  _modifyDatasetLink(data, callback) {
    const {
      owner,
      labbookName,
    } = this.state;
    const {
      datasetOwner,
      datasetName,
      linkType,
      remote,
    } = data;

    ModifyDatasetLinkMutation(
      owner,
      labbookName,
      datasetOwner,
      datasetName,
      linkType,
      remote,
      callback,
    );
  }

  /**
    * @param {Object} data
    *        {string} props.datasetName
    * pass above props to state
    */
  _buildImage(data, callback) {
    const {
      owner,
      labbookName,
    } = this.state;
    const {
      noCache,
    } = data;

    BuildImageMutation(
      owner,
      labbookName,
      noCache,
      callback,
    );
  }
}


export default PublishMutations;

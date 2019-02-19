// mutations
import StopContainerMutation from 'Mutations/container/StopContainerMutation';
import StartContainerMutation from 'Mutations/container/StartContainerMutation';
import StartDevToolMutation from 'Mutations/container/StartDevToolMutation';
import BuildImageMutation from 'Mutations/container/BuildImageMutation';


class ContainerMutations {
   /**
    * @param {Object} props
    *        {string} props.owner
    *        {string} props.name
    * pass above props to state
    */
   constructor(props) {
    this.state = props;
   }

   /**
   *  @param {Object} data
   *         {string} data.devTool
   *  @param {function} callback
   *  starts container, starts dev tool if it is passed in the data object
   */
   startContainer(data, callback) {
    const self = this;
    const devTool = data.devTool,
    { owner, name } = this.state;

    StartContainerMutation(
      owner,
      name,
      (response, error) => {
        if (response && devTool) {
          self.startDevTool(data, callback);
        } else {
          callback(response, error);
        }
      },
    );
   }

   /**
   *  @param {Object} data
   *  @param {function} callback
   *  stops container
   */
   stopContainer(data, callback) {
    const { owner, name } = this.state;
    StopContainerMutation(
      owner,
      name,
      callback,
    );
   }

   /**
   *  @param {Object} data
   *         {string} data.devTool
   *  @param {function} callback
   *  start dev tool
   */
   startDevTool(data, callback) {
     const { devTool } = data,
            { owner, name } = this.state;
     StartDevToolMutation(
        owner,
        name,
        devTool,
        callback,
     );
   }


   /**
   *  @param {Object} data
   *         {string} data.devTool
   *  @param {function} callback
   *  builds image if rebuild is required, starts dev tool on callback.
   */
   buildImage(data, callback) {
     const { noCache } = data,
           { owner, name } = this.state,
           self = this;

     BuildImageMutation(
        owner,
        name,
        noCache,
        () => {
          self.startContainer({}, callback);
        },
     );
   }
}

export default ContainerMutations;

// mutations
import AddPackageComponentsMutation from 'Mutations/environment/AddPackageComponentsMutation';
import RemovePackageComponentsMutation from 'Mutations/environment/RemovePackageComponentsMutation';

class PackageMutations {
  /**
    * @param {Object} props
    *        {string} props.owner
    *        {string} props.name
    *        {string} props.connection
    *        {string} props.parentId
    * pass above props to state
    */
  constructor(props) {
    this.state = props;
  }

  /**
   *  @param {Object} data
   *         {string} data.branchName
   *         {string} data.revision
   *         {string} data.description
   *  @param {function} callback
   *  creates a new branch and checks it out
   */
  addPackages(data, callback) {
    const {
      packages,
      duplicates,
    } = data;

    const {
      owner,
      name,
      environmentId,
    } = this.state;

    const addPackageObject = {};
    packages.forEach((pkg) => {
      if (addPackageObject[pkg.manager]) {
        addPackageObject[pkg.manager][pkg.package] = {
          description: pkg.description,
          latestVersion: pkg.latestVersion,
        };
      } else {
        addPackageObject[pkg.manager] = {
          [pkg.package]: {
            description: pkg.description,
            latestVersion: pkg.latestVersion,
          },
        };
      }
    });

    const filteredPackages = packages.map(pkg => ({
      package: pkg.package,
      manager: pkg.manager,
      version: pkg.version,
    }));

    AddPackageComponentsMutation(
      name,
      owner,
      environmentId,
      filteredPackages,
      addPackageObject,
      duplicates,
      callback,
    );
  }

  /**
   *  @param {Object} data
   *         {string} data.branchName
   *         {string} data.revision
   *         {string} data.description
   *  @param {function} callback
   *  creates a new branch and checks it out
   */
  removePackages(data, callback) {
    const {
      packages,
    } = data;

    const removalPackageObject = {};
    packages.forEach((pkg) => {
      if (removalPackageObject[pkg.manager]) {
        removalPackageObject[pkg.manager][pkg.package] = pkg.id;
      } else {
        removalPackageObject[pkg.manager] = { [pkg.package]: pkg.id };
      }
    });

    const managers = Object.keys(removalPackageObject);

    const {
      owner,
      name,
      environmentId,
    } = this.state;

    managers.forEach((manager) => {
      const managerObject = removalPackageObject[manager];
      const removalPackages = Object.keys(managerObject);
      const removalIDArr = Object.values(managerObject);
      RemovePackageComponentsMutation(
        name,
        owner,
        environmentId,
        manager,
        removalPackages,
        removalIDArr,
        callback,
      );
    });
  }
}

export default PackageMutations;

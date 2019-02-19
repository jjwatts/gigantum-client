// vendor
import React, { Component, Fragment } from 'react';
import { boundMethod } from 'autobind-decorator';
// utils
import ContainerMutations from './utils/ContainerMutations';
// component
import ContainerStatus from './containerStatus/ContainerStatus';
import DevTools from './devTools/DevTools';
// assets
import './Container.scss';

class Container extends Component {
  state = {
    containerMutations: new ContainerMutations({ name: this.props.labbook.name, owner: this.props.labbook.owner }),
    status: '',
    previousContainerStatus: this.props.containerStatus,
  }

  static getDerivedStateFromProps(nextProps, state) {
    const status = (state.previousContainerStatus === nextProps.containerStatus) ? state.status : '';
    return ({
      ...state,
      status,
      previousContainerStatus: nextProps.containerStatus,
    });
  }

  /**
  *  @param {String} status
  *
  *  @param {}
  *  updates container status
  */
  @boundMethod
  _updateStatus(status) {
    this.setState({ status });
  }

  render() {
    const { props, state } = this,
          { labbook } = props;

    return (
        <div className="Container">

            <DevTools
              {...props}
              updateStatus={this._updateStatus}
              stateStatus={state.status}
              containerMutations={state.containerMutations}
              isBuilding={state.isBuilding}
            />

            <ContainerStatus
              ref={ref => this.containerStatusComponent = ref}
              {...props}
              stateStatus={state.status}
              updateStatus={this._updateStatus}
              containerMutations={state.containerMutations}
              base={labbook.environment.base}
              isBuilding={state.isBuilding}
            />

        </div>
    );
  }
}

export default Container;

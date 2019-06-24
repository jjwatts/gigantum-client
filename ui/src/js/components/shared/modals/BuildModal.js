// vendor
import React, { Component } from 'react';
import { boundMethod } from 'autobind-decorator';
// components
import Modal from 'Components/common/Modal';
import BuildProgress from 'Components/common/BuildProgress';

export default props => (
  <Modal
    size="large-full"
    handleClose={() => props.setBuildId(null)}
    renderContent={() => (
      <BuildProgress
        headerText="Building Project"
        toggleModal={props.setBuildId}
        buildId={props.buildId}
        keepOpen={props.keepOpen}
        owner={props.owner}
        name={props.name}
      />
    )}
  />
);

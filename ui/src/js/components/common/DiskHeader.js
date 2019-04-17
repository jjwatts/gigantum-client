// vendor
import React from 'react';
// config
import config from 'JS/config';
// assets
import './DiskHeader.scss';

const DiskHeader = ({ available, hideDiskWarning }) => (
  <div className="DiskHeader">
    Gigantum has only
    {` ${config.humanFileSize(available * 1000000000)} `}
    of remaining disk space.
    <a
      href="https://docs.gigantum.com/docs/manage-docker-disk-size"
      rel="noopener noreferrer"
      target="_blank"
    >
    Click here
    </a>
    {' '}
    to learn how to allocate more space to Docker, or free up existing storage in Gigantum.
    <button
      onClick={() => hideDiskWarning()}
      className="Btn__close Btn--round Btn--medium"
      type="button"
    />
  </div>
);


export default DiskHeader;

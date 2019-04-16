// vendor
import React from 'react';
// assets
import './DiskHeader.scss';

const DiskHeader = () => (
  <div className="DiskHeader">
    Gigantum is running low on storage.
    {' '}
    <a
      href="https://docs.gigantum.com/docs/"
      rel="noopener noreferrer"
      target="_blank"
    >
    Click here
    </a>
    {' '}
    to learn how to allocate more space to Docker, or free up existing storage in Gigantum.
  </div>
);


export default DiskHeader;

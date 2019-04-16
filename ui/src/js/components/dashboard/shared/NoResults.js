// vendor
import React from 'react';
import PropTypes from 'prop-types';
// assets
import './NoResults.scss';

const NoResults = ({ setFilterValue }) => (
  <div className="NoResults">

    <h3>No Results Found</h3>

    <p>
      Edit your filters above or
      {' '}
      <button
        type="button"
        className="Btn Btn--flat Btn--noPadding Btn--noMargin"
        onClick={() => setFilterValue({ target: { value: '' } })}
      >
       clear
      </button>
      {' '}
      to try again.
    </p>

  </div>
);

NoResults.propTypes = { setFilterValue: PropTypes.func.isRequired };

export default NoResults;

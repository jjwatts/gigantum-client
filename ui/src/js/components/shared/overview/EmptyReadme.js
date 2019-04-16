import React from 'react';
import classNames from 'classnames';


const EmptyReadme = ({ editingReadme, setEditingReadme }) => {
  const overviewReadmeButtonCSS = classNames({
    'Btn Btn--feature Btn__edit': true,
    hidden: editingReadme,
  });

  return (
    <div className="grid">
      <div className="Overview__empty column-1-span-12">
        <button
          type="button"
          className={overviewReadmeButtonCSS}
          onClick={() => setEditingReadme(true)}
        >
          <span>Edit Readme</span>
        </button>
        <div className="Overview__empty-content">
          <p>This Project Has No Readme</p>
          <button
            type="button"
            className="Overview__empty-action Btn Btn--flat"
            onClick={() => setEditingReadme(true)}
          >
            Create a Readme
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmptyReadme;

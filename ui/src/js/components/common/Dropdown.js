// vendor
import React from 'react';
import classNames from 'classnames';

const Dropdown = ({
  listItems,
  visibility,
  customStyle,
  listAction,
  itemAction,
  label,
}) => {
  const dropdownCSS = classNames({
    'Dropdown relative': true,
    'Dropdown--open': visibility,
    'Dropdown--collapsed': !visibility,
    [`Dropdown--${customStyle}`]: customStyle,
  });

  return (
    <div
      className={dropdownCSS}
      onClick={() => listAction()}
    >
      {label}
      {
        visibility && (
        <ul className="Dropdown__menu">
          {
            listItems.map(item => (
              <li
                className="Dropdown__item"
                key={item}
                onClick={() => itemAction(item)}
              >
                {item}
              </li>))
          }
        </ul>
        )
      }
    </div>
  );
};


export default Dropdown;

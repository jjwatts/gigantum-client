import React from 'react';


const NoCollaborators = (props) => {

  return (
    props.collaborators.length
      ? (
        <div className="CollaboratorsModal__message">
          To add and edit collaborators,
          <b>{' Administrator '}</b>
          access is required. Contact the Project
          <b>{' Owner '}</b>
          or a Project
          <b>{' Administrator '}</b>
          to manage collaborator settings.
        </div>
      ) : (
        <div className="CollaboratorsModal__message">
          <b>
            This project needs to be published before collaborators can be added.
          </b>
        </div>
      )
  );
}

export default NoCollaborators;

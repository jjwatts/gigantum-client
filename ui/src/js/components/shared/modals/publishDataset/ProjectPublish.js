// vendor
import React, { Fragment } from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const ProjectPublish = (props) => {
  const {
    isProcessing,
    progress,
    header,
    owner,
    labbookName,
  } = props;
  const action = (header === 'Publish') ? 'Publishing' : 'Syncing';
  const currentStep = progress.project ? progress.project.step : 1;
  const firstProjectStepCSS = classNames({
    'is-active': currentStep === 1,
    'is-completed': currentStep > 1,
  });
  const secondProjectStepCSS = classNames({
    'is-active': currentStep === 2,
    'is-completed': currentStep > 2,
  });
  const thirdProjectStepCSS = classNames({
    'is-completed': currentStep === 3,
  });

  return (
    <Fragment>
      <p className="text-center">Select the visibility for the project and datasets to be published.</p>
      <p>
        <b>
        For collaborators to access a linked Dataset, the Dataset must be public or they must be added as a collaborator to the Dataset itself.
        </b>
      </p>

      <h5 className="PublishDatasetsModal__Label">Project</h5>
      <div className="PublishDatasetsModal__radio-container">
        {`${owner}/${labbookName}`}

        <div className="PublishDatasetsModal__radio-subcontainer">
          { !isProcessing
            ? (
              <Fragment>
                <div className="PublishDatasetsModal__private">
                  <label
                    className="Radio"
                    htmlFor="project_private"
                  >
                    <input
                      type="radio"
                      name="publishProject"
                      id="project_private"
                      onClick={() => { props.setPublic('project', false); }}
                    />
                    <span><b>Private</b></span>
                  </label>

                </div>

                <div className="PublishDatasetsModal__public">
                  <label
                    className="Radio"
                    htmlFor="project_public"
                  >
                    <input
                      name="publishProject"
                      type="radio"
                      id="project_public"
                      onClick={() => { props.setPublic('project', true); }}
                    />
                    <span><b>Public</b></span>
                  </label>

                </div>
              </Fragment>
            )
            : (
              <div className="container-fluid">
                <ul className="list-unstyled multi-steps project">
                  <li className={firstProjectStepCSS}>Waiting</li>
                  <li className={secondProjectStepCSS}>{action}</li>
                  <li className={thirdProjectStepCSS}>Finished</li>
                </ul>
              </div>
            )
          }

        </div>
      </div>
    </Fragment>
  );
};

ProjectPublish.propTypes = {
  isProcessing: PropTypes.isRequired,
  progress: PropTypes.isRequired,
  header: PropTypes.isRequired,
  owner: PropTypes.isRequired,
  labbookName: PropTypes.isRequired,
};

export default ProjectPublish;

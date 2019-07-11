import os
ENV_SKIP_TEST = os.environ.get('CIRCLE_BRANCH') is not None \
              and os.environ.get('SKIP_ENV_TESTS') is not None
ENV_SKIP_MSG = "Skip environment tests on circleCI when not in `test-gtmcore-environment` job"

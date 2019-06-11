from gtmcore.gitlib.git_fs import GitFilesystem
from gtmcore.logging import LMLogger
import subprocess

logger = LMLogger.get_logger()


class GitFilesystemShimmed(GitFilesystem):

    def add(self, filename):
        """Add a file to a commit

        Args:
            filename(str): Filename to add.

        Returns:
            None
        """
        logger.info("Adding file {} to Git repository in {}".format(filename, self.working_directory))
        try:
            r = subprocess.run(['git', 'add', f'{filename}'], stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                               check=True, cwd=self.working_directory)
        except subprocess.CalledProcessError as x:
            logger.error(f'{x.stdout}, {x.stderr}')
            raise

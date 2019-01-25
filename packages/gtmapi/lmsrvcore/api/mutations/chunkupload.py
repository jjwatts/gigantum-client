# Copyright (c) 2017 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import graphene
import abc

import os
import tempfile
from gtmcore.logging import LMLogger
from werkzeug.utils import secure_filename


logger = LMLogger.get_logger()


class ChunkUploadInput(graphene.InputObjectType):
    """Input Object for params needed for a chunked upload

    To use, add a field `chunk_upload_params` to your mutation input

    """
    # Total file size in kilobytes
    file_size_kb = graphene.Int(required=True)

    # Number of bytes in a single chunk (note, last chunk will be <= chunk_size
    chunk_size = graphene.Int(required=True)

    # Total number of chunks in the file
    total_chunks = graphene.Int(required=True)

    # An index value for which chunk is currently being uploaded, starting at 0
    chunk_index = graphene.Int(required=True)

    # The name of the file being uploaded
    filename = graphene.String(required=True)

    # A UUID for an entire upload job
    upload_id = graphene.String(required=True)


class ChunkUploadMutation(object):
    """Abstract class for performing chunked uploads

    To use, inherit from this class when writing your mutation and add the required ChunkUploadInput field:

        from lmsrvcore.api.mutations import ChunkUploadMutation, ChunkUploadInput

        class MyMutation(graphene.relay.ClientIDMutation, ChunkUploadMutation):
            class Input:
                chunk_upload_params = ChunkUploadInput(required=True)

            @classmethod
            def mutate_and_process_upload(cls, input, context, info):
                ...
                return MyMutation()

    """
    # TODO: REFACTOR check if this comment is still true
    # NOTE: CURRENTLY INPUT DOES NOT GET INHERITED PROPERLY IN GRAPHENE, SO YOU MUST ADD THE PARAM TO YOUR CHILD CLASS
    class Arguments:
        chunk_upload_params = ChunkUploadInput(required=True)

    # The uploaded temporary absolute file path
    upload_file_path = None

    # The desired filename
    filename = None

    @staticmethod
    def validate_args(args):
        """Method to validate the input chunking arguments"""
        if args['chunk_index'] >= args['total_chunks']:
            raise ValueError("Invalid args. chunk_index >= total_chunks")

        file_size_bytes = args['file_size_kb'] * 1000
        # Do to loss of precision when rounding to kb, add roughly 1 kb
        if args['chunk_size'] * args['total_chunks'] < file_size_bytes + 1001:
            raise ValueError("Invalid args. Not enough chunks expected")

    @staticmethod
    def py_secure_filename(filename: str) -> str:
        # Take any non-alphanumeric (and some limited special chars) and replace with _
        # Also note, max filename size is 4096 chars
        s = lambda n: n if (n.isalnum() or n in '._-+=') else '_'
        safe_fname = ''.join([s(c) for c in os.path.basename(filename)])[:255]
        if safe_fname != filename:
            logger.info(f"Renaming unsafe filename `{filename}` to `{safe_fname}`")
        return safe_fname

    @staticmethod
    def get_temp_filename(upload_id, filename):
        """Method to generate the temporary filename"""
        return os.path.join(tempfile.gettempdir(), "{}-{}".format(ChunkUploadMutation.py_secure_filename(upload_id),
                                                                  ChunkUploadMutation.py_secure_filename(filename)))

    @staticmethod
    def get_filename(filename):
        """Method to generate the desired target filename"""
        return os.path.basename(ChunkUploadMutation.py_secure_filename(filename))

    @classmethod
    def mutate_and_get_payload(cls, root, info, **kwargs):
        try:
            chunk_params = kwargs.get("chunk_upload_params")
            logger.debug(f"Processing chunk {chunk_params['chunk_index']} for {chunk_params['filename']}")

            # Make sure the file is there
            if 'uploadChunk' not in info.context.files:
                msg = 'No file "uploadChunk" associated with request'
                logger.error(msg)
                raise ValueError(msg)

            # Validate input arguments
            cls.validate_args(chunk_params)

            # Write chunk to file
            with open(cls.get_temp_filename(chunk_params['upload_id'], chunk_params['filename']), 'ab') as f:
                f.seek(chunk_params['chunk_index'] * chunk_params['chunk_size'])
                f.write(info.context.files.get('uploadChunk').stream.read())

            # If last chunk, move on to mutation
            logger.debug(f"Write for chunk {chunk_params['chunk_index']} complete")
            if chunk_params['chunk_index'] == chunk_params['total_chunks'] - 1:
                # Assume last chunk. Let mutation process
                upload_file_path = cls.get_temp_filename(chunk_params['upload_id'], chunk_params['filename'])
                filename = cls.get_filename(chunk_params['filename'])
                return cls.mutate_and_process_upload(info,
                                                     upload_file_path=upload_file_path,
                                                     upload_filename=filename,
                                                     **kwargs)
            else:
                # Assume more chunks to go. Short circuit request
                return cls.mutate_and_wait_for_chunks(info, **kwargs)

        except Exception as e:
            logger.exception(e)
            # Something bad happened, so make best effort to dump all the files in the body on the floor.
            # This is important because you must read all bytes out of a POST body when deployed with uwsgi/nginx
            if info.context.files:
                logger.error(f"Error occurred while processing a file chunk. Dumping all files in the body.")
                for fs in info.context.files.keys():
                    if info.context.files.get(fs):
                        try:
                            _ = info.context.files.get(fs).stream.read()
                            logger.error(f"Dumped file key {fs}")
                        except Exception:
                            pass
            raise

    @classmethod
    def mutate_and_process_upload(cls, info, upload_file_path, upload_filename, **kwargs):
        """Method to implement to process the upload. Must return a Mutation type"""
        raise NotImplemented

    @classmethod
    def mutate_and_wait_for_chunks(cls, info, **kwargs):
        """Method to implement to process set any non-null fields, but essentially just return.
         Must return a Mutation type"""
        raise NotImplemented

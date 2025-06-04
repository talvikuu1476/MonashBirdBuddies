FROM public.ecr.aws/lambda/python:3.9
# Install libsndfile so that soundfile (and librosa) can read/write audio
RUN yum install -y libsndfile \
    libsndfile-devel \
 && yum clean all

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt


# Set environment variable for numba cache
ENV NUMBA_CACHE_DIR=/tmp/numba_cache
# Create the directory so numba doesn't throw errors
RUN mkdir -p /tmp/numba_cache
ENV TMPDIR=/tmp
ENV TFHUB_CACHE_DIR=/tmp
ENV XDG_CACHE_HOME=/tmp


# Copy function code
COPY birds_audio_detection.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "birds_audio_detection.lambda_handler" ]
FROM public.ecr.aws/lambda/python:3.12

# Install dependencies for OpenCV
RUN dnf install -y \
    mesa-libGL \
    mesa-libGLU \
    glib2 \
&& dnf clean all

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code and model
COPY birds_video_detection.py .
COPY model.pt .

# Set handler
CMD [ "birds_video_detection.handler" ]

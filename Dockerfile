FROM python:3.13.2-slim-bookworm
WORKDIR /compunetpoc
COPY requirements.txt .
# Install any dependencies
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir -r requirements.txt
COPY . .
CMD ["/bin/sh"]
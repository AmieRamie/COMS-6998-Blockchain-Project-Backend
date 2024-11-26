# base image: https://hub.docker.com/r/nikolaik/python-nodejs
FROM nikolaik/python-nodejs:python3.12-nodejs18-slim

# Install build dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        build-essential

# install truffle and ganache
RUN npm install --global --quiet npm truffle ganache

# set working directory
WORKDIR /app

# install python dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# copy the application files
COPY main.py /app/
COPY services /app/services/

COPY truffle-config.js /app/
COPY contracts /app/contracts/
COPY migrations /app/migrations/
# COPY test /app/test/

COPY data.json /app/

# compile the smart contracts
RUN truffle compile

# EXPOSE 8545 8010
EXPOSE 8010

# start ganache and then run the application
CMD ["/bin/bash", "-c", "ganache & sleep 5 && python3 main.py"]
